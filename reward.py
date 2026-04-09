# -*- coding: utf-8 -*-
"""Graded reward for deterministic code-debugging tasks."""

from __future__ import annotations

from typing import Dict


def compute_reward(scorecard: Dict[str, float], step_number: int, max_steps: int) -> float:
    syntax = max(0.0, min(1.0, float(scorecard.get("syntax", 0.0))))
    logic = max(0.0, min(1.0, float(scorecard.get("logic", 0.0))))
    optimal = max(0.0, min(1.0, float(scorecard.get("optimal", 0.0))))

    base = 0.3 * syntax + 0.5 * logic + 0.2 * optimal

    # Efficiency bonus
    efficiency = 0.05 * max(0.0, 1.0 - (step_number - 1) / max(1, max_steps)) if base > 0 else 0.0

    # Penalty for useless steps
    penalty = 0.0
    if logic == 0.0:
        penalty -= 0.1
    elif logic < 0.5:
        penalty -= 0.05

    reward = base + efficiency + penalty

    # Clamp STRICTLY between 0 and 1 (0.0 and 1.0 are both invalid)
    return round(max(0.001, min(0.999, reward)), 4)
