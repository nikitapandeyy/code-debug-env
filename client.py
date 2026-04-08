"""
CodeDebugEnv client for OpenEnv HTTP/WebSocket servers.

This file exists primarily to satisfy OpenEnv `push` structure validation
and to provide a convenient Python client for local / deployed environments.
"""

from __future__ import annotations

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from models import CodeDebugAction, CodeDebugObservation


class CodeDebugEnvClient(EnvClient[CodeDebugAction, CodeDebugObservation, State]):
    """Client for CodeDebugEnv running at an OpenEnv server base URL."""

    def _step_payload(self, action: CodeDebugAction) -> Dict:
        return {"fixed_code": action.fixed_code}

    def _parse_result(self, payload: Dict) -> StepResult[CodeDebugObservation]:
        obs_data = payload.get("observation", {}) or {}
        observation = CodeDebugObservation(
            buggy_code=obs_data.get("buggy_code", ""),
            expected_output=obs_data.get("expected_output", ""),
            error_output=obs_data.get("error_output", ""),
            tests_passed=obs_data.get("tests_passed", 0),
            tests_total=obs_data.get("tests_total", 0),
            step_number=obs_data.get("step_number", 0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata={},
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )


__all__ = ["CodeDebugEnvClient"]

