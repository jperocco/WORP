import json
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

USERNAME = "jperocco"
LEAGUE_SEARCH = "Wookiee Moves"
LEAGUE_SEASON = 2026
STATS_SEASONS = (2023, 2024, 2025)
WEEKS = range(1, 19)
POSITIONS = {"QB", "RB", "WR", "TE"}

API_V1 = "https://api.sleeper.app/v1"

def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "WoRP-Lab-Sleeper-3Y-FP-Audit/0.1"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def try_json(urls):
    last = None
    for url in urls:
        try:
            return get_json(url), url
        except Exception as e:
            last = e
    raise RuntimeError(f"All endpoint candidates failed. Last error: {last}")

def resolve_league():
    user = get_json(f"{API_V1}/user/{USERNAME}")
    leagues = get_json(
        f"{API_V1}/user/{user['user_id']}/leagues/nfl/{LEAGUE_SEASON}"
    )
    matches = [
        x for x in leagues
        if LEAGUE_SEARCH.lower() in x.get("name", "").lower()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one league matching {LEAGUE_SEARCH!r}; "
            f"found {len(matches)}: {[x.get('name') for x in matches]}"
        )
    return user, matches[0]

def normalize_payload(payload):
    """
    Normalizes common Sleeper stats payload shapes to:
        {player_id: stats_dict}
    """
    out = {}

    if isinstance(payload, dict):
        for key, value in payload.items():
            if not isinstance(value, dict):
                continue

            pid = (
                value.get("player_id")
                or (value.get("player") or {}).get("player_id")
                or key
            )
            stats = value.get("stats")
            if stats is None:
                stats = {
                    k: v for k, v in value.items()
                    if k not in {
                        "player_id", "player", "team", "position",
                        "season", "week", "category", "game_id"
                    }
                }
            if pid is not None and isinstance(stats, dict):
                out[str(pid)] = stats

    elif isinstance(payload, list):
        for value in payload:
            if not isinstance(value, dict):
                continue
            pid = (
                value.get("player_id")
                or (value.get("player") or {}).get("player_id")
            )
            stats = value.get("stats")
            if stats is None:
                stats = {
                    k: v for k, v in value.items()
                    if k not in {
                        "player_id", "player", "team", "position",
                        "season", "week", "category", "game_id"
                    }
                }
            if pid is not None and isinstance(stats, dict):
                out[str(pid)] = stats

    return out

def fetch_season_stats(season):
    payload, used_url = try_json([
        f"https://api.sleeper.com/stats/nfl/{season}?season_type=regular",
        f"https://api.sleeper.app/v1/stats/nfl/regular/{season}",
    ])
    return normalize_payload(payload), used_url

def fetch_week_stats(season, week):
    payload, used_url = try_json([
        f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular",
        f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}",
    ])
    return normalize_payload(payload), used_url

def calc_points(stats, scoring):
    total = 0.0
    for key, raw_weight in scoring.items():
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            continue
        if weight == 0:
            continue
        try:
            value = float(stats.get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        total += value * weight
    return total

def main():
    user, league = resolve_league()
    scoring = league.get("scoring_settings", {}) or {}
    players = get_json(f"{API_V1}/players/nfl")

    print("=" * 112)
    print("SLEEPER 3-YEAR FANTASY POINTS AUDIT")
    print("=" * 112)
    print("User:", user.get("username"))
    print("League:", league.get("name"))
    print("League settings season:", LEAGUE_SEASON)
    print("Stats seasons:", STATS_SEASONS)
    print("League ID:", league.get("league_id"))
    print()

    all_results = {}
    global_max_delta = 0.0
    global_rows = 0
    global_within_001 = 0
    global_within_01 = 0

    for season in STATS_SEASONS:
        print("\n" + "=" * 112)
        print(f"SEASON {season}")
        print("=" * 112)

        season_stats, season_url = fetch_season_stats(season)
        print("Season endpoint:", season_url)
        print("Season players:", len(season_stats))

        weekly_sum = defaultdict(float)
        weekly_seen = defaultdict(int)
        weekly_urls = []

        for week in WEEKS:
            week_stats, week_url = fetch_week_stats(season, week)
            weekly_urls.append(week_url)

            for pid, stats in week_stats.items():
                weekly_sum[pid] += calc_points(stats, scoring)
                weekly_seen[pid] += 1

            print(
                f"  Week {week:2d}: {len(week_stats):4d} player rows"
            )

        rows = []
        for pid, sstats in season_stats.items():
            p = players.get(pid, {}) if isinstance(players, dict) else {}
            pos = p.get("position")
            if pos not in POSITIONS:
                continue

            season_points = calc_points(sstats, scoring)
            week_points = weekly_sum.get(pid, 0.0)
            delta = week_points - season_points

            rows.append({
                "player_id": pid,
                "player_name": p.get("full_name") or pid,
                "position": pos,
                "season_points": season_points,
                "weekly_sum_points": week_points,
                "delta": delta,
                "weeks_with_row": weekly_seen.get(pid, 0),
            })

        abs_deltas = [abs(r["delta"]) for r in rows]
        max_delta = max(abs_deltas) if abs_deltas else 0.0
        within_001 = sum(d <= 0.01 for d in abs_deltas)
        within_01 = sum(d <= 0.10 for d in abs_deltas)

        global_max_delta = max(global_max_delta, max_delta)
        global_rows += len(rows)
        global_within_001 += within_001
        global_within_01 += within_01

        print("\nRECONCILIATION SUMMARY")
        print(f"QB/RB/WR/TE rows:           {len(rows)}")
        print(f"Within ±0.01 points:        {within_001}/{len(rows)}")
        print(f"Within ±0.10 points:        {within_01}/{len(rows)}")
        print(f"Max absolute delta:         {max_delta:.6f}")

        worst = sorted(rows, key=lambda x: abs(x["delta"]), reverse=True)[:15]
        print("\n15 LARGEST DELTAS")
        print(
            f"{'PLAYER':26s} {'POS':>3s} {'SEASON':>11s} "
            f"{'WEEK SUM':>11s} {'DELTA':>11s} {'WKS':>4s}"
        )
        for r in worst:
            print(
                f"{r['player_name'][:26]:26s} {r['position']:>3s} "
                f"{r['season_points']:11.3f} "
                f"{r['weekly_sum_points']:11.3f} "
                f"{r['delta']:+11.3f} "
                f"{r['weeks_with_row']:4d}"
            )

        leaders = sorted(
            rows,
            key=lambda x: x["weekly_sum_points"],
            reverse=True
        )[:20]
        print("\nTOP 20 BY WEEKLY-SUM FANTASY POINTS")
        print(
            f"{'RK':>2s} {'PLAYER':26s} {'POS':>3s} "
            f"{'WEEK SUM':>11s} {'SEASON':>11s} {'DELTA':>9s}"
        )
        for i, r in enumerate(leaders, 1):
            print(
                f"{i:2d} {r['player_name'][:26]:26s} {r['position']:>3s} "
                f"{r['weekly_sum_points']:11.3f} "
                f"{r['season_points']:11.3f} "
                f"{r['delta']:+9.3f}"
            )

        all_results[str(season)] = {
            "season_endpoint": season_url,
            "weekly_endpoint_example": weekly_urls[0] if weekly_urls else None,
            "rows": len(rows),
            "within_001": within_001,
            "within_01": within_01,
            "max_abs_delta": max_delta,
            "worst_deltas": worst,
            "top20": leaders,
        }

    print("\n" + "=" * 112)
    print("3-YEAR GATE")
    print("=" * 112)
    print(f"Total player-season rows:   {global_rows}")
    print(f"Within ±0.01:               {global_within_001}/{global_rows}")
    print(f"Within ±0.10:               {global_within_01}/{global_rows}")
    print(f"Max absolute delta:         {global_max_delta:.6f}")

    # Strict candidate threshold: nearly every row should reconcile to cents.
    pass_candidate = (
        global_rows > 0
        and global_within_001 / global_rows >= 0.99
        and global_max_delta <= 0.10
    )

    if pass_candidate:
        print("\nPASS CANDIDATE ✅")
        print(
            "Sleeper weekly stats summed across REG closely reproduce "
            "Sleeper season stats under the league scoring."
        )
        print(
            "This is the data contract WoRP needs for weekly calculation "
            "and 3-Year WoRP Avg."
        )
    else:
        print("\nNOT YET PASS ❌")
        print(
            "Inspect the largest deltas before making Sleeper-native weekly "
            "stats the WoRP production datasource."
        )

    Path("sleeper_3year_fp_audit_result.json").write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\nSaved sleeper_3year_fp_audit_result.json")

if __name__ == "__main__":
    main()
