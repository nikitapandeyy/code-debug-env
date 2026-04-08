import gymnasium as gym
from gymnasium import spaces
import numpy as np

from evaluator.test_runner import run_tests
from evaluator.reward_calculator import compute_reward
from env.state_manager import StateManager
from env.action_handler import apply_action


class CodeDebugEnv(gym.Env):
    def __init__(self, task):
        super().__init__()

        self.task = task
        self.state_manager = StateManager(task)
        self.max_steps = 10
        self.current_step = 0

        self.action_space = spaces.MultiDiscrete([3, 20])

        self.observation_space = spaces.Box(
            low=0, high=255, shape=(100,), dtype=np.int32
        )

    def encode_state(self, code):
        encoded = [ord(c) for c in code][:100]
        return np.array(encoded + [0]*(100-len(encoded)), dtype=np.int32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.current_step = 0
        state = self.state_manager.initialize_state()

        return self.encode_state(state["code"]), {}

    def step(self, action):
        self.current_step += 1

        action_type, line = action

        action_map = {0: "replace", 1: "delete", 2: "insert"}

        possible_fixes = [
            "return a + b",
            "return b + a",
            "return a*b",
            "return a/b if b!=0 else 0"
        ]

        structured_action = {
            "type": action_map[action_type],
            "line": int(line % max(1, len(self.state_manager.code.split("\n")))),
            "content": possible_fixes[action_type % len(possible_fixes)]
        }

        new_code = apply_action(self.state_manager.code, structured_action)

        result = run_tests(new_code, self.task["tests"])
        reward = compute_reward(result)

        state = self.state_manager.update_state(new_code, result)

        terminated = result["all_passed"]
        truncated = self.current_step >= self.max_steps

        obs = self.encode_state(state["code"])

        return obs, reward, terminated, truncated, result
