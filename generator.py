import os
from typing import List
from aerialist.px4.drone_test import DroneTest
from aerialist.px4.obstacle import Obstacle
from testcase import TestCase
from generator_our import Obstacle_our # 自己定义的障碍生成器
from read_ulg import read_ulg # 从 .ulg 日志中提取飞行轨迹（trajectory）
import shutil
import random
import os
import time
import Our_operator
from datetime import datetime
import json

random.seed(726)
def check_collision(obstacles):
    # 该函数用于检测给定的 obstacles（list of dict）中是否有重叠：
    text = ""
    for i in range(len(obstacles)):
        obstacle1 = obstacles[i]
        for j in range(i + 1, len(obstacles)):
            obstacle2 = obstacles[j]

            if (
                    obstacle1['x'] + obstacle1['l'] >= obstacle2['x'] and
                    obstacle1['x'] <= obstacle2['x'] + obstacle2['l'] and
                    obstacle1['y'] + obstacle1['w'] >= obstacle2['y'] and
                    obstacle1['y'] <= obstacle2['y'] + obstacle2['w'] and
                    obstacle1['z'] + obstacle1['h'] >= obstacle2['z'] and
                    obstacle1['z'] <= obstacle2['z'] + obstacle2['h']
            ):
                text += f"obstacle {i + 1} is colliding with obstacle {j + 1}."

    if text == "":
        return False
    else:
        return text


def check_within_area(obstacles):
    # 障碍是否在合法区域内
    text = ""
    for i, obstacle in enumerate(obstacles):
        x_min = -40
        x_max = 30
        y_min = 10
        y_max = 40

        if (
                x_min < obstacle['x'] < x_max and
                x_min < obstacle['x'] + obstacle['l'] < x_max and
                y_min < obstacle['y'] < y_max and
                y_min < obstacle['y'] + obstacle['w'] < y_max
        ):
            continue
        else:
            text += f"Obstacle {i + 1} is not entirely within the (-40 < x < 30, 10 < y < 40) area."

    if text == "":
        return False
    else:
        return text


class AIGenerator(object):
    def __init__(self, case_study_file: str) -> None:
        # 读取任务配置文件 .yaml
        # 创建 DroneTest 对象，包含参数、起飞点、仿真设置等
        self.case_study = DroneTest.from_yaml(case_study_file)

    def generate(self, Max_budget: int) -> List[TestCase]:
        # budget 是真实评估的次数。
        test_cases = [] # 成功的测试用例
        run_time = 0 # 当前仿真运行时间

        # random.seed(2025)
        # 超参数设置
        pop_size = 100  # 种群大小
        # Max_budget = 200  # 总预算
        budget = 0  #
        Case = ['case2', 'case3', 'case4', 'case5', 'case6', 'case7']
        case = Case[3] # mission1 =  case2
        B1_step = 15  # 15度为一个步长
        num_B1 = 6
        B2_step = 0.1  # 0.1度为一个步长
        num_B2 = 8
        Behavior_space = [[[] for _ in range(num_B2)] for _ in range(num_B1)]
        num_parents = 10  # 第二阶段父代数量

        if case == 'case2':
            region = 0.8
        elif case == 'case3':
            region = 0.8
        elif case == 'case4':
            region = 0
        elif case == 'case5':
            region = 0.4
        elif case == 'case6':
            region = 0
        elif case == 'case7':
            region = 0.1

        # 第一阶段 填满行为空间
        empty = Our_operator.find_empty_cells(Behavior_space)
        while (len(empty) != 0):
            # 个体初始化
            population = Our_operator.initialize_population(pop_size, case)
            for i in range(pop_size):  # 对个体进行合法化
                population[i] = Our_operator.repair_individual(population[i])

            for i in range(pop_size):  # 映射行为空间
                # todo 映射到行为空间的过程可以先不评估，
                B1 = Our_operator.Behavior_1(population[i])
                B2 = Our_operator.Behavior_2(population[i], case)
                index1 = int(B1 / 15)  # 第一个行为中在第几个格子
                index2 = int((B2 - region) / 0.1)  # 第二个行为在第几个格子
                if index2 < 0:
                    index2 = 0
                if index2 >= num_B2:
                    index2 = num_B2 - 1
                # A = (index2+1)*0.1+0.8
                Behavior_distance = (B1 - (index1 + 1) * 15) ** 2 + (B2 - (index2 + 1) * 0.1 + 0.8) ** 2

                Behavior_space[index1][index2].append({
                    'BD': Behavior_distance,
                    # 'B1' : B1,
                    # 'B2' : B2,
                    'individual': population[i],
                    # 'fitness': 999,
                })
            empty = Our_operator.find_empty_cells(Behavior_space)
        # print("22")
        # 第二阶段 每个格子评估一个，
        B_S = [[[] for _ in range(num_B2)] for _ in range(num_B1)]

        for i in range(num_B1):
            for j in range(num_B2):
                Dis = 99999
                for k in range(len(Behavior_space[i][j])):
                    if Behavior_space[i][j][k]['BD'] < Dis:
                        Dis = Behavior_space[i][j][k]['BD']
                        K = k

                Behavior_space[i][j][K]['individual'] = Our_operator.repair_individual(Behavior_space[i][j][K]['individual'])
                # todo 评估
                obstacle_list = []

                for info in range(2):
                    size = Obstacle.Size(l=Behavior_space[i][j][K]['individual'][info*5+2],
                                         w=Behavior_space[i][j][K]['individual'][info*5+3],
                                         h=25)
                    pos = Obstacle.Position(x=Behavior_space[i][j][K]['individual'][info*5],
                                            y=Behavior_space[i][j][K]['individual'][info*5+1],
                                            z=0,
                                            r=Behavior_space[i][j][K]['individual'][info*5+4])
                    obstacle_list.append(Obstacle(size, pos))

                test = TestCase(self.case_study, obstacle_list)
                start_time = time.time()
                trajectory = test.execute()
                if trajectory is None:
                    #logger.warning("⚠️ First test execution failed. Retrying once...")
                    trajectory = test.execute()

                # 如果仍然失败，就彻底放弃
                if trajectory is None:
                    #logger.error("❌ Test execution failed twice. Skipping this individual.")
                    B_S[i][j].append({
                        'individual': Behavior_space[i][j][K]['individual'],
                        'fitness': 1.5,
                    })
                    continue  # 或 return 或其他操作

                end_time = time.time()
                run_time = end_time - start_time
                distances = test.get_distances()
                fit = min(distances)

                print(f"minimum_distance:{min(distances)}")
                print(f"Time_cost:{run_time}")
                test.plot()

                if min(distances) <= 1.5:
                    test_cases.append(test)

                budget = budget + 1
                print("One: {}Th test at {}".format(budget,datetime.now().strftime("%y-%m-%d-%H-%M")))
                if budget == Max_budget:
                    return test_cases

                B_S[i][j].append({
                    'individual': Behavior_space[i][j][K]['individual'],
                    'fitness': fit,
                })

                # 保存位置
                timestamp = datetime.now().strftime("%y-%m-%d-%H-%M")
                save_path = f"results/ind/{timestamp}-ind"

                # 保存整个个体对象 + 元信息
                with open(save_path, "w") as f:
                    json.dump({
                        "individual": Behavior_space[i][j][K]['individual'].tolist(),
                        "min_distance": fit,
                        "time_cost": run_time
                    }, f)

        # 第三阶段，对行为空间采样，然后繁衍，对适应度高的地方进行局部搜索。
        while (budget <= Max_budget):
            # 选出num_select适应度最高的、基于概率选，被选出来的格子可以重估
            parents = Our_operator.sample_parents_from_BS(B_S, num_parents=num_parents)
            # 第三阶段，对适应度高的地方进行局部搜索。

            # 算子1，对个体中的一个障碍物的 x和y进行 扰动，保持行为不变
            for i in range(len(parents)):
                parents[i] = Our_operator.perturb_positions(parents[i], case)
            # 算子2-1，在算子1的基础上，对单个个体，两个障碍物的r同时增加一个扰动值，这不会改变行为1，可能会改变行为2但是不多（局部搜索）
            parents1 = parents.copy()
            for i in range(len(parents)):
                parents1[i] = Our_operator.oper2_1(parents[i])
            # 算子2-2，在2-1的基础上对l,w进行扰动(尽量增大），即算子二不改变行为1，只改变行为2
            parents2 = parents.copy()
            for i in range(len(parents)):
                parents2[i] = Our_operator.oper2_2(parents1[i])
            # 算子3-1，在算子1的基础上，针对一个障碍物的r进行扰动，这会改变行为1，但是对行为2的影响较小。
            parents3 = parents.copy()
            for i in range(len(parents)):
               parents3[i] = Our_operator.oper2_2(parents[i])

            combined_parents = parents2 + parents3
            # combined_parents = parents2

            # 2. 打乱顺序（in-place）
            random.shuffle(combined_parents)
            combined_parents[i] = Our_operator.repair_individual(combined_parents[i])
            # 更新 行为空间B_S 并评估
            for i in range(len(combined_parents)):
                # todo 评估
                obstacle_list = []
                for info in range(2):
                    size = Obstacle.Size(l=combined_parents[i][info * 5 + 2],
                                         w=combined_parents[i][info * 5 + 3],
                                         h=25)
                    pos = Obstacle.Position(x=combined_parents[i][info * 5],
                                            y=combined_parents[i][info * 5 + 1],
                                            z=0,
                                            r=combined_parents[i][info * 5 + 4])
                    obstacle_list.append(Obstacle(size, pos))

                test = TestCase(self.case_study, obstacle_list)
                start_time = time.time()
                trajectory = test.execute()
                if trajectory is None:
                    #logger.warning("⚠️ First test execution failed. Retrying once...")
                    trajectory = test.execute()

                # 如果仍然失败，就彻底放弃
                if trajectory is None:
                    #logger.error("❌ Test execution failed twice. Skipping this individual.")

                    continue  # 或 return 或其他操作
                end_time = time.time()
                run_time = end_time - start_time
                distances = test.get_distances()
                fit =  min(distances)
                print(f"minimum_distance:{min(distances)}")
                print(f"Time_cost:{run_time}")
                test.plot()

                # 保存位置
                timestamp = datetime.now().strftime("%y-%m-%d-%H-%M")
                save_path = f"results/ind/{timestamp}-ind"

                # 保存整个个体对象 + 元信息
                with open(save_path, "w") as f:
                    json.dump({
                        "individual": combined_parents[i].tolist(),
                        "min_distance": fit,
                        "time_cost": run_time
                    }, f)

                if min(distances) <= 1.5:
                    test_cases.append(test)

                budget = budget + 1
                print("Two {}TH test at {}".format(budget,datetime.now().strftime("%y-%m-%d-%H-%M")))
                B1 = Our_operator.Behavior_1(combined_parents[i])
                B2 = Our_operator.Behavior_2(combined_parents[i], case)
                index1 = int(B1 / 15)  # 第一个行为中在第几个格子
                index2 = int((B2 - region) / 0.1)  # 第二个行为在第几个格子
                if index2 < 0:
                    index2 = 0
                if index2 >= num_B2:
                    index2 = num_B2 - 1

                B_S[index1][index2].append({
                    'individual': combined_parents[i],
                    'fitness': fit,
                })

                if budget == Max_budget:
                    return test_cases

        ### You should only return the test cases
        ### that are needed for evaluation (failing or challenging ones)
        return test_cases



if __name__ == "__main__":
    generator = AIGenerator("case_studies/mission1.yaml")
    generator.generate(3)
