import copy
import logging
from typing import List
from aerialist.px4.aerialist_test import AerialistTest, AgentConfig
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.docker_agent import DockerAgent
from aerialist.px4.k8s_agent import K8sAgent
from aerialist.px4.local_agent import LocalAgent
from aerialist.px4.trajectory import Trajectory
from aerialist.px4.plot import Plot
from decouple import config

AGENT = config("AGENT", default=AgentConfig.DOCKER)
logger = logging.getLogger(__name__)


class TestCase(object):
    def __init__(self, casestudy: AerialistTest, obstacles: List[Obstacle]):
        self.test = copy.deepcopy(casestudy)
        self.test.simulation.obstacles = obstacles

    def execute(self) -> Trajectory:
        if AGENT == AgentConfig.LOCAL:
            agent = LocalAgent(self.test)
        if AGENT == AgentConfig.DOCKER:
            agent = DockerAgent(self.test)
        if AGENT == AgentConfig.K8S:
            agent = K8sAgent(self.test)
        logger.info("running the test...")
        self.test_results = agent.run()
        
        # 调试信息
        print(f"🧪 test_results type: {type(self.test_results)}")
        print(f"🧪 test_results length: {len(self.test_results) if self.test_results else 0}")
        if self.test_results:
            print(f"🧪 test_results[0] type: {type(self.test_results[0])}")
        
        if not self.test_results:
            logger.warning("❌ agent.run() returned no results after retry. Skipping this test.")
            self.trajectory = None
            return None
        logger.info("test finished...")
        self.trajectory = self.test_results[0].record
        self.log_file = self.test_results[0].log_file
        return self.trajectory

    def get_distances(self) -> List[float]:
        return [
            self.trajectory.min_distance_to_obstacles([obst])
            for obst in self.test.simulation.obstacles
        ]

    def plot(self):
        self.plot_file = Plot.plot_test(self.test, self.test_results)

    def save_yaml(self, path):
        self.test.to_yaml(path)
