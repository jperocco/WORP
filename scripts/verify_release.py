#!/usr/bin/env python3
"""Validate a clean WoRP release without modifying the project."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def fail(message: str) -> None:
    print(f"PUBLICACAO BLOQUEADA: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if run("git", "branch", "--show-current") != "main":
        fail("use a branch main antes de publicar")
    if run("git", "status", "--porcelain"):
        fail("ha arquivos alterados; revise e salve/commite antes")

    print("Rodando testes...")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-p", "test_*.py"],
        cwd=ROOT,
    )
    if result.returncode:
        fail("os testes falharam")
    print("Tudo certo para publicar.")


if __name__ == "__main__":
    main()
