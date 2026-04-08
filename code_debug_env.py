# -*- coding: utf-8 -*-
"""Gym-style core environment plus OpenEnv-compatible adapter."""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional, Tuple

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State as OpenEnvState
from pydantic import AliasChoices, BaseModel, Field

from reward import compute_reward
from tasks import TASKS


class CodeDebugObservation(BaseModel):
    buggy_code: str
    expected_output: str
    error_output: str
    tests_passed: int
    tests_total: int
    step_number: int
    done: bool = False
    reward: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeDebugAction(BaseModel):
    fixed_code: str = Field(
        description="Proposed fixed Python source code.",
        validation_alias=AliasChoices("fixed_code", "message"),
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeDebugEnv:
    """Core RL environment with Gym-style reset/step/state."""

    def __init__(self, task_name: str = "easy", seed: int = 42):
        if task_name not in TASKS:
            raise ValueError(f"Unknown task '{task_name}'. Available: {list(TASKS)}")
        self.seed = seed  # kept for reproducibility contract (deterministic eval)
        self.task_name = task_name
        self.task = TASKS[task_name]
        self.max_steps = int(self.task["max_steps"])
        self._episode_id: Optional[str] = None
        self._step_number = 0
        self._done = False
        self._last_error = ""
        self._last_reward = 0.0
        self._last_scorecard: Dict[str, float] = {"syntax": 0.0, "logic": 0.0, "optimal": 0.0}
        self._last_tests_passed = 0
        self._last_tests_total = 0

    def reset(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        if task_name is not None:
            if task_name not in TASKS:
                raise ValueError(f"Unknown task '{task_name}'. Available: {list(TASKS)}")
            self.task_name = task_name
            self.task = TASKS[task_name]
            self.max_steps = int(self.task["max_steps"])

        self._episode_id = str(uuid.uuid4())
        self._step_number = 0
        self._done = False
        self._last_reward = 0.0
        self._last_scorecard = {"syntax": 0.0, "logic": 0.0, "optimal": 0.0}

        scorecard, tests_passed, tests_total, error = self._evaluate_code(self.task["buggy_code"])
        self._last_scorecard = scorecard
        self._last_tests_passed = tests_passed
        self._last_tests_total = tests_total
        self._last_error = error
        return self.state()

    def step(self, action: str | Dict[str, Any] | CodeDebugAction) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        if self._done:
            return self.state(), 0.0, True, {"reason": "episode_already_done"}

        fixed_code = self._extract_code(action)
        self._step_number += 1

        scorecard, tests_passed, tests_total, error = self._evaluate_code(fixed_code)
        reward = compute_reward(scorecard=scorecard, step_number=self._step_number, max_steps=self.max_steps)

        done = bool(scorecard["logic"] >= 1.0) or self._step_number >= self.max_steps
        self._done = done
        self._last_reward = reward
        self._last_scorecard = scorecard
        self._last_tests_passed = tests_passed
        self._last_tests_total = tests_total
        self._last_error = error

        info = {
            "task": self.task_name,
            "scorecard": scorecard,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "episode_id": self._episode_id,
        }
        return self.state(), reward, done, info

    def state(self) -> Dict[str, Any]:
        return {
            "episode_id": self._episode_id,
            "task_name": self.task_name,
            "buggy_code": self.task["buggy_code"],
            "expected_output": self.task["expected_output"],
            "step_number": self._step_number,
            "max_steps": self.max_steps,
            "done": self._done,
            "error_output": self._last_error,
            "tests_passed": self._last_tests_passed,
            "tests_total": self._last_tests_total,
            "scorecard": self._last_scorecard,
        }

    def close(self) -> None:
        return

    @staticmethod
    def _extract_code(action: str | Dict[str, Any] | CodeDebugAction) -> str:
        if isinstance(action, str):
            return action
        if isinstance(action, CodeDebugAction):
            return action.fixed_code
        if isinstance(action, dict):
            return str(action.get("fixed_code", action.get("message", "")))
        raise TypeError(f"Unsupported action type: {type(action)}")

    def _evaluate_code(self, code: str) -> Tuple[Dict[str, float], int, int, str]:
        namespace: Dict[str, Any] = {}
        try:
            compiled = compile(code, "<candidate>", "exec")
            exec(compiled, namespace, namespace)
            syntax_score = 1.0
        except Exception as exc:
            return {"syntax": 0.0, "logic": 0.0, "optimal": 0.0}, 0, 1, f"Syntax/exec error: {exc}"

        try:
            checks = self.task["evaluator"](namespace)
            tests_total = len(checks)
            tests_passed = sum(1 for _, ok, _, _ in checks if ok)
            logic_score = tests_passed / max(1, tests_total)
            optimal_score = self._optimality_score(code, self.task_name)
            error_lines = [f"{name}: got={got} expected={exp}" for name, ok, got, exp in checks if not ok]
            error = "\n".join(error_lines) if error_lines else ""
            return {
                "syntax": syntax_score,
                "logic": logic_score,
                "optimal": optimal_score,
            }, tests_passed, tests_total, error
        except Exception as exc:
            return {"syntax": 1.0, "logic": 0.0, "optimal": 0.0}, 0, 1, f"Evaluation error: {exc}"

    @staticmethod
    def _optimality_score(code: str, task_name: str) -> float:
        compact = [ln for ln in code.splitlines() if ln.strip()]
        if task_name == "easy":
            return 1.0 if len(compact) <= 10 else 0.6
        if task_name == "medium":
            has_mod = re.search(r"%\s*2\s*==\s*0", code) is not None
            return 1.0 if has_mod else 0.5
        # hard
        has_punct = "re.sub" in code or "translate(" in code
        has_agg = ".get(" in code
        score = 0.4 + (0.3 if has_punct else 0.0) + (0.3 if has_agg else 0.0)
        return min(1.0, score)


class OpenEnvCodeDebugEnv(Environment[CodeDebugAction, CodeDebugObservation, OpenEnvState]):
    """Adapter layer for OpenEnv HTTP/WebSocket server."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, task_name: str = "easy"):
        super().__init__()
        self._core = CodeDebugEnv(task_name=task_name, seed=42)

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> CodeDebugObservation:
        task_name = kwargs.get("task_name")
        st = self._core.reset(task_name=task_name)
        return CodeDebugObservation(
            buggy_code=st["buggy_code"],
            expected_output=st["expected_output"],
            error_output=st["error_output"],
            tests_passed=st["tests_passed"],
            tests_total=st["tests_total"],
            step_number=st["step_number"],
            done=st["done"],
            reward=None,
            metadata={"task": st["task_name"], "scorecard": st["scorecard"]},
        )

    def step(
        self,
        action: CodeDebugAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> CodeDebugObservation:
        st, reward, done, info = self._core.step(action)
        return CodeDebugObservation(
            buggy_code=st["buggy_code"],
            expected_output=st["expected_output"],
            error_output=st["error_output"],
            tests_passed=st["tests_passed"],
            tests_total=st["tests_total"],
            step_number=st["step_number"],
            done=done,
            reward=reward,
            metadata=info,
        )

    @property
    def state(self) -> OpenEnvState:
        st = self._core.state()
        return OpenEnvState(episode_id=st["episode_id"], step_count=st["step_number"])

    def close(self) -> None:
        self._core.close()


