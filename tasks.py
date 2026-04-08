# -*- coding: utf-8 -*-
"""Task definitions and deterministic evaluators for CodeDebugEnv."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def eval_easy_syntax(namespace: Dict[str, Any]) -> List[Tuple[str, bool, Any, Any]]:
    fn = namespace["running_total"]
    cases = [
        ("single", [4], [4]),
        ("mixed", [1, 2, 3], [1, 3, 6]),
        ("zeros", [0, 0, 5], [0, 0, 5]),
    ]
    return [(name, fn(inp) == expected, fn(inp), expected) for name, inp, expected in cases]


def eval_medium_logic(namespace: Dict[str, Any]) -> List[Tuple[str, bool, Any, Any]]:
    fn = namespace["count_evens"]
    cases = [
        ("none", [1, 3, 5], 0),
        ("some", [1, 2, 3, 4, 6], 3),
        ("all", [2, 4, 8], 3),
    ]
    return [(name, fn(inp) == expected, fn(inp), expected) for name, inp, expected in cases]


def eval_hard_multifunction(namespace: Dict[str, Any]) -> List[Tuple[str, bool, Any, Any]]:
    normalize = namespace["normalize_text"]
    tokenize = namespace["tokenize_words"]
    vectorize = namespace["vectorize_counts"]

    text = "Hello, HELLO world."
    norm = normalize(text)
    tokens = tokenize(norm)
    vec = vectorize(tokens)

    checks = [
        ("normalize", norm == "hello hello world", norm, "hello hello world"),
        ("tokenize", tokens == ["hello", "hello", "world"], tokens, ["hello", "hello", "world"]),
        ("vectorize", vec == {"hello": 2, "world": 1}, vec, {"hello": 2, "world": 1}),
    ]
    return checks


TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "name": "easy",
        "difficulty": "easy",
        "description": "Fix syntax issues in a cumulative-sum function (missing colon + indentation).",
        "max_steps": 6,
        "bug_type": "syntax",
        "buggy_code": '''\
def running_total(nums)
result = []
total = 0
for n in nums:
    total += n
    result.append(total)
return result
''',
        "expected_output": "[1, 3, 6] for input [1, 2, 3]",
        "evaluation_notes": "Function should compile and produce deterministic cumulative sums.",
        "evaluator": eval_easy_syntax,
    },
    "medium": {
        "name": "medium",
        "difficulty": "medium",
        "description": "Fix logical bug in even-number counting (wrong condition).",
        "max_steps": 8,
        "bug_type": "logic",
        "buggy_code": '''\
def count_evens(nums):
    count = 0
    for n in nums:
        if n % 2 == 1:
            count += 1
    return count
''',
        "expected_output": "3 for input [1, 2, 3, 4, 6]",
        "evaluation_notes": "Should count even integers only.",
        "evaluator": eval_medium_logic,
    },
    "hard": {
        "name": "hard",
        "difficulty": "hard",
        "description": "Fix multi-function text preprocessing pipeline (normalization, tokenization, aggregation).",
        "max_steps": 10,
        "bug_type": "multi_function",
        "buggy_code": '''\
def normalize_text(text):
    return text.lower()

def tokenize_words(text):
    return text.split(" ")

def vectorize_counts(tokens):
    counts = {}
    for t in tokens:
        counts[t] = 1
    return counts
''',
        "expected_output": "{'hello': 2, 'world': 1} for 'Hello, HELLO world.'",
        "evaluation_notes": "Must remove punctuation, avoid empty tokens, and aggregate repeated tokens correctly.",
        "evaluator": eval_hard_multifunction,
    },
}
