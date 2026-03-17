import numpy as np
import random
random.seed(726)
def initialize_population(pop_size,case):
    """
    初始化种群，每个个体为10维向量，表示两个障碍物的属性。
    每个障碍物属性为 [x, y, l, w, r]，z=0, h=20 固定不计入向量。

    :param pop_size: 个体数量（种群规模）
    :return: numpy 数组，形状为 (pop_size, 10)
    """
    # 范围
    x_range = (-40, 30)
    y_range = (10, 40)
    l_range = (5, 20)  # min = 2
    w_range = (5, 20)  # min  =2
    r_range = (0, 90)
    if case == 'case2':
        x_range = (-15, 5)
    elif case == 'case3':
        x_range = (-20, 5)
    elif case == 'case4':
        x_range = (-25, 30)
    elif case == 'case5':
        x_range = (-5, 30)
    elif case == 'case6':
        x_range = (-40, 30)
    elif case == 'case7':
        x_range = (-40, 5)

    # 第一个障碍物
    x1 = np.random.uniform(*x_range, size=(pop_size, 1))
    y1 = np.random.uniform(*y_range, size=(pop_size, 1))
    l1 = np.random.uniform(*l_range, size=(pop_size, 1))
    w1 = np.random.uniform(*w_range, size=(pop_size, 1))
    r1 = np.random.uniform(*r_range, size=(pop_size, 1))

    # 第二个障碍物
    x2 = np.random.uniform(*x_range, size=(pop_size, 1))
    y2 = np.random.uniform(*y_range, size=(pop_size, 1))
    l2 = np.random.uniform(*l_range, size=(pop_size, 1))
    w2 = np.random.uniform(*w_range, size=(pop_size, 1))
    r2 = np.random.uniform(*r_range, size=(pop_size, 1))

    # 拼接为 (pop_size, 10)
    population = np.hstack([x1, y1, l1, w1, r1, x2, y2, l2, w2, r2])
    return population

import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import rotate, translate

# 创建旋转矩形
def create_rotated_rectangle(x, y, l, w, r_deg):
    dx = l / 2
    dy = w / 2
    corners = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
    rect = Polygon(corners)
    rect = rotate(rect, r_deg, origin=(0, 0), use_radians=False)
    rect = translate(rect, xoff=x, yoff=y)
    return rect

# 修补函数
def repair_individual(ind,
                    d_target=3.0, # 约束
                    max_attempts=50, #
                    step_size=1.0,
                    scale_step=0.9,
                    min_lw=2.0):
    ind = ind.copy()
    x1, y1, l1, w1, r1 = ind[0:5]
    x2, y2, l2, w2, r2 = ind[5:10]
    for _ in range(max_attempts):
        rect1 = create_rotated_rectangle(x1, y1, l1, w1, r1)
        rect2 = create_rotated_rectangle(x2, y2, l2, w2, r2)

        overlap = rect1.intersects(rect2)  # 是否又重叠部分
        min_dist = rect1.distance(rect2)   # 计算边界到边界之间的最小欧式距离

        # 如果已经满足不重叠且距离>=3，直接返回
        if (not overlap) and (min_dist >= d_target):
            ind[5:10] = [x2, y2, l2, w2, r2]
            return ind  # 第一种情况，满足所有约束

        # 第二种情况，重叠
        # 计算单位方向向量 dir_unit（从障碍物1指向障碍物2）
        dir_vec = np.array([x2 - x1, y2 - y1])
        norm = np.linalg.norm(dir_vec)
        if norm == 0:
            dir_vec = np.random.uniform(-1, 1, size=2)
            norm = np.linalg.norm(dir_vec)
        dir_unit = dir_vec / norm

        if overlap:
            # 若有重叠，直接推远一步
            x2 += dir_unit[0] * step_size
            y2 += dir_unit[1] * step_size
        elif min_dist < d_target:
            # 若不重叠但距离不足，精确推远 delta = d_target - min_dist
            delta = d_target - min_dist
            x2 += dir_unit[0] * delta
            y2 += dir_unit[1] * delta

        # 检查是否越界
        if not (-40 <= x2 <= 30 and 10 <= y2 <= 40):
            # 缩小尺寸，维持中心点
            l2 *= scale_step
            w2 *= scale_step
            l2 = max(l2, min_lw)
            w2 = max(w2, min_lw)

    # 最后尝试后强行返回（仍可能不完全满足）
    ind[5:10] = [x2, y2, l2, w2, r2]
    return ind

def Behavior_1(ind): # 行为1 ， 两个障碍物之间的夹角
    r1 = ind[4]
    r2 = ind[9]
    diff = abs(r1 - r2) % 180
    B_1 = min(diff, 180 - diff)
    return B_1


def Behavior_2(ind,case):  # 行为2 横截长度之和 占 区域面积之比
    if case == 'case2':
        region = 20
    elif case == 'case3':
        region = 25
    elif case == 'case4':
        region = 55
    elif case == 'case5':
        region = 35
    elif case == 'case6':
        region = 70
    elif case == 'case7':
        region = 45
    L1 = abs(ind[2]* np.cos(ind[4])) + abs(ind[3]* np.sin(ind[4]))
    L2 = abs(ind[7]* np.cos(ind[9])) + abs(ind[8]* np.sin(ind[9]))
    B_2 = (L1 + L2) /region
    return B_2

def find_empty_cells(grid):
    empty_cells = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if len(grid[i][j]) == 0:
                empty_cells.append((i, j))
    return empty_cells


def sample_parents_from_BS(B_S, num_parents):
    """
    从 B_S 中采样一批 parent 个体（有放回的行为格子选择 + 个体随机抽取）
    :param B_S: 二维行为网格结构
    :param num_parents: 需要的 parent 数量
    :return: parents 列表（仅个体编码）
    """
    all_cells = []
    avg_fitnesses = []

    for i in range(len(B_S)):
        for j in range(len(B_S[0])):
            cell = B_S[i][j]
            if cell:
                avg_fit = np.mean([entry['fitness'] for entry in cell])
                all_cells.append((i, j))
                avg_fitnesses.append(avg_fit)

    if not all_cells:
        return []

    # 概率分布：越小越好 → 取倒数
    epsilon = 1e-1
    inv_fitness = 1.0 / (np.array(avg_fitnesses) + epsilon)
    probs = inv_fitness / np.sum(inv_fitness)

    # 有放回地选择 num_parents 个格子索引
    selected_indices = np.random.choice(len(all_cells), size=num_parents, replace=True, p=probs)

    # 从每个格子中随机抽一个个体作为 parent
    parents = []
    for idx in selected_indices:
        i, j = all_cells[idx]
        cell = B_S[i][j]
        entry = random.choice(cell)
        parents.append(entry['individual'])

    return parents

def perturb_positions(individual, case,sigma=0.05):
    """
    对两个障碍物的位置 (x, y) 进行小范围扰动，保持行为（r）不变
    :param individual: np.array 长度为10
    :param sigma: 扰动标准差
    :return: 新个体（np.array）
    """
    ind = individual.copy()

    if case == 'case2':
        region = 20
    elif case == 'case3':
        region = 25
    elif case == 'case4':
        region = 55
    elif case == 'case5':
        region = 35
    elif case == 'case6':
        region = 70
    elif case == 'case7':
        region = 45
    sigma = region *0.05 # x值扰动
    sigma1 = 30 * 0.05 # y值扰动
    # 第一个障碍物位置扰动
    ind[0] += np.random.normal(0, sigma)  # x1
    ind[1] += np.random.normal(0, sigma1)  # y1

    # 第二个障碍物位置扰动
    ind[5] += np.random.normal(0, sigma)  # x2
    ind[6] += np.random.normal(0, sigma1)  # y2

    # 位置边界裁剪（保持在合法范围内）
    ind[0] = np.clip(ind[0], -40, 30)
    ind[1] = np.clip(ind[1], 10, 40)
    ind[5] = np.clip(ind[5], -40, 30)
    ind[6] = np.clip(ind[6], 10, 40)

    return ind


def oper2_1(individual,sigma=0.05):  # 同时对两个个体的r进行扰动
    """
    对两个障碍物的位置 (x, y) 进行小范围扰动，保持行为（r）不变
    :param individual: np.array 长度为10
    :param sigma: 扰动标准差
    :return: 新个体（np.array）
    """
    ind = individual.copy()

    sigma = sigma * 20 # x值扰动
    # 第一个障碍物位置扰动
    ind[4] += np.random.normal(0, sigma)  # x1
    ind[9] += np.random.normal(0, sigma)  # y1

    # 位置边界裁剪（保持在合法范围内）
    ind[4] = np.clip(ind[4], 0, 90)
    ind[9] = np.clip(ind[9], 0, 90)

    return ind

def oper2_2(individual, delta_range=(-0.5, 1.0)):
    """
    在位置扰动基础上，对两个障碍物的 l 和 w 进行“偏增大”的扰动
    :param individual: 个体编码
    :param delta_range: 扰动范围（默认偏向增大）
    :return: 新个体
    """
    ind = individual.copy()

    for obs in [0, 1]:
        base = obs * 5
        l_idx = base + 2
        w_idx = base + 3

        #loc = (0.8 × upper_bound - current_value) / (upper_bound - lower_bound)
        delta_l = (0.8 * 20 - ind[l_idx]) / (20 - 2)
        delta_w = (0.8 * 20 - ind[w_idx]) / (20 - 2)
        ind[l_idx] += delta_l
        ind[w_idx] += delta_w

        # 裁剪到合法范围
        ind[l_idx] = np.clip(ind[l_idx], 2.0, 20.0)
        ind[w_idx] = np.clip(ind[w_idx], 2.0, 20.0)

    return ind