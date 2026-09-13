#!/usr/bin/env python3
"""Fast CLI regression harness for WoRP Lab Structural Insights.

First run:
    python3 structural_insights_harness.py setup

Then:
    python3 structural_insights_harness.py

The harness loads the calculation/editor definitions from the generated app but
never launches Streamlit UI. It keeps the same WoRP Engine/editor code path while
stripping Streamlit decorators and top-level UI execution.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
import urllib.request
from pathlib import Path

APP_PATH = Path("app_v0_8_0.py")
CONFIG_DIR = Path.home() / ".worp_lab"
CONFIG_PATH = CONFIG_DIR / "structural_insights_harness.json"
DEFAULT_SEASONS = (2023, 2024, 2025)
DEFAULT_N_SIMS = 4000
DEFAULT_SEED = 7
SLEEPER_BASE = "https://api.sleeper.app/v1"


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRP-Lab-Harness/0.2"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _is_upper_assignment(node):
    """Keep module constants needed by calculation helpers, not UI state."""
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        return bool(names) and all(n.isupper() for n in names)
    return False


def _strip_decorators(node):
    """Definitions are identical; Streamlit caching is unnecessary in CLI."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        node.decorator_list = []
    return node


def _load_core_namespace(app_path: Path):
    """Load calculation/editor code from the app without executing its UI.

    Previous harness V0.1 stopped at the first top-level st.* call. Current WoRP
    apps define calculate_league_intelligence_cached later in the file, after UI
    setup, so that extractor could never see it.

    V0.2 instead builds a definition-only module containing:
      * imports
      * module-level UPPERCASE constants (engine/cache/API constants)
      * every function/class definition, wherever it appears in the app

    Function decorators are stripped so @st.cache_data does not require a live
    Streamlit runtime. Function bodies themselves are not rewritten.
    """
    if not app_path.exists():
        raise SystemExit(f"STOP: {app_path} not found. Build V0.8.0 first.")

    source = app_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(app_path))

    kept = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            kept.append(node)
        elif _is_upper_assignment(node):
            kept.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kept.append(_strip_decorators(node))

    module = ast.Module(body=kept, type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {"__name__": "worp_harness_core", "__file__": str(app_path)}
    try:
        exec(compile(module, str(app_path), "exec"), ns, ns)
    except Exception as exc:
        raise SystemExit(f"STOP: could not load app calculation core: {type(exc).__name__}: {exc}")

    if "calculate_league_intelligence_cached" not in ns:
        funcs = sorted(k for k, v in ns.items() if callable(v) and not k.startswith("__"))
        raise SystemExit(
            "STOP: calculate_league_intelligence_cached not found in definition-only app core. "
            f"Loaded functions: {', '.join(funcs[:25])}"
        )
    return ns


def _format_counts(roster_positions):
    counts = {}
    for p in roster_positions or []:
        counts[p] = counts.get(p, 0) + 1
    return counts


def _league_call_kwargs(calc, league, seasons, n_sims, seed):
    counts = _format_counts(league.get("roster_positions") or [])
    scoring = league.get("scoring_settings") or {}
    scoring_json = json.dumps(scoring, sort_keys=True, separators=(",", ":"))

    known = {
        "teams": int(league.get("total_rosters") or 0),
        "qb": int(counts.get("QB", 0)),
        "rb": int(counts.get("RB", 0)),
        "wr": int(counts.get("WR", 0)),
        "te": int(counts.get("TE", 0)),
        "flex": int(counts.get("FLEX", 0)),
        "superflex": int(counts.get("SUPER_FLEX", 0)),
        "scoring_json": scoring_json,
        "seasons": tuple(int(x) for x in seasons),
        "n_sims": int(n_sims),
        "seed": int(seed),
    }

    sig = inspect.signature(calc)
    kwargs = {}
    missing = []
    for name, param in sig.parameters.items():
        if name in known:
            kwargs[name] = known[name]
        elif param.default is inspect._empty:
            missing.append(name)

    if missing:
        raise RuntimeError(f"Harness does not know required calculate args: {missing}")
    return kwargs


def _fetch_user_leagues(username: str, season: int):
    user = _get_json(f"{SLEEPER_BASE}/user/{username}")
    if not user or not user.get("user_id"):
        raise SystemExit(f"STOP: Sleeper user not found: {username}")
    uid = user["user_id"]
    leagues = _get_json(f"{SLEEPER_BASE}/user/{uid}/leagues/nfl/{season}") or []
    return leagues


def _setup(args):
    username = args.user or input("Sleeper username: ").strip()
    season = int(args.sleeper_season)
    leagues = _fetch_user_leagues(username, season)
    if not leagues:
        raise SystemExit(f"STOP: no Sleeper leagues found for {username} in {season}")

    leagues = sorted(leagues, key=lambda x: str(x.get("name", "")).lower())
    print("\nChoose regression leagues (comma-separated numbers).\n")
    for i, lg in enumerate(leagues, start=1):
        rp = lg.get("roster_positions") or []
        print(f"{i:>2}. {lg.get('name','(unnamed)')}  [{lg.get('league_id')}]  slots={','.join(rp)}")

    raw = input("\nSelection (example: 1,4,7,9,12): ").strip()
    picks = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        idx = int(part)
        if idx < 1 or idx > len(leagues):
            raise SystemExit(f"STOP: invalid selection {idx}")
        picks.append(leagues[idx - 1])

    if not picks:
        raise SystemExit("STOP: select at least one league")

    cfg = {
        "username": username,
        "sleeper_season": season,
        "league_ids": [str(x["league_id"]) for x in picks],
        "league_names": {str(x["league_id"]): str(x.get("name", "")) for x in picks},
        "historical_seasons": list(DEFAULT_SEASONS),
        "n_sims": DEFAULT_N_SIMS,
        "seed": DEFAULT_SEED,
        "app_path": str(APP_PATH),
    }
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"\nPASS: saved {len(picks)} regression leagues to {CONFIG_PATH}")
    print("Next time run: python3 structural_insights_harness.py")


def _load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit("STOP: harness not configured. Run: python3 structural_insights_harness.py setup")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _resolve_saved_leagues(cfg):
    leagues = _fetch_user_leagues(cfg["username"], int(cfg["sleeper_season"]))
    by_id = {str(x.get("league_id")): x for x in leagues}
    resolved = []
    missing = []
    for lid in cfg.get("league_ids", []):
        if str(lid) in by_id:
            resolved.append(by_id[str(lid)])
        else:
            missing.append(str(lid))
    if missing:
        print(f"WARN: saved league IDs not found this season: {', '.join(missing)}")
    return resolved


def _print_insights(league, insight_df):
    name = league.get("name", "(unnamed)")
    lid = league.get("league_id", "")
    rp = league.get("roster_positions") or []
    print("\n" + "=" * 100)
    print(f"{name}  [{lid}]")
    print(f"slots: {', '.join(rp)}")
    print("-" * 100)

    if insight_df is None or getattr(insight_df, "empty", True):
        print("NO STRUCTURAL INSIGHTS")
        return

    for i, (_, row) in enumerate(insight_df.head(5).iterrows(), start=1):
        title = row.get("title", "")
        detail = row.get("detail", "")
        story_id = row.get("story_id", "")
        family = row.get("family", "")
        position = row.get("position", "")
        ed = row.get("editorial_score", None)
        mat = row.get("materiality", None)
        conf = row.get("confidence", None)
        act = row.get("actionability", None)
        print(f"\n{i}. {title}")
        print(f"   {detail}")
        diagnostic = f"story={story_id} | family={family} | pos={position}"
        if ed is not None:
            try:
                diagnostic += f" | editor={float(ed):.3f}"
            except Exception:
                pass
        for label, val in (("M", mat), ("C", conf), ("A", act)):
            if val is not None:
                try:
                    diagnostic += f" | {label}={float(val):.2f}"
                except Exception:
                    pass
        print(f"   [{diagnostic}]")


def _run(args):
    cfg = _load_config()
    app_path = Path(args.app or cfg.get("app_path") or APP_PATH)
    ns = _load_core_namespace(app_path)
    calc = ns["calculate_league_intelligence_cached"]
    leagues = _resolve_saved_leagues(cfg)
    if not leagues:
        raise SystemExit("STOP: no saved regression leagues could be resolved")

    seasons = tuple(cfg.get("historical_seasons") or DEFAULT_SEASONS)
    n_sims = int(args.n_sims or cfg.get("n_sims") or DEFAULT_N_SIMS)
    seed = int(cfg.get("seed") or DEFAULT_SEED)

    print(f"WoRP Structural Insights Harness | app={app_path} | seasons={seasons} | sims={n_sims}")
    print(f"Regression leagues: {len(leagues)}")

    failures = 0
    for league in leagues:
        try:
            kwargs = _league_call_kwargs(calc, league, seasons, n_sims, seed)
            result = calc(**kwargs)
            if not isinstance(result, tuple) or len(result) < 5:
                raise RuntimeError(f"unexpected calculate return shape: {type(result)} / {getattr(result, '__len__', lambda: '?')()}")
            insight_df = result[4]
            _print_insights(league, insight_df)
        except Exception as exc:
            failures += 1
            print("\n" + "=" * 100)
            print(f"FAIL: {league.get('name','(unnamed)')} [{league.get('league_id','')}]")
            print(f"{type(exc).__name__}: {exc}")

    print("\n" + "=" * 100)
    if failures:
        print(f"HARNESS RESULT: {failures} league(s) failed")
        sys.exit(1)
    print(f"HARNESS RESULT: PASS ({len(leagues)} leagues)")


def main():
    parser = argparse.ArgumentParser(description="WoRP Structural Insights CLI regression harness")
    sub = parser.add_subparsers(dest="command")

    setup = sub.add_parser("setup", help="choose and save regression leagues")
    setup.add_argument("--user", help="Sleeper username")
    setup.add_argument("--sleeper-season", type=int, default=2026)

    parser.add_argument("--app", help="app file to test (default saved app_v0_8_0.py)")
    parser.add_argument("--n-sims", type=int, help="override Monte Carlo sims")

    args = parser.parse_args()
    if args.command == "setup":
        _setup(args)
    else:
        _run(args)


if __name__ == "__main__":
    main()
