---
title: code-debug-env
emoji: 🐛
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---
# CodeDebugEnv

CodeDebugEnv is a deterministic reinforcement learning environment for program repair.
An agent receives buggy Python code and must submit a fixed version. The environment
scores each step with graded rewards (not binary pass/fail), enabling stable learning.

## Problem Statement

Large language models can generate code, but robust debugging requires iterative repair:
identify failure mode, patch, re-evaluate, and improve. This environment turns that workflow
into an RL benchmark with strict reproducibility and a curriculum of escalating difficulty.

## Environment Design

Core Gym-style API:

- `reset()` -> returns current state (buggy code + metadata)
- `step(action)` -> applies candidate fix and returns `(next_state, reward, done, info)`
- `state()` -> current environment state snapshot

OpenEnv adapter:

- `OpenEnvCodeDebugEnv` wraps the core environment and exposes OpenEnv-compatible
  observation/state interfaces for HTTP, WebSocket, and HF Spaces deployment.

## Task Curriculum

1. `easy` (syntax): missing colon/indentation in cumulative-sum function.
2. `medium` (logic): wrong branch condition in even counter.
3. `hard` (multi-function): text normalization + tokenization + aggregation pipeline bug.

Each task includes:

- buggy input code
- expected correct output
- deterministic Python evaluator function

## Action Space
- Field: `fixed_code` (string) — corrected Python source code
- Max length: ~2000 chars
- Also accepts: `message` as alias

## Observation Space  
- `buggy_code` (str) — the broken code to fix
- `expected_output` (str) — what correct output looks like
- `tests_passed` / `tests_total` (int) — progress signal
- `reward` (float, 0.0–1.0) — partial credit score
- `done` (bool) — episode complete
- `error_output` (str) — what failed

## Reward Logic (0.0 to 1.0)

- Syntax correctness: `+0.3`
- Logic/test correctness: `+0.5`
- Optimal/clean solution quality: `+0.2`
- Small deterministic efficiency bonus for earlier successful fixes

This gives dense credit and avoids brittle all-or-nothing scoring.

## Deterministic Evaluation

- Fixed seed: `42`
- No stochastic judges
- In-process Python execution with fixed evaluator functions
- Same input action always yields same reward and transition


## Run Baseline

```bash
python inference.py
```

The baseline is rule-based and CPU-only (no heavy model dependency). It prints:

- `[START]` per task
- `[STEP]` per transition
- `[END]` final task score
- `[SUMMARY]` mean score across easy/medium/hard

## OpenEnv / HF Space Validation

```bash
python -m openenv.cli validate .
python -m openenv.cli push --repo-id nikitapandey123/code-debug-env
```


## Local Docker

```bash
docker build -t code-debug-env .
docker run -p 7860:7860 code-debug-env
```
