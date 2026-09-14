#!/usr/bin/env python3
"""One-command WoRP Structural Insights regression cycle.

Runs:
  1) git pull --ff-only
  2) newest build_worp_lab_vX_Y_Z.py builder
  3) structural_insights_harness.py --app matching app_vX_Y_Z.py

Usage:
    python3 worp_test.py
"""

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BUILDER_RE = re.compile(r"^build_worp_lab_v(\d+)_(\d+)_(\d+)\.py$")


def run(cmd):
    print("\n$ " + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def newest_builder():
    found = []
    for path in ROOT.glob("build_worp_lab_v*.py"):
        m = BUILDER_RE.match(path.name)
        if m:
            found.append((tuple(map(int, m.groups())), path))
    if not found:
        raise SystemExit("STOP: no versioned WoRP builder found")
    return max(found, key=lambda x: x[0])


def main():
    run(["git", "pull", "--ff-only"])

    version, builder = newest_builder()
    version_text = "_".join(map(str, version))
    app = ROOT / f"app_v{version_text}.py"
    harness = ROOT / "structural_insights_harness.py"

    if not harness.exists():
        raise SystemExit("STOP: structural_insights_harness.py not found")

    print(f"\nLatest builder: {builder.name}")
    run([sys.executable, builder.name])

    if not app.exists():
        raise SystemExit(f"STOP: expected {app.name} was not created")

    print(f"\nRegression app: {app.name}")
    run([sys.executable, harness.name, "--app", app.name])


if __name__ == "__main__":
    main()
