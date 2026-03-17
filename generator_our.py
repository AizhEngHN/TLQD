# import openai
import ast
import os
class Obstacle_our:
    def __init__(self,A = 1):
        self.A = A


    def get_response(self, user_input):
        # 示例：完全自定义生成逻辑，不调用 GPT
        # user_input 可以作为输入条件或种子参数

        # 示例：生成一个固定结构（你可以替换为你自己的生成器输出）
        return [
            {
                'l': 10,
                'w': 5,
                'h': 20,
                'x': 5,
                'y': 25,
                'z': 0,
                'r': 60
            },
            {
                'l': 8,
                'w': 4,
                'h': 18,
                'x': -10,
                'y': 15,
                'z': 0,
                'r': 30
            }
        ]




