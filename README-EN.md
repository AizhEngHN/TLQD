# UAV Test Case Generator

An automated UAV test case generation tool based on behavior space search, designed to generate challenging obstacle configurations for testing PX4 UAV flight systems.

## Project Overview

This project implements an intelligent test case generator that automatically generates UAV flight test scenarios through behavior space mapping and evolutionary algorithms. The generator can:

- Automatically generate challenging obstacle configurations
- Explore search space based on behavioral features
- Identify dangerous scenarios that cause UAV collisions or near-misses
- Support multiple mission scenarios (mission1-7)

## Core Algorithm

The project employs a three-phase search strategy:

1. **Phase 1: Behavior Space Filling** - Fill all cells in the behavior space using random initialization
2. **Phase 2: Initial Evaluation** - Evaluate the individual closest to the center in each cell through simulation
3. **Phase 3: Local Search** - Perform local search and optimization in high-fitness regions

### Behavioral Features

- **Behavior 1 (B1)**: Rotation angle difference between obstacles
- **Behavior 2 (B2)**: Obstacle size ratio

## Requirements

- Python 3.8 ~ 3.11 (Aerialist requires Python ≥ 3.8 and < 3.12)
- Docker (for running PX4 simulation)
- Aerialist framework

## Installation

### Method 1: Using Virtual Environment (Recommended, Avoids Dependency Conflicts)

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Create and activate Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or Windows: venv\Scripts\activate
```

3. Install Aerialist framework first:
```bash
pip3 install git+https://github.com/skhatiri/Aerialist.git
```

4. Install project dependencies:
```bash
pip3 install -r requirements.txt
```

5. Configure environment variables (create `.env` file):
```bash
echo "AGENT=docker" > .env
echo "TESTS_FOLDER=./generated_tests/" >> .env
```

6. Ensure Docker is running and PX4 simulation environment is configured

### Method 2: Using Docker (Complete Environment Isolation)

1. Build Docker image:
```bash
docker build -t uav-test-generator .
```

2. Run container:
```bash
docker run -v $(pwd)/generated_tests:/app/generated_tests \
           -v /var/run/docker.sock:/var/run/docker.sock \
           uav-test-generator python3 cli.py generate case_studies/mission6.yaml 200
```

## Usage

### Pre-run Checklist

Ensure the following steps are completed:
1. ✅ Virtual environment is activated (if using Method 1)
2. ✅ Docker service is running
3. ✅ `.env` file is created and configured correctly
4. ✅ All dependencies are installed correctly

### Basic Usage

Run the test generator:

```bash
python3 cli.py generate case_studies/mission6.yaml 200
```

Parameters:
- `case_studies/mission6.yaml`: Mission configuration file path
- `200`: Test budget (number of simulations allowed)

### Available Mission Scenarios

The project provides multiple predefined mission scenarios:

- `mission1.yaml` - `mission7.yaml`: Different flight mission configurations
- Each mission includes takeoff points, waypoints, flight parameters, etc.

## Troubleshooting

### Dependency Conflicts

If you encounter dependency conflicts, follow these steps:

1. **Clean existing environment**:
```bash
deactivate  # If in virtual environment
rm -rf venv  # Remove old virtual environment
```

2. **Recreate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install in correct order**:
```bash
# Install Aerialist first
pip3 install git+https://github.com/skhatiri/Aerialist.git

# Then install project dependencies
pip3 install -r requirements.txt
```

**Note**: This project's `requirements.txt` only contains necessary dependencies (python-decouple, pyulog, numpy, shapely) and will not conflict with Aerialist.

### Docker Issues

If Docker cannot run tests:

1. Ensure Docker daemon is running:
```bash
docker ps
```

2. Check Docker permissions (Linux):
```bash
sudo usermod -aG docker $USER
# Then log out and log back in
```

3. Verify `.env` file configuration:
```bash
cat .env
# Should display:
# AGENT=docker
# TESTS_FOLDER=./generated_tests/
```

### Verify Installation

Run the following command to verify successful installation:

```bash
python3 -c "import aerialist; import pyulog; from decouple import config; print('All dependencies installed successfully!')"
```

## Project Structure

```
.
├── cli.py                  # Command-line interface
├── generator.py            # Main test generator (AIGenerator class)
├── testcase.py            # Test case execution class
├── Our_operator.py        # Genetic algorithm operators
├── read_ulg.py            # ULG log file reader
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── case_studies/         # Mission scenario configuration files
│   ├── mission1.yaml
│   ├── mission2.yaml
│   └── ...
└── generated_tests/      # Generated test case output directory
```

## Core Classes

### AIGenerator

Main test generator class implementing behavior space search algorithm.

**Main Methods:**
- `__init__(case_study_file)`: Initialize and load mission configuration
- `generate(Max_budget)`: Generate test cases, return failing or challenging tests

### TestCase

Test case execution class encapsulating single test execution and evaluation.

**Main Methods:**
- `execute()`: Execute simulation test
- `get_distances()`: Get minimum distances from UAV to each obstacle
- `plot()`: Generate visualization chart
- `save_yaml(path)`: Save test configuration

## Output Results

Generated test cases are saved in the `generated_tests/` directory. Each run creates a timestamped subdirectory containing:

- `test_*.yaml`: Test configuration files
- `test_*.ulg`: PX4 flight logs
- `test_*.png`: Flight trajectory visualization

Individual evaluation details are also saved in `results/ind/` directory (JSON format).

## Algorithm Parameters

Main parameters adjustable in `generator.py`:

- `pop_size`: Population size (default 100)
- `num_parents`: Number of parents selected (default 10)
- `B1_step`: Behavior 1 step size (default 15 degrees)
- `B2_step`: Behavior 2 step size (default 0.1)
- `num_B1`: Number of Behavior 1 cells (default 6)
- `num_B2`: Number of Behavior 2 cells (default 8)

## Logs

Runtime logs are saved in the `logs/` directory:
- `debug.txt`: Detailed debug logs
- `info.txt`: General information logs

## Fitness Evaluation

Test case fitness is based on minimum distance from UAV to obstacles:
- Distance ≤ 1.5 meters: Considered failing test case (high value)
- Smaller distance = more challenging test case

## Docker Deployment

Run using Docker:

```bash
docker build -t uav-test-generator .
docker run -v $(pwd)/generated_tests:/app/generated_tests uav-test-generator
```

## Related Projects

This project is developed based on the [Aerialist](https://github.com/skhatiri/Aerialist) framework for UAV test case definition and execution.

## License

Please refer to the project license file.

## Contact

For questions or suggestions, please contact via issues or discussion board.
