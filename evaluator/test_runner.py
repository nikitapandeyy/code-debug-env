def run_tests(code, tests):
    results = {
        "passed": 0,
        "total": len(tests),
        "all_passed": False,
        "error": None
    }

    try:
        local_env = {}
        exec(code, {}, local_env)

        for test in tests:
            func = local_env.get(test["function"])
            if not func:
                continue

            output = func(*test["input"])

            if output == test["expected"]:
                results["passed"] += 1

        results["all_passed"] = results["passed"] == results["total"]

    except Exception as e:
        results["error"] = str(e)

    return results
