import json
import urllib.request
from pathlib import Path

USERNAME = "jperocco"
LEAGUE_SEARCH = "Wookiee Moves"
LEAGUE_SEASON = 2026
STATS_SEASON = 2025
POSITIONS = ("QB", "RB", "WR", "TE")

API_V1 = "https://api.sleeper.app/v1"
API_STATS = "https://api.sleeper.com"

SCREENSHOT_QB_TARGETS = {
    "Joe Burrow": 834.0,
    "Jayden Daniels": 825.0,
    "Patrick Mahomes": 815.0,
    "Lamar Jackson": 814.0,
    "Josh Allen": 793.0,
    "Jalen Hurts": 768.0,
    "Baker Mayfield": 764.0,
    "Bo Nix": 759.0,
    "Brock Purdy": 759.0,
    "Kyler Murray": 756.0,
    "Dak Prescott": 748.0,
    "Trevor Lawrence": 742.0,
    "Drake Maye": 740.0,
    "C.J. Stroud": 729.0,
}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "WoRP-Lab-Sleeper-FP-Audit/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def user_and_league():
    user = get_json(f"{API_V1}/user/{USERNAME}")
    leagues = get_json(f"{API_V1}/user/{user['user_id']}/leagues/nfl/{LEAGUE_SEASON}")
    matches = [x for x in leagues if LEAGUE_SEARCH.lower() in x.get("name", "").lower()]
    if len(matches) != 1:
        names = [x.get("name") for x in matches]
        raise RuntimeError(f"Expected exactly one league matching {LEAGUE_SEARCH!r}; found {len(matches)}: {names}")
    return user, matches[0]

def normalize_stats_payload(payload):
    rows = []
    if isinstance(payload, list):
        source = payload
    elif isinstance(payload, dict):
        source = []
        for k, v in payload.items():
            if isinstance(v, dict):
                row = dict(v)
                row.setdefault("player_id", k)
                source.append(row)
    else:
        source = []

    for row in source:
        if not isinstance(row, dict):
            continue
        pid = row.get("player_id") or row.get("player", {}).get("player_id")
        stats = row.get("stats")
        if stats is None:
            stats = {k: v for k, v in row.items()
                     if k not in {"player_id", "player", "team", "position", "season", "week"}}
        if pid and isinstance(stats, dict):
            rows.append({"player_id": str(pid), "stats": stats})
    return rows

def calculate_points(stats, scoring):
    total = 0.0
    used = []
    missing = []
    for key, raw_weight in scoring.items():
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            continue
        if weight == 0:
            continue
        if key in stats:
            try:
                value = float(stats[key])
            except (TypeError, ValueError):
                value = 0.0
            total += value * weight
            used.append((key, value, weight, value * weight))
        else:
            missing.append(key)
    return total, used, missing

def main():
    user, league = user_and_league()
    scoring = league.get("scoring_settings", {}) or {}

    print("=" * 100)
    print("SLEEPER NATIVE FANTASY POINTS AUDIT")
    print("=" * 100)
    print("User:", user.get("username"))
    print("League:", league.get("name"))
    print("League season/settings:", LEAGUE_SEASON)
    print("Stats season:", STATS_SEASON)
    print("League ID:", league.get("league_id"))

    print("\nNon-zero scoring settings:")
    for k, v in sorted(scoring.items()):
        try:
            if float(v) != 0:
                print(f"  {k:28s} {v}")
        except Exception:
            pass

    print("\nFetching Sleeper player map...")
    players = get_json(f"{API_V1}/players/nfl")

    all_rows = []
    seen_stat_keys = set()

    for pos in POSITIONS:
        print(f"Fetching {STATS_SEASON} {pos} season stats...")
        url = f"{API_STATS}/stats/nfl/{STATS_SEASON}?season_type=regular&position={pos}"
        payload = get_json(url)
        rows = normalize_stats_payload(payload)

        for row in rows:
            pid = row["player_id"]
            stats = row["stats"]
            seen_stat_keys.update(stats.keys())
            pts, used, missing = calculate_points(stats, scoring)

            p = players.get(pid, {}) if isinstance(players, dict) else {}
            full_name = p.get("full_name") or " ".join(
                x for x in [p.get("first_name"), p.get("last_name")] if x
            ).strip() or pid
            position = p.get("position") or pos

            all_rows.append({
                "player_id": pid,
                "player_name": full_name,
                "position": position,
                "calculated_points": pts,
                "used": used,
                "missing": missing,
            })

    nonzero_scoring = {
        k for k, v in scoring.items()
        if isinstance(v, (int, float)) and float(v) != 0
    }
    found_keys = sorted(nonzero_scoring & seen_stat_keys)
    absent_keys = sorted(nonzero_scoring - seen_stat_keys)

    print("\n" + "=" * 100)
    print("SCORING KEY COVERAGE")
    print("=" * 100)
    print(f"Non-zero league scoring keys: {len(nonzero_scoring)}")
    print(f"Observed as exact stat keys: {len(found_keys)}")
    print(f"Not observed anywhere: {len(absent_keys)}")
    print("\nAbsent keys:")
    for key in absent_keys:
        print(" ", key)

    qbs = sorted(
        [r for r in all_rows if r["position"] == "QB"],
        key=lambda x: x["calculated_points"],
        reverse=True
    )

    print("\n" + "=" * 100)
    print("TOP 20 QB — OUR SLEEPER-NATIVE CALCULATION")
    print("=" * 100)
    print(f"{'RK':>2}  {'PLAYER':24s} {'CALC':>10s} {'FRONTEND':>10s} {'DELTA':>10s}")
    for i, row in enumerate(qbs[:20], 1):
        target = SCREENSHOT_QB_TARGETS.get(row["player_name"])
        if target is None:
            target_s = "-"
            delta_s = "-"
        else:
            target_s = f"{target:.1f}"
            delta_s = f"{row['calculated_points'] - target:+.3f}"
        print(f"{i:2d}  {row['player_name'][:24]:24s} {row['calculated_points']:10.3f} {target_s:>10s} {delta_s:>10s}")

    print("\n" + "=" * 100)
    print("SCREENSHOT RECONCILIATION")
    print("=" * 100)

    matched = 0
    exactish = 0
    deltas = []
    by_name = {r["player_name"]: r for r in qbs}

    for name, target in SCREENSHOT_QB_TARGETS.items():
        row = by_name.get(name)
        if row is None:
            print(f"MISS   {name}: not found")
            continue
        matched += 1
        delta = row["calculated_points"] - target
        deltas.append(abs(delta))
        if abs(delta) <= 0.5:
            exactish += 1
        print(f"{name:24s} calc={row['calculated_points']:8.3f} frontend={target:7.1f} delta={delta:+8.3f}")

    print()
    print(f"Targets matched by name: {matched}/{len(SCREENSHOT_QB_TARGETS)}")
    print(f"Within ±0.5 points:      {exactish}/{len(SCREENSHOT_QB_TARGETS)}")
    if deltas:
        print(f"Max absolute delta:      {max(deltas):.3f}")

    audit = {
        "league": {"name": league.get("name"), "league_id": league.get("league_id"), "season": LEAGUE_SEASON},
        "stats_season": STATS_SEASON,
        "scoring_settings": scoring,
        "found_scoring_keys": found_keys,
        "absent_scoring_keys": absent_keys,
        "qb_reconciliation": [
            {
                "player_name": name,
                "frontend_points": target,
                "calculated_points": by_name[name]["calculated_points"] if name in by_name else None,
                "delta": (by_name[name]["calculated_points"] - target if name in by_name else None),
            }
            for name, target in SCREENSHOT_QB_TARGETS.items()
        ],
    }

    Path("sleeper_fp_audit_result.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\nSaved sleeper_fp_audit_result.json")

    print("\nINTERPRETATION:")
    if matched >= 10 and exactish >= 10 and max(deltas or [999]) <= 0.5:
        print("PASS CANDIDATE: Sleeper-native season scoring closely reproduces the front end.")
        print("Next gate: weekly Sleeper stats → sum REG weeks → season total reconciliation.")
    else:
        print("NOT YET PASS: inspect absent scoring keys and player deltas before changing WoRP input source.")

if __name__ == "__main__":
    main()
