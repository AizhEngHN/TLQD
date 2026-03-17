# 无人机测试用例生成器

基于行为空间搜索的无人机测试用例自动生成工具，用于生成具有挑战性的障碍物配置来测试 PX4 无人机飞行系统。

## 项目简介

本项目实现了一个智能测试用例生成器，通过行为空间映射和进化算法自动生成无人机飞行测试场景。生成器能够：

- 自动生成具有挑战性的障碍物配置
- 基于行为特征进行搜索空间探索
- 识别导致无人机碰撞或接近障碍物的危险场景
- 支持多种任务场景（mission1-7）

## 核心算法

项目采用三阶段搜索策略：

1. **阶段一：行为空间填充** - 使用随机初始化填充行为空间的所有格子
2. **阶段二：初始评估** - 对每个格子中最接近中心的个体进行仿真评估
3. **阶段三：局部搜索** - 对高适应度区域进行局部搜索和优化

### 行为特征

- **行为1 (B1)**: 障碍物旋转角度差异
- **行为2 (B2)**: 障碍物尺寸比例

## 环境要求

- Python 3.8+
- Docker（用于运行 PX4 仿真）
- Aerialist 框架

## 安装步骤

### 方法一：使用虚拟环境（推荐，避免依赖冲突）

1. 克隆本仓库：
```bash
git clone <repository-url>
cd <project-directory>
```

2. 创建并激活 Python 虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 Windows: venv\Scripts\activate
```

3. 先安装 Aerialist 框架：
```bash
pip3 install git+https://github.com/skhatiri/Aerialist.git
```

4. 再安装本项目的依赖：
```bash
pip3 install -r requirements.txt
```

5. 配置环境变量（创建 `.env` 文件）：
```bash
echo "AGENT=docker" > .env
echo "TESTS_FOLDER=./generated_tests/" >> .env
```

6. 确保 Docker 正在运行并配置好 PX4 仿真环境

### 方法二：使用 Docker（完全隔离环境）

1. 构建 Docker 镜像：
```bash
docker build -t uav-test-generator .
```

2. 运行容器：
```bash
docker run -v $(pwd)/generated_tests:/app/generated_tests \
           -v /var/run/docker.sock:/var/run/docker.sock \
           uav-test-generator python3 cli.py generate case_studies/mission6.yaml 200
```

## 使用方法

### 运行前检查

确保已完成以下步骤：
1. ✅ 虚拟环境已激活（如果使用方法一）
2. ✅ Docker 服务正在运行
3. ✅ `.env` 文件已创建并配置正确
4. ✅ 所有依赖已正确安装

### 基本用法

运行测试生成器：

```bash
python3 cli.py generate case_studies/mission6.yaml 200
```

参数说明：
- `case_studies/mission6.yaml`: 任务配置文件路径
- `200`: 测试预算（允许的仿真次数）

### 可用的任务场景

项目提供了多个预定义的任务场景：

- `mission1.yaml` - `mission7.yaml`: 不同的飞行任务配置
- 每个任务包含起飞点、航点、飞行参数等配置

## 故障排除

### 依赖冲突问题

如果遇到依赖冲突，请按以下顺序操作：

1. **清理现有环境**：
```bash
deactivate  # 如果在虚拟环境中
rm -rf venv  # 删除旧的虚拟环境
```

2. **重新创建虚拟环境**：
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **按正确顺序安装**：
```bash
# 先安装 Aerialist
pip3 install git+https://github.com/skhatiri/Aerialist.git

# 再安装本项目依赖
pip3 install -r requirements.txt
```

**注意**：本项目的 `requirements.txt` 只包含必需依赖（python-decouple、pyulog、numpy、shapely），不会与 Aerialist 冲突。

### Docker 相关问题

如果 Docker 无法运行测试：

1. 确保 Docker daemon 正在运行：
```bash
docker ps
```

2. 检查 Docker 权限（Linux）：
```bash
sudo usermod -aG docker $USER
# 然后重新登录
```

3. 验证 `.env` 文件配置：
```bash
cat .env
# 应该显示：
# AGENT=docker
# TESTS_FOLDER=./generated_tests/
```

### 缺少模块错误

如果提示缺少 `Our_operator` 或 `generator_our` 模块：
- 确保这些文件存在于项目根目录
- 检查文件名是否正确（区分大小写）

### 验证安装

运行以下命令验证安装是否成功：

```bash
python3 -c "import aerialist; import pyulog; from decouple import config; print('All dependencies installed successfully!')"
```


## 项目结构

```
.
├── cli.py                  # 命令行接口
├── generator.py            # 主测试生成器（AIGenerator类）
├── testcase.py            # 测试用例执行类
├── Our_operator.py        # 遗传算法操作符
├── read_ulg.py            # ULG日志文件读取工具
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker配置
├── case_studies/         # 任务场景配置文件
│   ├── mission1.yaml
│   ├── mission2.yaml
│   └── ...
└── generated_tests/      # 生成的测试用例输出目录
```

## 核心类说明

### AIGenerator

主测试生成器类，实现行为空间搜索算法。

**主要方法：**
- `__init__(case_study_file)`: 初始化，加载任务配置
- `generate(Max_budget)`: 生成测试用例，返回失败或具有挑战性的测试

### TestCase

测试用例执行类，封装了单个测试的执行和评估。

**主要方法：**
- `execute()`: 执行仿真测试
- `get_distances()`: 获取无人机到各障碍物的最小距离
- `plot()`: 生成可视化图表
- `save_yaml(path)`: 保存测试配置

## 输出结果

生成的测试用例保存在 `generated_tests/` 目录下，每次运行创建一个时间戳命名的子目录，包含：

- `test_*.yaml`: 测试配置文件
- `test_*.ulg`: PX4飞行日志
- `test_*.png`: 飞行轨迹可视化图

同时在 `results/ind/` 目录保存每个评估个体的详细信息（JSON格式）。

## 算法参数

可在 `generator.py` 中调整的主要参数：

- `pop_size`: 种群大小（默认100）
- `num_parents`: 父代选择数量（默认10）
- `B1_step`: 行为1的步长（默认15度）
- `B2_step`: 行为2的步长（默认0.1）
- `num_B1`: 行为1的格子数量（默认6）
- `num_B2`: 行为2的格子数量（默认8）

## 日志

运行日志保存在 `logs/` 目录：
- `debug.txt`: 详细调试日志
- `info.txt`: 一般信息日志

## 适应度评估

测试用例的适应度基于无人机到障碍物的最小距离：
- 距离 ≤ 1.5米：视为失败测试用例（高价值）
- 距离越小，测试用例越具有挑战性

## Docker 部署

使用 Docker 运行：

```bash
docker build -t uav-test-generator .
docker run -v $(pwd)/generated_tests:/app/generated_tests uav-test-generator
```

## 相关项目

本项目基于 [Aerialist](https://github.com/skhatiri/Aerialist) 框架开发，用于无人机测试用例的定义和执行。

## 许可证

请参考项目许可证文件。

## 联系方式

如有问题或建议，请通过 issue 或讨论区联系。
