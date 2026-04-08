def apply_action(code, action):
    lines = code.split("\n")

    line = min(action["line"], len(lines)-1)

    if action["type"] == "replace":
        lines[line] = action["content"]

    elif action["type"] == "delete" and len(lines) > 1:
        lines.pop(line)

    elif action["type"] == "insert":
        lines.insert(line, action["content"])

    return "\n".join(lines)
