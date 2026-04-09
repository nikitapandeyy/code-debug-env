# -*- coding: utf-8 -*-
"""LLM-based baseline runner for CodeDebugEnv."""

from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from typing import Dict, List

from openai import OpenAI

from code_debug_env import CodeDebugEnv

BENCHMARK = "code-debug-env"
TASKS = ["easy", "medium", "hard"]

API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN", "")
MODEL_NAME   = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)


def llm_fix_code(buggy_code: str, expected_output: str, error_output: str, task_name: str) -> str:
    prompt = f"""You are an expert Python debugger. Fix the following buggy Python code.

Task: {task_name}
Expected output description: {expected_output}
Current error or failing tests: {error_output or 'none'}

Buggy code:
```python
{buggy_code}
```

Return ONLY the fixed Python code, no explanation, no markdown fences, no preamble.
"""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.0,
    )
    fixed = response.choices[0].message.content.strip()
    if fixed.startswith("```"):
        lines = fixed.splitlines()
        fixed = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        )
    return fixed.strip()


def run_task(task_name: str) -> float:
    env = CodeDebugEnv(task_name=task_name, seed=42)
    state = env.reset()
    print(f"[START] task={task_name} env={BENCHMARK} model={MODEL_NAME}")

    rewards: List[float] = []
    done = False
    step = 0
    info: Dict[str, object] = {}

    while not done and step < int(state["max_steps"]):
        step += 1

        try:
            action = llm_fix_code(
                buggy_code=state["buggy_code"],
                expected_output=state["expected_output"],
                error_output=str(state.get("error_output") or ""),
                task_name=task_name,
            )
        except Exception as exc:
            err_msg = str(exc).replace("\n", " ")[:120]
            print(f"[STEP] step={step} action='error' reward=0.001 done=true error={err_msg}")
            print(f"[END] success=false steps={step} score=0.001 rewards=0.001")
            env.close()
            return 0.001

        state, reward, done, info = env.step(action)
        rewards.append(float(reward))

        action_preview = action.replace("\n", " ")[:60]
        err = str(state.get("error_output") or "null").replace("\n", " ")[:80]
        print(
            f"[STEP] step={step} action='{action_preview}' "
            f"reward={reward:.4f} done={str(done).lower()} error={err}"
        )

    raw_score = float(info.get("scorecard", {}).get("logic", 0.0)) if info else 0.0
    score = max(0.001, min(0.999, raw_score))
    success = raw_score >= 1.0

    print(
        f"[END] success={str(success).lower()} steps={step} "
        f"score={score:.4f} rewards={','.join(f'{r:.4f}' for r in rewards)}"
    )
    env.close()
    return score


if __name__ == "__main__":
    all_scores = [run_task(task) for task in TASKS]
    print(f"[SUMMARY] mean_score={sum(all_scores) / len(all_scores):.4f}")
