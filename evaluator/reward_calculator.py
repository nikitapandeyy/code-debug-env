def compute_reward(result):
    if result["error"]:
        return -0.2

    if result["all_passed"]:
        return 1.0

    return (result["passed"] / result["total"]) * 0.5
