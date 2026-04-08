# -*- coding: utf-8 -*-
"""Deterministic baseline runner for CodeDebugEnv (CPU-only, no LLM calls)."""

from __future__ import annotations

from typing import Dict, List

from code_debug_env import CodeDebugEnv

BENCHMARK = "code-debug-env"
TASKS = ["easy", "medium", "hard"]


def simple_baseline(state: Dict[str, object]) -> str:
    task = str(state["task_name"])
    if task == "easy":
        return """def running_total(nums):
    result = []
    total = 0
    for n in nums:
        total += n
        result.append(total)
    return result
"""
    if task == "medium":
        return """def count_evens(nums):
    count = 0
    for n in nums:
        if n % 2 == 0:
            count += 1
    return count
"""
    return """import re

def normalize_text(text):
    text = text.lower()
    return re.sub(r"[^a-z0-9\\s]", "", text)

def tokenize_words(text):
    return [tok for tok in text.split() if tok]

def vectorize_counts(tokens):
    counts = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    return counts
"""


def run_task(task_name: str) -> float:
    env = CodeDebugEnv(task_name=task_name, seed=42)
    state = env.reset()
    print(f"[START] task={task_name} env={BENCHMARK} model=rule_based")

    rewards: List[float] = []
    done = False
    step = 0
    info: Dict[str, object] = {}

    while not done and step < int(state["max_steps"]):
        step += 1
        action = simple_baseline(state)
        state, reward, done, info = env.step(action)
        rewards.append(float(reward))
        err = str(state.get("error_output") or "null")
        err = err.replace("\n", " ")[:120]
        print(
            f"[STEP] step={step} reward={reward:.2f} done={str(done).lower()} "
            f"passed={state['tests_passed']}/{state['tests_total']} error={err}"
        )

    score = float(info.get("scorecard", {}).get("logic", 0.0)) if info else 0.0
    print(
        f"[END] success={str(score >= 1.0).lower()} steps={step} "
        f"score={score:.2f} rewards={','.join(f'{r:.2f}' for r in rewards)}"
    )
    env.close()
    return score


if __name__ == "__main__":
    all_scores = [run_task(task) for task in TASKS]
    print(f"[SUMMARY] mean_score={sum(all_scores)/len(all_scores):.2f}")
