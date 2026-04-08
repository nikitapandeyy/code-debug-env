# -*- coding: utf-8 -*-
"""
Run this BEFORE pushing to HF to find charset issues.
Usage: python fix_encoding.py
"""
import os
import re

EXTENSIONS = (".py", ".toml", ".yaml", ".yml", ".md", ".txt", ".json")
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}

REPLACEMENTS = {
    "\u2019": "'",   # right single quote
    "\u2018": "'",   # left single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u2013": "-",   # en dash
    "\u2014": "--",  # em dash
    "\u2192": "->",  # arrow
    "\u00e9": "e",   # e acute
    "\u2026": "...", # ellipsis
    "\u00a0": " ",   # non-breaking space
    "\x9d": "",      # Windows-1252 garbage byte
}


def fix_file(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try Windows encoding
        try:
            with open(path, "r", encoding="cp1252") as f:
                content = f.read()
            print(f"  Re-encoding from cp1252: {path}")
        except Exception as e:
            print(f"  CANNOT READ: {path} -- {e}")
            return False

    original = content
    for bad, good in REPLACEMENTS.items():
        content = content.replace(bad, good)

    # Remove any remaining non-ASCII from Python files
    if path.endswith(".py"):
        content = content.encode("ascii", errors="ignore").decode("ascii")

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Fixed: {path}")
        return True
    return False


def scan():
    fixed = 0
    bad = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not any(fname.endswith(ext) for ext in EXTENSIONS):
                continue
            path = os.path.join(root, fname)
            try:
                open(path, encoding="utf-8").read()
            except UnicodeDecodeError:
                bad.append(path)
                if fix_file(path):
                    fixed += 1

    if bad:
        print(f"\nFound {len(bad)} files with encoding issues. Fixed {fixed}.")
    else:
        print("All files are valid UTF-8. Safe to push.")


if __name__ == "__main__":
    scan()
