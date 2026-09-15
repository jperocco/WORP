from pathlib import Path
import json
import hashlib
import time
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st
from sleeper_native_loader import load_sleeper_player_weeks, fetch_player_map, validate_weekly_contract

st.set_page_config(page_title="WoRP Lab", page_icon="Ⓦ", layout="wide")

API = "https://api.sleeper.app/v1"
CURRENT_SEASON = 2026
DATA_CANDIDATES = [
    Path("worp_2016_2025_normalized.csv"),
    Path("worp_2016_2025_rankings.csv"),
]

@st.cache_data
def load_history():
    for path in DATA_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path)
            if "worp_per_game" not in df.columns:
                df["worp_per_game"] = df["worp"] / df["games"]
            if "worp_17g_pace" not in df.columns:
                df["worp_17g_pace"] = df["worp_per_game"] * 17
            return df, path.name
    return None, None

@st.cache_data(ttl=300)
def sleeper_get(path):
    req = urllib.request.Request(
        API + path,
        headers={"User-Agent": "WoRP-Lab/0.9.4"}
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))

def get_user(username):
    return sleeper_get(f"/user/{username.strip()}")

def get_leagues(user_id, season):
    return sleeper_get(f"/user/{user_id}/leagues/nfl/{season}")

def get_rosters(league_id):
    return sleeper_get(f"/league/{league_id}/rosters")

def get_users(league_id):
    return sleeper_get(f"/league/{league_id}/users")

def format_counts(roster_positions):
    counts = {}
    for p in roster_positions or []:
        counts[p] = counts.get(p, 0) + 1
    return counts

def league_format_label(league):
    c = format_counts(league.get("roster_positions", []))
    pieces = [f"{league.get('total_rosters', '?')}T"]
    for key, label in [("QB","QB"),("RB","RB"),("WR","WR"),("TE","TE"),("FLEX","FLEX"),("SUPER_FLEX","SF")]:
        if c.get(key):
            pieces.append(f"{c[key]}{label}")
    return " · ".join(pieces)

def scoring_summary(sc):
    rec = sc.get("rec", 0)
    te_bonus = sc.get("bonus_rec_te", 0)
    pass_td = sc.get("pass_td", 0)
    return f"{rec:g} PPR · TE bonus {te_bonus:+g} · Pass TD {pass_td:g}"


def build_three_year_curve(df, seasons=(2023, 2024, 2025), top_n=50):
    """Presentation-layer benchmark only. Does not alter WoRP math."""
    if df is None or df.empty:
        return pd.DataFrame()
    need = {"season", "player_name", "position", "worp"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    d = df[df["season"].isin(seasons) & df["position"].isin(["QB","RB","WR","TE"])].copy()
    if d.empty:
        return pd.DataFrame()
    # Average season WoRP for each player across the seasons in which he appears,
    # then rank those player averages within position. This is a descriptive benchmark.
    g = (d.groupby(["position","player_name"], as_index=False)["worp"]
           .mean().rename(columns={"worp":"three_year_worp_avg"}))
    g["position_rank"] = g.groupby("position")["three_year_worp_avg"].rank(method="first", ascending=False).astype(int)
    return g[g["position_rank"] <= top_n].sort_values(["position","position_rank"])

history, history_source = load_history()

st.title("WoRP Lab")
st.caption("USER → LEAGUE → GRAPH · Engine V0.2.1 frozen · UI V0.9.4")

with st.sidebar:
    st.header("Sleeper")
    username = st.text_input("Username", placeholder="Sleeper username")
    season = st.selectbox("League season", [2026, 2025, 2024, 2023], index=0)
    connect = st.button("Connect", type="primary", use_container_width=True)
    if history_source:
        st.divider()
        st.caption(f"Historical data: {history_source}")

if "sleeper_user" not in st.session_state:
    st.session_state.sleeper_user = None
if "leagues" not in st.session_state:
    st.session_state.leagues = []

if connect:
    if not username.strip():
        st.warning("Enter a Sleeper username.")
    else:
        try:
            user = get_user(username)
            if not user:
                st.error("Sleeper user not found.")
            else:
                leagues = get_leagues(user["user_id"], season)
                st.session_state.sleeper_user = user
                st.session_state.leagues = leagues or []
        except Exception as e:
            st.error(f"Sleeper connection failed: {e}")

user = st.session_state.sleeper_user
leagues = st.session_state.leagues

if not user:
    st.markdown("### Connect your Sleeper account")
    st.write("Enter a public Sleeper username in the sidebar. No password or API token is required.")
    st.info("V0.7.2: five league-specific Structural Insights + Value Cliffs + faster compute.")
    st.stop()

st.success(f"Connected: {user.get('display_name') or user.get('username')}  ·  @{user.get('username')}")

if not leagues:
    st.warning(f"No NFL leagues found for {season}.")
    st.stop()

league_map = {f"{x.get('name','Unnamed league')}  —  {league_format_label(x)}": x for x in leagues}

league_search = st.text_input(
    "Search leagues",
    placeholder="Type part of the league name",
)

if league_search.strip():
    needle = league_search.strip().lower()
    filtered_labels = [
        label for label in league_map
        if needle in label.lower()
    ]
else:
    filtered_labels = list(league_map.keys())

st.caption(f"{len(filtered_labels)} of {len(league_map)} leagues shown")

if not filtered_labels:
    st.warning("No leagues match your search.")
    st.stop()

choice = st.selectbox("League", filtered_labels)
league = league_map[choice]

st.subheader(league.get("name", "League"))
st.caption(league_format_label(league) + " · " + scoring_summary(league.get("scoring_settings", {})))

a,b,c,d = st.columns(4)
a.metric("Teams", league.get("total_rosters", "—"))
counts = format_counts(league.get("roster_positions", []))
b.metric("Starters", sum(v for k,v in counts.items() if k not in {"BN","IR","TAXI"}))
c.metric("Superflex", counts.get("SUPER_FLEX", 0))
d.metric("TE starters", counts.get("TE", 0))

with st.expander("Detected league settings"):
    st.write("Roster positions:", league.get("roster_positions", []))
    st.json(league.get("scoring_settings", {}))

try:
    rosters = get_rosters(league["league_id"])
    users = get_users(league["league_id"])
except Exception as e:
    st.error(f"Could not load league rosters/users: {e}")
    st.stop()

user_by_id = {u.get("user_id"): u for u in users}
rows = []
for r in rosters:
    owner = user_by_id.get(r.get("owner_id"), {})
    team_name = (owner.get("metadata") or {}).get("team_name")
    rows.append({
        "Roster": r.get("roster_id"),
        "Manager": owner.get("display_name") or owner.get("username") or "Orphan",
        "Team": team_name or owner.get("display_name") or owner.get("username") or f"Roster {r.get('roster_id')}",
        "Players": len(r.get("players") or []),
        "Starters": len(r.get("starters") or []),
        "Wins": (r.get("settings") or {}).get("wins"),
        "Losses": (r.get("settings") or {}).get("losses"),
    })

roster_df = pd.DataFrame(rows).sort_values("Roster")


st.markdown("### Historical WoRP")

st.success(
    "Sleeper-native scoring validated · 9,132 / 9,132 player-seasons "
    "reconciled within ±0.01 in the 2023–2025 validation fixture."
)

st.caption(
    "Exact Sleeper scoring → frozen WoRP Engine V0.2.1 → league-specific "
    "historical positional curve and observed player board."
)

control_a, control_b, control_c = st.columns([1.4, 1, 1])

with control_a:
    window_label = st.selectbox(
        "3-Year window",
        ["2023–2025", "2022–2024", "2021–2023"],
        index=0,
        help=(
            "The selected league's current scoring settings are applied to all "
            "three historical seasons."
        ),
    )

with control_b:
    top_n = st.selectbox(
        "Curve depth",
        [24, 36, 50],
        index=2,
    )

with control_c:
    n_sims_ui = st.selectbox(
        "Monte Carlo",
        [2000, 4000, 8000],
        index=1,
        format_func=lambda x: {2000: "2,000 · Fast preview", 4000: "4,000 · Standard", 8000: "8,000 · Validated control"}[x],
        help="Historical results are persisted by scoring + format + season after the first calculation. 8,000 remains the validated control setting.",
    )

window_map = {
    "2023–2025": (2023, 2024, 2025),
    "2022–2024": (2022, 2023, 2024),
    "2021–2023": (2021, 2022, 2023),
}
selected_seasons = window_map[window_label]

compute = st.button(
    "Calculate league-specific 3-Year WoRP",
    type="primary",
    width="stretch",
)

@st.cache_data(ttl=86400, show_spinner=False)
def load_scored_history_cached(seasons, scoring_json):
    """Cache expensive Sleeper historical input preparation separately from Monte Carlo."""
    sc = json.loads(scoring_json)
    player_map = fetch_player_map()
    all_weeks, endpoint_log = load_sleeper_player_weeks(
        seasons=tuple(seasons),
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)
    return all_weeks, endpoint_log


ENGINE_CACHE_VERSION = "worp_engine_v0_2_1"
ENGINE_CACHE_DIR = Path.home() / ".worp_lab" / "season_rankings_v0_2_1"


def _season_ranking_cache_path(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    season, n_sims, seed, replacement_band=6,
):
    payload = {
        "engine": ENGINE_CACHE_VERSION,
        "teams": int(teams), "qb": int(qb), "rb": int(rb), "wr": int(wr),
        "te": int(te), "flex": int(flex), "superflex": int(superflex),
        "scoring_json": scoring_json,
        "season": int(season), "n_sims": int(n_sims), "seed": int(seed),
        "replacement_band": int(replacement_band),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:24]
    ENGINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return ENGINE_CACHE_DIR / f"{int(season)}_{digest}.pkl"


from worp_lineup_economics_v0_9_4 import build_lineup_scoring_share

@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    seasons=(2023, 2024, 2025), n_sims=4000, seed=7
):
    from worp_engine import LeagueSettings, calculate_season_worp
    t_calc0 = time.perf_counter()

    sc = json.loads(scoring_json)

    settings = LeagueSettings(
        teams=int(teams),
        qb=int(qb),
        rb=int(rb),
        wr=int(wr),
        te=int(te),
        flex=int(flex),
        superflex=int(superflex),
        ppr=float(sc.get("rec", 0.0)),
        te_premium=float(sc.get("bonus_rec_te", 0.0)),
    )

    # Base historical scoring/input prep is cached independently from Monte Carlo.
    rankings = {}
    engine_timings = []
    cache_hits = {}
    cache_paths = {}

    for season_i in seasons:
        cache_paths[int(season_i)] = _season_ranking_cache_path(
            teams, qb, rb, wr, te, flex, superflex, scoring_json,
            int(season_i), int(n_sims), int(seed), replacement_band=6,
        )

    missing_seasons = []
    for season_i in seasons:
        season_i = int(season_i)
        path = cache_paths[season_i]
        if path.exists():
            try:
                ranking = pd.read_pickle(path)
                rankings[season_i] = ranking
                cache_hits[season_i] = True
            except Exception:
                missing_seasons.append(season_i)
                cache_hits[season_i] = False
        else:
            missing_seasons.append(season_i)
            cache_hits[season_i] = False

    if missing_seasons:
        all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)
        t_after_load = time.perf_counter()
        for season_i in missing_seasons:
            season_df = all_weeks[all_weeks["season"] == int(season_i)].copy()
            t_engine0 = time.perf_counter()
            _weekly, ranking = calculate_season_worp(
                season_df,
                settings,
                replacement_band=6,
                n_sims=int(n_sims),
                seed=int(seed),
            )
            engine_timings.append((int(season_i), time.perf_counter() - t_engine0))
            ranking = ranking.copy()
            ranking["season"] = int(season_i)
            ranking["position_rank"] = (
                ranking.groupby("position")["worp"]
                .rank(method="first", ascending=False)
                .astype(int)
            )
            rankings[int(season_i)] = ranking
            try:
                ranking.to_pickle(cache_paths[int(season_i)])
            except Exception:
                pass
    else:
        # Fully warm historical configuration: no Sleeper fetch, no Monte Carlo.
        all_weeks = pd.DataFrame()
        endpoint_log = {}
        t_after_load = time.perf_counter()

    t_after_engine = time.perf_counter()

    # Rank-average positional curve:
    # rank players within position in each season, then average the WoRP
    # attached to each positional rank across the three seasons.
    curve_frames = []
    for season_i, ranking in rankings.items():
        x = ranking[
            ranking["position"].isin(["QB", "RB", "WR", "TE"])
        ].copy()
        curve_frames.append(
            x[["season", "position", "position_rank", "worp"]]
        )

    curve_source = pd.concat(curve_frames, ignore_index=True)
    curve = (
        curve_source
        .groupby(["position", "position_rank"], as_index=False)
        .agg(
            three_year_worp_avg=("worp", "mean"),
            seasons_present=("season", "nunique"),
        )
    )
    curve = curve[curve["seasons_present"] == len(seasons)].copy()

    # Attach each year's abstract positional-rank WoRP to the curve.
    # Example: QB1 = mean(QB1/2023, QB1/2024, QB1/2025).
    # No player identity is used in this aggregation.
    for season_i in seasons:
        annual = (
            curve_source[curve_source["season"] == int(season_i)]
            [["position", "position_rank", "worp"]]
            .rename(columns={"worp": f"worp_{int(season_i)}"})
        )
        curve = curve.merge(
            annual,
            on=["position", "position_rank"],
            how="left",
        )

    curve["concept"] = (
        curve["position"]
        + curve["position_rank"].astype(int).astype(str)
    )
    curve = curve.sort_values(["position", "position_rank"])

    # Player board. This is player-specific, unlike the rank-average curve.
    player_frames = []
    for season_i, ranking in rankings.items():
        cols = ["season", "player_name", "position", "worp", "position_rank"]
        for optional in ["games", "porp", "worp_per_game"]:
            if optional in ranking.columns:
                cols.append(optional)

        x = ranking[ranking["position"].isin(["QB", "RB", "WR", "TE"])][cols].copy()

        if "worp_per_game" not in x.columns and "games" in x.columns:
            safe_games = x["games"].replace(0, pd.NA)
            x["worp_per_game"] = x["worp"] / safe_games

        player_frames.append(x)

    player_seasons = pd.concat(player_frames, ignore_index=True)

    agg_spec = {
        "three_year_worp_avg": ("worp", "mean"),
        "three_year_worp_total": ("worp", "sum"),
        "seasons": ("season", "nunique"),
        "avg_position_rank": ("position_rank", "mean"),
        "best_position_rank": ("position_rank", "min"),
    }
    if "games" in player_seasons.columns:
        agg_spec["games"] = ("games", "sum")
    if "porp" in player_seasons.columns:
        agg_spec["avg_porp"] = ("porp", "mean")
    if "worp_per_game" in player_seasons.columns:
        agg_spec["avg_worp_per_game"] = ("worp_per_game", "mean")

    player_summary = (
        player_seasons
        .groupby(["position", "player_name"], as_index=False)
        .agg(**agg_spec)
    )

    latest = max(seasons)
    latest_rows = (
        player_seasons[player_seasons["season"] == latest]
        [["position", "player_name", "worp", "position_rank"]]
        .rename(columns={
            "worp": "latest_worp",
            "position_rank": "latest_position_rank",
        })
    )
    player_summary = player_summary.merge(
        latest_rows,
        on=["position", "player_name"],
        how="left",
    )

    # Simple descriptive cliffs: largest loss over the next 5 ranks.
    cliffs = []
    for pos in ["QB", "RB", "WR", "TE"]:
        x = curve[curve["position"] == pos].sort_values("position_rank").copy()
        x["five_rank_drop"] = (
            x["three_year_worp_avg"]
            - x["three_year_worp_avg"].shift(-5)
        )
        x = x.dropna(subset=["five_rank_drop"])
        if not x.empty:
            row = x.loc[x["five_rank_drop"].idxmax()]
            cliffs.append({
                "position": pos,
                "cliff_start_rank": int(row["position_rank"]),
                "cliff_end_rank": int(row["position_rank"]) + 5,
                "worp_drop": float(row["five_rank_drop"]),
                "start_worp": float(row["three_year_worp_avg"]),
            })
    cliff_df = pd.DataFrame(cliffs)

    # Product layer V0.7.4: league-aware story editor.
    # The engine remains descriptive/historical. The editor is allowed to publish
    # only economically relevant ranges at or before the observed replacement frontier.
    def _value_at(pos, rank):
        row = curve[(curve["position"] == pos) & (curve["position_rank"] == int(rank))]
        if row.empty:
            return None
        return float(row.iloc[0]["three_year_worp_avg"])

    positions = ["QB", "RB", "WR", "TE"]

    # Engine-native relevance frontier. This is NOT a universal positional cutoff:
    # it is derived from this league format and these historical seasons.
    frontier_samples = {p: [] for p in positions}
    for _season_i, _ranking in rankings.items():
        if "avg_replacement_effective_rank" not in _ranking.columns:
            continue
        for pos in positions:
            vals = pd.to_numeric(
                _ranking.loc[_ranking["position"] == pos, "avg_replacement_effective_rank"],
                errors="coerce",
            ).dropna()
            if not vals.empty:
                frontier_samples[pos].append(float(vals.median()))

    frontier_by_pos = {
        pos: (sum(vals) / len(vals) if vals else None)
        for pos, vals in frontier_samples.items()
    }

    def _frontier_rank(pos):
        f = frontier_by_pos.get(pos)
        return None if f is None else max(1, int(round(f)))

    def _relevant(pos, end_rank):
        f = _frontier_rank(pos)
        return f is None or int(end_rank) <= f

    def _window_value(pos, a, b):
        va, vb = _value_at(pos, a), _value_at(pos, b)
        if va is None or vb is None:
            return None
        return float(va - vb)

    # -------------------------------------------------------------------------
    # Product layer V0.7.6 — STORY-FIRST EDITOR
    # Evidence -> structural hypothesis -> roster-construction story -> ranking.
    # A metric is never itself a headline. Engine V0.2.1 remains descriptive.
    # -------------------------------------------------------------------------
    story_candidates = []

    def _add_story(story_id, family, position, score, title, detail,
                   materiality, confidence, actionability, evidence=None):
        # Explicit product contract: every candidate must carry a decision story,
        # not merely a statistic. Scores are editorial ranking inputs, not claims.
        story_candidates.append({
            "story_id": str(story_id),
            "family": str(family),
            "position": str(position),
            "score": float(score),
            "materiality": float(materiality),
            "confidence": float(confidence),
            "actionability": float(actionability),
            "title": str(title),
            "detail": str(detail),
            "evidence": evidence or {},
        })

    # STORY A — ELITE CONCENTRATION + CHEAPER DEPTH
    # Synthesize head steepness and later marginal cost into one economic story.
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 12:
            continue
        elite_end = min(8, f)
        post_end = min(f, max(12, int(round(f * 0.45))))
        head = _window_value(pos, 1, elite_end)
        post = _window_value(pos, elite_end, post_end)
        if head is None or post is None or post_end <= elite_end:
            continue
        head_per_rank = head / max(1, elite_end - 1)
        post_per_rank = post / max(1, post_end - elite_end)
        ratio = head_per_rank / max(post_per_rank, 0.01)
        if head >= 0.70 and ratio >= 1.55:
            materiality = min(2.0, head)
            confidence = min(1.5, 0.80 + ratio * 0.12)
            actionability = 1.35
            _add_story(
                f"elite_then_depth:{pos}", "elite_depth", pos,
                materiality + confidence + actionability,
                f"Protect access to elite {pos}",
                (
                    f"The top of {pos} is expensive: {pos}1 to {pos}{elite_end} loses {head:.2f} WoRP. "
                    f"After that, the curve gets cheaper before replacement near {pos}{f}. "
                    "Prioritize access to the elite tier; be more selective paying for smaller upgrades behind it."
                ),
                materiality, confidence, actionability,
                {"head_drop": head, "head_end": elite_end, "frontier": f, "slope_ratio": ratio},
            )

    # STORY B — EXPENSIVE WAITING / PERSISTENT SCARCITY
    # The window scales with this league's own replacement frontier. This remains
    # a supporting heuristic until Task 2 replaces windows with whole-curve shape.
    runway = []
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 12:
            continue
        a = min(8, max(1, int(round(f * 0.20))))
        b = min(f, max(a + 5, int(round(f * 0.70))))
        if b <= a:
            continue
        drop = _window_value(pos, a, b)
        if drop is not None:
            per10 = drop / max(1, b - a) * 10.0
            runway.append((pos, a, b, drop, per10, f))
    if runway:
        pos, a, b, drop, per10, f = max(runway, key=lambda z: z[4])
        if drop > 0:
            _add_story(
                f"waiting_cost:{pos}", "scarcity", pos,
                1.10 + min(per10, 2.0) * 0.85,
                f"Waiting at {pos} has been expensive",
                (
                    f"Across the relevant {pos} pool, moving from {pos}{a} to {pos}{b} gives up {drop:.2f} WoRP "
                    f"before replacement near {pos}{f}. This is a position where waiting has carried a real sporting cost."
                ),
                min(1.6, drop), 1.05, 1.25,
                {"start": a, "end": b, "drop": drop, "per10": per10, "frontier": f},
            )

    # STORY C — CHEAP MID-RANGE UPGRADES / CAPITAL EFFICIENCY PREVIEW
    # Sporting WoRP only: rank is NOT acquisition price. Keep the claim narrowly
    # about the historical marginal value purchased by moving up this curve.
    compressions = []
    for pos in positions:
        f = _frontier_rank(pos)
        if f is None or f < 16:
            continue
        a = max(8, int(round(f * 0.35)))
        b = min(f, max(a + 6, int(round(f * 0.70))))
        if b <= a or not _relevant(pos, b):
            continue
        drop = _window_value(pos, a, b)
        if drop is not None:
            cost10 = drop / max(1, b - a) * 10.0
            compressions.append((pos, a, b, cost10, drop, f))
    if compressions:
        pos, a, b, cost10, drop, f = min(compressions, key=lambda z: z[3])
        if cost10 >= 0:
            cheapness = max(0.0, 1.25 - cost10)
            _add_story(
                f"cheap_midrange:{pos}", "capital_efficiency", pos,
                0.90 + cheapness,
                f"Mid-range {pos} upgrades buy relatively little WoRP",
                (
                    f"Between {pos}{a} and {pos}{b}, moving 10 ranks costs about {cost10:.2f} WoRP. "
                    "Historically, small upgrades in this part of the relevant pool have produced limited marginal value."
                ),
                min(1.2, cheapness + 0.35), 0.95, 1.10,
                {"start": a, "end": b, "cost_per_10": cost10, "frontier": f},
            )

    # STORY D — FORMAT-DRIVEN QB DEMAND
    # V0.7.5 slot-eligibility semantics are preserved. This story describes legal
    # starting capacity; it does not pretend every eligible slot will contain a QB.
    if int(superflex) > 0:
        f = _frontier_rank("QB")
        fixed_qb_per_team = int(qb)
        sf_per_team = int(superflex)
        qb_eligible_per_team = fixed_qb_per_team + sf_per_team
        qb_eligible_leaguewide = int(teams) * qb_eligible_per_team
        if f is not None:
            if fixed_qb_per_team == 0:
                title = "QB demand is created by flexible starter eligibility"
                detail = (
                    f"There are no fixed QB slots, but each team has {sf_per_team} QB-eligible flexible "
                    f"slot{'s' if sf_per_team != 1 else ''}. Historical replacement sits near QB{f}. "
                    "Build QB depth around where QBs can legally start, not around a traditional QB-slot count."
                )
            else:
                title = "QB depth is part of the starting lineup in this format"
                detail = (
                    f"Each team has {qb_eligible_per_team} QB-eligible starting slots "
                    f"({fixed_qb_per_team} fixed + {sf_per_team} flexible), while historical replacement sits near QB{f}. "
                    "Treat QB depth as lineup construction, not merely bench insurance."
                )
            pressure = max(0.0, f - qb_eligible_leaguewide) / max(int(teams), 1)
            _add_story(
                "format_qb_demand", "format_demand", "QB",
                3.20 + min(pressure, 2.0) * 0.20,
                title, detail,
                1.30, 1.30, 1.45,
                {"fixed_qb_per_team": fixed_qb_per_team, "sf_per_team": sf_per_team,
                 "qb_eligible_leaguewide": qb_eligible_leaguewide, "frontier": f},
            )

    # STORY E — FLEX ABSORPTION OF RB/WR/TE DEPTH
    # This is the first roster-utilization bridge, but deliberately limited to
    # legal capacity. It does NOT claim observed lineup capture or manager behavior.
    if int(flex) >= 3:
        wr_f, rb_f, te_f = _frontier_rank("WR"), _frontier_rank("RB"), _frontier_rank("TE")
        if wr_f is not None and rb_f is not None:
            flexible_capacity = int(flex)
            deeper_pos, deeper_f = ("WR", wr_f) if wr_f >= rb_f else ("RB", rb_f)
            _add_story(
                "flex_depth_absorption", "lineup_capacity", deeper_pos,
                2.75 + min(flexible_capacity, 8) * 0.10,
                "This lineup can turn skill-position depth into starters",
                (
                    f"Each team has {flexible_capacity} RB/WR/TE-eligible FLEX slot{'s' if flexible_capacity != 1 else ''}. "
                    f"Historical replacement reaches roughly WR{wr_f} and RB{rb_f}. "
                    "In this format, useful skill-position depth has more paths into the starting lineup instead of being automatically treated as bench depth."
                ),
                1.15, 1.20, 1.35,
                {"flex_per_team": flexible_capacity, "wr_frontier": wr_f,
                 "rb_frontier": rb_f, "te_frontier": te_f},
            )

    # STORY F — TE FORMAT DEMAND
    if int(te) >= 2 or float(sc.get("bonus_rec_te", 0.0)) > 0:
        f = _frontier_rank("TE")
        if f is not None:
            premium = float(sc.get("bonus_rec_te", 0.0))
            if int(te) >= 2 and premium > 0:
                title = "TE demand is reinforced by both lineup and scoring"
            elif int(te) >= 2:
                title = "Two-TE lineups deepen usable TE demand"
            else:
                title = "TE premium changes where TE value matters"
            _add_story(
                "format_te_demand", "format_demand", "TE",
                2.80 + min(int(te), 2) * 0.10 + (0.15 if premium > 0 else 0.0),
                title,
                (
                    f"Historical TE replacement sits near TE{f} under this league's scoring and lineup structure. "
                    "Evaluate TE depth against this league's demand rather than a generic 1TE format."
                ),
                1.10, 1.20, 1.25,
                {"te_slots": int(te), "te_premium": premium, "frontier": f},
            )

    # STORY G — RELEVANT VALUE CLIFF AS A ROSTER DECISION
    # Value Cliffs remains separately visible. Only the strongest pre-replacement
    # cliff may become a card, and only if it adds a distinct economic story.
    relevant_cliffs = []
    if cliff_df is not None and not cliff_df.empty:
        for _, r in cliff_df.iterrows():
            pos = str(r["position"])
            a, b = int(r["cliff_start_rank"]), int(r["cliff_end_rank"])
            if _relevant(pos, b):
                relevant_cliffs.append((pos, a, b, float(r["worp_drop"])))
    if relevant_cliffs:
        pos, a, b, drop = max(relevant_cliffs, key=lambda z: z[3])
        if drop >= 0.55:
            _add_story(
                f"cliff:{pos}", "cliff", pos,
                1.40 + drop,
                f"Avoid crossing the {pos}{a}–{pos}{b} value cliff cheaply",
                (
                    f"That short move gives up {drop:.2f} WoRP, the sharpest relevant cliff on this league's board. "
                    "If moving down through it, demand compensation for the historical value lost."
                ),
                min(1.6, drop), 1.15, 1.30,
                {"start": a, "end": b, "drop": drop},
            )

    # -------------------------------------------------------------------------
    # TASK-1 EDITORIAL GATE
    # This is intentionally simple and inspectable. Later backlog tasks will add
    # formal materiality, whole-curve segmentation and richer semantic dedupe.
    # -------------------------------------------------------------------------
    # One economic story ID = one candidate. If duplicate evidence created the
    # same story, retain the strongest version.
    best_by_story = {}
    for c in story_candidates:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # Prevent the known QB duplication: when the league format itself explains
    # QB starting demand, a generic QB waiting-cost card is supporting evidence,
    # not a second headline story.
    if any(c["story_id"] == "format_qb_demand" for c in candidates):
        candidates = [
            c for c in candidates
            if not (c["position"] == "QB" and c["story_id"].startswith("waiting_cost:"))
        ]

    # Same principle for TE: format-driven demand outranks a generic mid-range TE
    # compression card when both would mostly tell the manager how to price TE in
    # this league. Value Cliffs remains separately visible below the cards.
    if any(c["story_id"] == "format_te_demand" for c in candidates):
        candidates = [
            c for c in candidates
            if not (c["position"] == "TE" and c["story_id"].startswith("cheap_midrange:"))
        ]

    # If a position already has the synthesized elite+depth story, suppress a
    # cliff card when that cliff is entirely inside the elite range; it is evidence
    # for the same story, not another card.
    elite_story_positions = {
        c["position"] for c in candidates if c["story_id"].startswith("elite_then_depth:")
    }
    filtered = []
    for c in candidates:
        if c["story_id"].startswith("cliff:") and c["position"] in elite_story_positions:
            ev = c.get("evidence", {})
            if int(ev.get("end", 999)) <= 8:
                continue
        filtered.append(c)
    candidates = filtered

    # -------------------------------------------------------------------------
    # V0.7.7 CROSS-POSITION DECISION ENGINE
    # Compare positions only where the decision is economically comparable.
    # - Elite draft/trade capital: RB/WR/TE same positional rank band.
    # - FLEX decisions: only RB/WR/TE, because they share FLEX eligibility.
    # This does NOT assume rank itself is market price; it compares historical
    # WoRP produced by similarly ranked positional assets in this league.
    # -------------------------------------------------------------------------
    def _avg_rank_band(pos, a, b):
        vals = []
        for r in range(int(a), int(b) + 1):
            v = _value_at(pos, r)
            if v is not None:
                vals.append(float(v))
        return (sum(vals) / len(vals)) if vals else None

    # 1) ELITE INTERPOSITIONAL PRIORITY
    # Replace several "protect elite X" cards with one decision if one skill
    # position clearly generates more WoRP across the same elite rank band.
    elite_band_end = 8
    elite_scores = []
    for pos in ["RB", "WR", "TE"]:
        f = _frontier_rank(pos)
        if f is None or f < elite_band_end:
            continue
        avg = _avg_rank_band(pos, 1, elite_band_end)
        if avg is not None:
            elite_scores.append((pos, avg))

    if len(elite_scores) >= 2:
        elite_scores = sorted(elite_scores, key=lambda z: z[1], reverse=True)
        win_pos, win_avg = elite_scores[0]
        second_pos, second_avg = elite_scores[1]
        elite_edge = win_avg - second_avg

        # Materiality gate: do not manufacture a preference from noise.
        if elite_edge >= 0.12:
            _add_story(
                "crosspos_elite_priority", "cross_position", win_pos,
                4.50 + min(elite_edge, 1.0),
                f"At the elite tier, prioritize {win_pos} over {second_pos}",
                (
                    f"Across {win_pos}1–{win_pos}{elite_band_end}, {win_pos} averages {win_avg:.2f} WoRP versus "
                    f"{second_avg:.2f} for {second_pos}1–{second_pos}{elite_band_end}. "
                    f"For similarly ranked elite assets in this league, {win_pos} has delivered about {elite_edge:.2f} more WoRP per player. "
                    "That makes the position the stronger structural target when draft or trade capital is comparable."
                ),
                min(1.8, 1.10 + elite_edge), 1.25, 1.50,
                {"rank_start": 1, "rank_end": elite_band_end,
                 "winner": win_pos, "runner_up": second_pos,
                 "winner_avg": win_avg, "runner_up_avg": second_avg,
                 "avg_edge": elite_edge},
            )

            # The cross-position card now carries the elite decision. Keep only
            # elite intra-position cards that tell a genuinely different story.
            candidates = [
                c for c in candidates
                if not (
                    c["story_id"].startswith("elite_then_depth:")
                    and c["position"] in {"RB", "WR", "TE"}
                )
            ]

    # 2) FLEX INTERPOSITIONAL PREFERENCE
    # Compare RB/WR/TE at several same-rank anchors inside the shared relevant
    # pool. Require a stable winner, not a single-rank accident.
    if int(flex) > 0:
        flex_positions = []
        for pos in ["RB", "WR", "TE"]:
            f = _frontier_rank(pos)
            if f is not None and f >= 12:
                flex_positions.append((pos, f))

        if len(flex_positions) >= 2:
            common_frontier = min(f for _, f in flex_positions)
            raw_anchors = [
                max(8, int(round(common_frontier * 0.30))),
                max(9, int(round(common_frontier * 0.45))),
                max(10, int(round(common_frontier * 0.60))),
                max(11, int(round(common_frontier * 0.75))),
            ]
            anchors = sorted({min(common_frontier, a) for a in raw_anchors})

            wins = {p: 0 for p, _ in flex_positions}
            values_by_pos = {p: [] for p, _ in flex_positions}

            for r in anchors:
                rank_values = []
                for p, _ in flex_positions:
                    v = _value_at(p, r)
                    if v is not None:
                        values_by_pos[p].append(float(v))
                        rank_values.append((p, float(v)))
                if len(rank_values) >= 2:
                    rank_values.sort(key=lambda z: z[1], reverse=True)
                    wins[rank_values[0][0]] += 1

            avg_values = []
            for p, vals in values_by_pos.items():
                if vals:
                    avg_values.append((p, sum(vals) / len(vals)))

            if len(avg_values) >= 2 and anchors:
                avg_values.sort(key=lambda z: z[1], reverse=True)
                flex_win, flex_win_avg = avg_values[0]
                flex_second, flex_second_avg = avg_values[1]
                flex_edge = flex_win_avg - flex_second_avg
                stable_wins = wins.get(flex_win, 0)
                required_wins = max(2, (len(anchors) // 2) + 1)

                if stable_wins >= required_wins and flex_edge >= 0.10:
                    rank_text = ", ".join(str(x) for x in anchors)
                    _add_story(
                        "crosspos_flex_preference", "cross_position", flex_win,
                        4.10 + min(flex_edge, 0.8),
                        f"For comparable FLEX-range assets, lean {flex_win} over {flex_second}",
                        (
                            f"At shared rank checkpoints ({rank_text}), {flex_win} leads the eligible skill positions in "
                            f"{stable_wins} of {len(anchors)} comparisons and averages about {flex_edge:.2f} more WoRP than {flex_second}. "
                            f"When similarly ranked {flex_win}/{flex_second} options compete for flexible lineup capital, "
                            f"this league's historical structure favors {flex_win}."
                        ),
                        min(1.6, 1.00 + flex_edge), 1.20, 1.45,
                        {"anchors": anchors, "winner": flex_win, "runner_up": flex_second,
                         "winner_avg": flex_win_avg, "runner_up_avg": flex_second_avg,
                         "avg_edge": flex_edge, "wins": wins,
                         "common_frontier": common_frontier},
                    )

    # Newly added cross-position stories must participate in the same semantic
    # story-ID contract as the rest of the editor.
    best_by_story = {}
    for c in candidates + [c for c in story_candidates if c["family"] == "cross_position"]:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # -------------------------------------------------------------------------
    # V0.7.8 CROSS-POSITION EQUIVALENCE ENGINE
    # Question: at the same WoRP level, how deep into another eligible position's
    # curve can a manager go? Example shape: RB40 ~= WR20.
    #
    # This is stronger than same-rank comparison because FLEX decisions are made
    # between players, not between labels such as RB20 and WR20.
    # -------------------------------------------------------------------------
    def _equivalent_rank(pos, target_worp, max_rank=None):
        f = _frontier_rank(pos)
        if f is None:
            return None
        stop = int(f if max_rank is None else min(f, int(max_rank)))
        best = None
        for r in range(1, stop + 1):
            v = _value_at(pos, r)
            if v is None:
                continue
            diff = abs(float(v) - float(target_worp))
            if best is None or diff < best[0]:
                best = (diff, r, float(v))
        return best

    # Search FLEX-compatible skill positions for the strongest economically useful
    # rank equivalence. Stay before replacement and away from near-zero tail noise.
    equivalence_candidates = []
    if int(flex) > 0:
        skill_positions = ["RB", "WR", "TE"]
        for target_pos in skill_positions:
            target_frontier = _frontier_rank(target_pos)
            if target_frontier is None:
                continue

            # Start at rank 8 so this is not merely another elite card. Stop at
            # 80% of the target frontier to keep the comparison roster-relevant.
            target_end = max(8, int(round(target_frontier * 0.80)))
            for target_rank in range(8, target_end + 1):
                target_worp = _value_at(target_pos, target_rank)
                if target_worp is None or target_worp < 0.20:
                    continue

                for source_pos in skill_positions:
                    if source_pos == target_pos:
                        continue
                    eq = _equivalent_rank(source_pos, target_worp)
                    if eq is None:
                        continue
                    diff, source_rank, source_worp = eq

                    # We care about the powerful case: the same economic value
                    # survives materially deeper in one position's curve.
                    rank_gap = int(source_rank) - int(target_rank)
                    if rank_gap < 6:
                        continue

                    # Approximate equivalence guardrail. Allow a little more
                    # tolerance at high WoRP, but do not equate visibly different
                    # values simply because ranks are far apart.
                    tolerance = max(0.08, abs(float(target_worp)) * 0.12)
                    if diff > tolerance:
                        continue

                    rank_multiple = float(source_rank) / max(float(target_rank), 1.0)
                    equivalence_candidates.append({
                        "source_pos": source_pos,
                        "source_rank": int(source_rank),
                        "source_worp": float(source_worp),
                        "target_pos": target_pos,
                        "target_rank": int(target_rank),
                        "target_worp": float(target_worp),
                        "rank_gap": rank_gap,
                        "rank_multiple": rank_multiple,
                        "worp_diff": float(diff),
                    })

    if equivalence_candidates:
        # Prefer large rank leverage at a still-material WoRP level. This makes a
        # statement such as RB40 ~= WR20 more valuable than tiny tail equivalence.
        equivalence_candidates.sort(
            key=lambda x: (
                x["rank_gap"] * min(x["target_worp"], 1.5),
                x["rank_multiple"],
                -x["worp_diff"],
            ),
            reverse=True,
        )
        eq = equivalence_candidates[0]

        _add_story(
            "crosspos_rank_equivalence", "cross_position_equivalence", eq["source_pos"],
            5.00 + min(eq["rank_gap"] / 20.0, 1.0),
            f"{eq['source_pos']} value survives much deeper than {eq['target_pos']}",
            (
                f"{eq['source_pos']}{eq['source_rank']} ({eq['source_worp']:.2f} WoRP) is roughly equivalent to "
                f"{eq['target_pos']}{eq['target_rank']} ({eq['target_worp']:.2f} WoRP). "
                f"The same historical value appears about {eq['rank_gap']} positional ranks deeper at {eq['source_pos']}. "
                f"When {eq['source_pos']} and {eq['target_pos']} compete for FLEX or roster capital, do not treat the deeper "
                f"{eq['source_pos']} rank as automatically less valuable."
            ),
            1.60, 1.30, 1.55,
            {"source_position": eq["source_pos"], "source_rank": eq["source_rank"],
             "source_worp": eq["source_worp"], "target_position": eq["target_pos"],
             "target_rank": eq["target_rank"], "target_worp": eq["target_worp"],
             "rank_gap": eq["rank_gap"], "rank_multiple": eq["rank_multiple"],
             "worp_diff": eq["worp_diff"]},
        )

        # The equivalence story is a richer version of the generic same-rank FLEX
        # preference. Keep elite priority, but avoid spending two cards on the same
        # RB-vs-WR middle-of-curve message.
        candidates = [
            c for c in candidates
            if c.get("story_id") != "crosspos_flex_preference"
        ]

    # -------------------------------------------------------------------------
    # DECISION-ONLY FORMAT GATE
    # Format is evidence, not a headline. A card that merely says TEP/SF/FLEX
    # changes demand does not earn Top 5 unless it resolves into a concrete roster
    # decision. Current TE-format card is the known weak case from V0.7.7.
    # -------------------------------------------------------------------------
    candidates = [
        c for c in candidates
        if c.get("story_id") != "format_te_demand"
    ]

    # Add the new equivalence story through the same semantic-story contract.
    best_by_story = {}
    for c in candidates + [
        c for c in story_candidates
        if c.get("family") == "cross_position_equivalence"
    ]:
        sid = c["story_id"]
        if sid not in best_by_story or c["score"] > best_by_story[sid]["score"]:
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # -------------------------------------------------------------------------
    # V0.7.9 DECISION-RELEVANCE EDITOR
    # -------------------------------------------------------------------------
    # Shared-slot decision relevance is an editorial prior, not a WoRP claim.
    # RB/WR decisions are most directly recurrent in FLEX roster construction;
    # TE participates too, but dedicated TE demand makes a pure rank-gap less
    # automatically transferable. We therefore reward shared FLEX competition
    # and material equivalence, while still allowing TE stories to win when the
    # economic evidence is clearly stronger.
    pair_relevance = {
        frozenset(("RB", "WR")): 1.00,
        frozenset(("RB", "TE")): 0.82,
        frozenset(("WR", "TE")): 0.82,
    }

    # Re-score equivalence candidates using decision relevance rather than raw
    # rank-gap spectacle. The V0.7.8 candidate stores the pair and equivalence
    # evidence; if field names evolve, use conservative defaults rather than
    # inventing evidence.
    for c in candidates:
        if c.get("family") != "cross_position_equivalence":
            continue
        ev = c.get("evidence", {}) or {}
        p1 = str(ev.get("position_a", ev.get("deeper_position", c.get("position", ""))))
        p2 = str(ev.get("position_b", ev.get("shallower_position", "")))
        relevance = pair_relevance.get(frozenset((p1, p2)), 0.70)
        gap = abs(float(ev.get("rank_gap", 0.0) or 0.0))
        worp_gap = abs(float(ev.get("worp_gap", 0.0) or 0.0))
        # Equivalence quality: smaller WoRP mismatch is better. Rank gap matters,
        # but only after decision relevance; huge gaps do not automatically win.
        equivalence_quality = max(0.0, 1.0 - min(worp_gap, 0.25) / 0.25)
        c["decision_relevance"] = relevance
        c["editorial_score"] = (
            c.get("materiality", 1.0) * 0.30 +
            c.get("confidence", 1.0) * 0.20 +
            c.get("actionability", 1.0) * 0.25 +
            relevance * 0.20 +
            equivalence_quality * 0.05
        )
        c["score"] = float(c.get("score", 0.0)) + relevance * 0.55 + min(gap, 20.0) * 0.01

    # Build a specifically RB-vs-WR equivalence candidate when both positions
    # share FLEX eligibility and a material cross-rank equivalence exists. This
    # prevents a larger but less recurrent RB-vs-TE rank gap from monopolizing
    # the equivalence slot merely because the number is bigger.
    if int(flex) > 0:
        rb_f = _frontier_rank("RB")
        wr_f = _frontier_rank("WR")
        if rb_f is not None and wr_f is not None:
            # Search the full relevant curves. For each deeper RB rank, find the
            # closest WR WoRP and retain a material, close equivalence. Avoid the
            # elite band already covered by the elite-priority story.
            rbwr_matches = []
            for rb_rank in range(9, int(rb_f) + 1):
                rb_val = _value_at("RB", rb_rank)
                if rb_val is None:
                    continue
                best = None
                for wr_rank in range(1, int(wr_f) + 1):
                    wr_val = _value_at("WR", wr_rank)
                    if wr_val is None:
                        continue
                    diff = abs(float(rb_val) - float(wr_val))
                    if best is None or diff < best[0]:
                        best = (diff, wr_rank, float(wr_val))
                if best is None:
                    continue
                diff, wr_rank, wr_val = best
                rank_gap = rb_rank - wr_rank
                # We want meaningful cross-rank equivalence, not RB17 ~= WR16.
                if rank_gap >= 6 and diff <= 0.08:
                    # Prefer a large but roster-relevant gap, with an anchor that
                    # remains inside both replacement frontiers.
                    strength = rank_gap * 0.08 + max(0.0, 0.08 - diff) * 4.0
                    rbwr_matches.append((strength, rb_rank, float(rb_val), wr_rank, wr_val, diff, rank_gap))

            if rbwr_matches:
                _, rb_rank, rb_val, wr_rank, wr_val, diff, rank_gap = max(rbwr_matches, key=lambda x: x[0])
                _add_story(
                    "crosspos_equivalence_rb_wr", "cross_position_equivalence", "RB",
                    5.15 + min(rank_gap, 20) * 0.03,
                    f"RB{rb_rank} has carried roughly WR{wr_rank} value",
                    (
                        f"RB{rb_rank} ({rb_val:.2f} WoRP) is roughly equivalent to WR{wr_rank} ({wr_val:.2f} WoRP). "
                        f"The same historical value survives about {rank_gap} positional ranks deeper at RB. "
                        "Because RB and WR compete directly for FLEX capacity, do not assume the deeper RB is the lesser roster asset."
                    ),
                    min(1.8, 1.05 + rank_gap * 0.025), 1.30, 1.60,
                    {"position_a": "RB", "position_b": "WR", "deeper_position": "RB",
                     "shallower_position": "WR", "deeper_rank": rb_rank,
                     "shallower_rank": wr_rank, "rank_gap": rank_gap,
                     "worp_a": rb_val, "worp_b": wr_val, "worp_gap": diff,
                     "shared_slot": "FLEX", "decision_relevance": 1.0},
                )

    # Rebuild story-ID map after adding the decision-relevant equivalence.
    best_by_story = {}
    for c in candidates + [c for c in story_candidates if c.get("story_id") == "crosspos_equivalence_rb_wr"]:
        sid = c["story_id"]
        if sid not in best_by_story or c.get("score", 0.0) > best_by_story[sid].get("score", 0.0):
            best_by_story[sid] = c
    candidates = list(best_by_story.values())

    # If a strong RB/WR equivalence exists, generic FLEX-capacity copy is no
    # longer allowed to consume a Top-5 slot. The equivalence itself explains
    # which depth the lineup can exploit and why.
    has_rbwr_equivalence = any(c.get("story_id") == "crosspos_equivalence_rb_wr" for c in candidates)
    if has_rbwr_equivalence:
        candidates = [c for c in candidates if c.get("story_id") != "flex_depth_absorption"]
        # Same-rank FLEX preference is also weaker evidence than cross-rank
        # economic equivalence; keep one economic story = one card.
        candidates = [c for c in candidates if c.get("story_id") != "crosspos_flex_preference"]

    # QB semantic synthesis: in SF, "QB depth is part of the lineup" and
    # "protect elite QB" can be two pieces of one roster-construction story.
    qb_format = next((c for c in candidates if c.get("story_id") == "format_qb_demand"), None)
    qb_elite = next((c for c in candidates if c.get("story_id") == "elite_then_depth:QB"), None)
    if qb_format is not None and qb_elite is not None:
        evf = qb_format.get("evidence", {}) or {}
        eve = qb_elite.get("evidence", {}) or {}
        fixed_qb = int(evf.get("fixed_qb_per_team", int(qb)))
        sf_qb = int(evf.get("sf_per_team", int(superflex)))
        eligible = fixed_qb + sf_qb
        frontier = evf.get("frontier", _frontier_rank("QB"))
        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        candidates = [
            c for c in candidates
            if c.get("story_id") not in {"format_qb_demand", "elite_then_depth:QB"}
        ]
        _add_story(
            "qb_roster_construction_synth", "roster_construction", "QB",
            4.75 + min(head_drop, 1.5) * 0.15,
            "QB requires both top-end access and starting depth here",
            (
                f"Each team can start a QB in {eligible} lineup slots, while historical replacement sits near QB{frontier}. "
                f"The QB1–QB{head_end} segment also loses {head_drop:.2f} WoRP. "
                "This format rewards securing a strong QB anchor without treating the second startable QB as mere bench insurance."
            ),
            1.45, 1.30, 1.55,
            {"qb_eligible_per_team": eligible, "frontier": frontier,
             "head_drop": head_drop, "head_end": head_end},
        )
        synth = [c for c in story_candidates if c.get("story_id") == "qb_roster_construction_synth"]
        candidates.extend(synth[-1:])

    # -------------------------------------------------------------------------
    # V0.8.0 INTERPOSITIONAL STORY SYNTHESIS
    # -------------------------------------------------------------------------
    # Detect whether RB has a coherent top+depth advantage over WR. We require
    # BOTH independent pieces of evidence:
    #   1) elite same-rank advantage (already generated by cross-position engine)
    #   2) material RB-vs-WR cross-rank equivalence inside the relevant pool.
    # This is synthesis, not a new WoRP calculation.
    elite_rbwr = next((
        c for c in candidates
        if c.get("story_id") in {"crosspos_elite_preference", "crosspos_elite_priority"}
        and c.get("position") == "RB"
    ), None)
    rbwr_equiv = next((
        c for c in candidates
        if c.get("story_id") == "crosspos_equivalence_rb_wr"
    ), None)

    if elite_rbwr is not None and rbwr_equiv is not None:
        eve = elite_rbwr.get("evidence", {}) or {}
        evq = rbwr_equiv.get("evidence", {}) or {}

        # V0.7.7 elite candidate fields may vary slightly; derive the displayed
        # elite advantage conservatively from evidence when available, otherwise
        # from the known detail text only as a last resort is NOT allowed.
        elite_adv = eve.get("advantage", eve.get("mean_gap", eve.get("worp_gap")))
        try:
            elite_adv = float(elite_adv) if elite_adv is not None else None
        except Exception:
            elite_adv = None

        rb_rank = int(evq.get("deeper_rank", 0) or 0)
        wr_rank = int(evq.get("shallower_rank", 0) or 0)
        rb_val = float(evq.get("worp_a", 0.0) or 0.0)
        wr_val = float(evq.get("worp_b", 0.0) or 0.0)
        rank_gap = int(evq.get("rank_gap", rb_rank - wr_rank) or 0)

        if rb_rank > 0 and wr_rank > 0 and rank_gap >= 6:
            # Do not spend separate cards on evidence that now belongs to the
            # synthesized RB roster-construction thesis.
            candidates = [
                c for c in candidates
                if c.get("story_id") not in {
                    "crosspos_elite_preference",
                    "crosspos_elite_priority",
                    "crosspos_equivalence_rb_wr",
                }
            ]

            elite_sentence = (
                f"Elite RB also carries about {elite_adv:.2f} more WoRP per player than elite WR. "
                if elite_adv is not None and elite_adv > 0
                else "Elite RB also leads elite WR on this league's historical curve. "
            )

            _add_story(
                "rb_top_and_depth_synth", "roster_construction", "RB",
                6.10 + min(rank_gap, 20) * 0.025,
                "Prioritize RB across both elite and FLEX decisions",
                (
                    elite_sentence +
                    f"RB{rb_rank} ({rb_val:.2f} WoRP) still carries roughly WR{wr_rank} ({wr_val:.2f} WoRP) value, "
                    f"so comparable historical value survives about {rank_gap} ranks deeper at RB. "
                    "In this league, RB has offered an advantage both at the top and through FLEX-relevant depth."
                ),
                1.75, 1.40, 1.70,
                {"elite_advantage": elite_adv, "rb_rank": rb_rank, "wr_rank": wr_rank,
                 "rb_worp": rb_val, "wr_worp": wr_val, "rank_gap": rank_gap,
                 "shared_slot": "FLEX"},
            )
            synth = [c for c in story_candidates if c.get("story_id") == "rb_top_and_depth_synth"]
            candidates.extend(synth[-1:])

            # Any other RB-led FLEX equivalence is now supporting evidence for
            # the same thesis unless it expresses a genuinely different slot
            # constraint. This removes RB~TE as a second card saying "RB survives
            # deeper" while preserving the evidence internally.
            candidates = [
                c for c in candidates
                if not (
                    c.get("family") == "cross_position_equivalence"
                    and c.get("position") == "RB"
                    and c.get("story_id") != "rb_top_and_depth_synth"
                )
            ]

    # Semantic family cap: even without a full synthesis, no more than one raw
    # cross-position-equivalence card may survive into the Top 5. Keep the most
    # decision-relevant one; other equivalences remain backoffice evidence.
    eqs = [c for c in candidates if c.get("family") == "cross_position_equivalence"]
    if len(eqs) > 1:
        best_eq = max(
            eqs,
            key=lambda c: (
                float(c.get("decision_relevance", 0.0) or 0.0),
                float(c.get("editorial_score", 0.0) or 0.0),
                float(c.get("score", 0.0) or 0.0),
            ),
        )
        candidates = [
            c for c in candidates
            if c.get("family") != "cross_position_equivalence" or c is best_eq
        ]

    # Rank by the explicit editorial dimensions first; score breaks close ties.
    for c in candidates:
        if "editorial_score" not in c:
            c["editorial_score"] = (
                c["materiality"] * 0.40 +
                c["confidence"] * 0.25 +
                c["actionability"] * 0.35
            )

    candidates = sorted(
        candidates,
        key=lambda c: (c["editorial_score"], c["score"]),
        reverse=True,
    )

    # -------------------------------------------------------------------------
    # V0.8.2 semantic editorial gate.
    # -------------------------------------------------------------------------
    published_ids_now = {c.get("story_id") for c in candidates}

    # One economic story = one card. If the RB synthesis already says RB wins at
    # the top AND through FLEX-relevant depth, the same-rank FLEX preference is
    # evidence for that story, not an additional recommendation.
    if "rb_top_and_depth_synth" in published_ids_now:
        candidates = [
            c for c in candidates
            if c.get("story_id") not in {
                "crosspos_flex_preference",
                "crosspos_elite_preference",
                "crosspos_elite_priority",
                "crosspos_equivalence_rb_wr",
            }
        ]

    # A raw statement that the lineup has several FLEX slots is useful evidence,
    # but not by itself a Top-5 economic story. Keep it in backoffice generation
    # and remove it from publication. The reserve below may promote an existing
    # curve/economic story instead; no new metric or claim is fabricated.
    candidates = [
        c for c in candidates
        if c.get("story_id") != "flex_depth_absorption"
    ]

    # -------------------------------------------------------------------------
    # V0.8.4 WR vertical synthesis.
    # -------------------------------------------------------------------------
    elite_wr = next((
        c for c in candidates
        if c.get("story_id") == "elite_then_depth:WR"
    ), None)
    cheap_wr = next((
        c for c in candidates
        if c.get("story_id") == "cheap_midrange:WR"
    ), None)

    if elite_wr is not None and cheap_wr is not None:
        eve = elite_wr.get("evidence", {}) or {}
        evm = cheap_wr.get("evidence", {}) or {}

        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", evm.get("frontier", 0)) or 0)
        mid_start = int(evm.get("start", 0) or 0)
        mid_end = int(evm.get("end", 0) or 0)
        cost10 = float(evm.get("cost_per_10", 0.0) or 0.0)

        if head_drop > 0 and mid_start > 0 and mid_end > mid_start:
            candidates = [
                c for c in candidates
                if c.get("story_id") not in {
                    "elite_then_depth:WR",
                    "cheap_midrange:WR",
                }
            ]

            _add_story(
                "wr_elite_and_midrange_synth", "roster_construction", "WR",
                6.00,
                "Pay for elite WR access; be selective in the middle",
                (
                    f"WR1 to WR{head_end} loses {head_drop:.2f} WoRP, so the top of the position has carried real historical separation. "
                    f"But between WR{mid_start} and WR{mid_end}, moving 10 ranks changes only about {cost10:.2f} WoRP. "
                    + (f"With replacement near WR{frontier}, " if frontier > 0 else "")
                    + "this league has rewarded securing elite WR access more than paying repeatedly for small mid-range upgrades."
                ),
                1.70, 1.40, 1.60,
                {
                    "head_drop": head_drop,
                    "head_end": head_end,
                    "mid_start": mid_start,
                    "mid_end": mid_end,
                    "cost_per_10": cost10,
                    "frontier": frontier,
                },
            )
            synth = [
                c for c in story_candidates
                if c.get("story_id") == "wr_elite_and_midrange_synth"
            ]
            candidates.extend(synth[-1:])

    # V0.8.1 editorial reserve.
    # Synthesis can correctly collapse two cards into one and leave only four.
    # When that happens, look only at stories the engine/editor already generated.
    # Do NOT backfill generic format facts or evidence that belongs to a published
    # synthesized thesis. The reserve is therefore conservative by construction.
    if len(candidates) < 5:
        published_ids = {c.get("story_id") for c in candidates}
        published_families = {(c.get("family"), c.get("position")) for c in candidates}
        has_qb_synth = "qb_roster_construction_synth" in published_ids
        has_rb_synth = "rb_top_and_depth_synth" in published_ids
        has_wr_synth = "wr_elite_and_midrange_synth" in published_ids

        blocked_ids = {
            "flex_depth_absorption",   # format fact without enough economic specificity
            "format_te_demand",       # format alone is evidence, not a Top-5 story
        }
        if has_qb_synth:
            blocked_ids.update({
                "format_qb_demand", "elite_then_depth:QB", "waiting_cost:QB"
            })
        if has_rb_synth:
            blocked_ids.update({
                "crosspos_elite_preference", "crosspos_elite_priority",
                "crosspos_equivalence_rb_wr", "crosspos_flex_preference",
                "elite_then_depth:RB",
            })
        if has_wr_synth:
            blocked_ids.update({
                "elite_then_depth:WR", "cheap_midrange:WR",
            })

        reserve = []
        for c in story_candidates:
            sid = c.get("story_id")
            if sid in published_ids or sid in blocked_ids:
                continue
            # A reserve card still has to clear a basic decision-quality floor.
            if float(c.get("materiality", 0.0) or 0.0) < 0.90:
                continue
            if float(c.get("confidence", 0.0) or 0.0) < 0.90:
                continue
            if float(c.get("actionability", 0.0) or 0.0) < 1.00:
                continue
            # Avoid spending a second card on the same family+position unless the
            # story itself is semantically different and no alternative survives.
            fam_pos = (c.get("family"), c.get("position"))
            if fam_pos in published_families:
                continue
            if "editorial_score" not in c:
                c["editorial_score"] = (
                    float(c.get("materiality", 0.0)) * 0.40 +
                    float(c.get("confidence", 0.0)) * 0.25 +
                    float(c.get("actionability", 0.0)) * 0.35
                )
            reserve.append(c)

        reserve = sorted(
            reserve,
            key=lambda c: (float(c.get("editorial_score", 0.0)), float(c.get("score", 0.0))),
            reverse=True,
        )
        for c in reserve:
            if len(candidates) >= 5:
                break
            candidates.append(c)
            published_ids.add(c.get("story_id"))
            published_families.add((c.get("family"), c.get("position")))

    # Exactly five remains the product target, but we still refuse to fabricate a
    # sixth-rate claim merely to fill space. The regression harness will expose
    # any league that still has fewer than five material, distinct stories.
    # V0.8.5 final publication gate.
    # Work on the actual visible five cards. If both WR evidence cards survived
    # every earlier editorial stage, merge them here into one roster-construction
    # story and fill the freed slot only with an already-generated distinct story.
    final_cards = list(candidates[:5])
    final_ids = {c.get("story_id") for c in final_cards}

    if {
        "elite_then_depth:WR",
        "cheap_midrange:WR",
    }.issubset(final_ids):
        elite_wr = next(c for c in final_cards if c.get("story_id") == "elite_then_depth:WR")
        cheap_wr = next(c for c in final_cards if c.get("story_id") == "cheap_midrange:WR")
        eve = elite_wr.get("evidence", {}) or {}
        evm = cheap_wr.get("evidence", {}) or {}

        head_drop = float(eve.get("head_drop", 0.0) or 0.0)
        head_end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", evm.get("frontier", 0)) or 0)
        mid_start = int(evm.get("start", 0) or 0)
        mid_end = int(evm.get("end", 0) or 0)
        cost10 = float(evm.get("cost_per_10", 0.0) or 0.0)

        if head_drop > 0 and mid_start > 0 and mid_end > mid_start:
            merged = {
                "story_id": "wr_elite_and_midrange_synth",
                "family": "roster_construction",
                "position": "WR",
                "score": 6.00,
                "materiality": 1.70,
                "confidence": 1.40,
                "actionability": 1.60,
                "editorial_score": 1.585,
                "title": "Pay for elite WR access; be selective in the middle",
                "detail": (
                    f"WR1 to WR{head_end} loses {head_drop:.2f} WoRP, so the top of the position has carried real historical separation. "
                    f"But between WR{mid_start} and WR{mid_end}, moving 10 ranks changes only about {cost10:.2f} WoRP. "
                    + (f"With replacement near WR{frontier}, " if frontier > 0 else "")
                    + "this league has rewarded securing elite WR access more than paying repeatedly for small mid-range upgrades."
                ),
                "evidence": {
                    "head_drop": head_drop,
                    "head_end": head_end,
                    "mid_start": mid_start,
                    "mid_end": mid_end,
                    "cost_per_10": cost10,
                    "frontier": frontier,
                },
            }

            # Preserve the earlier of the two WR cards as the position of the
            # synthesized story, remove both evidence cards, and keep ordering
            # stable for every other visible recommendation.
            first_idx = min(
                i for i, c in enumerate(final_cards)
                if c.get("story_id") in {"elite_then_depth:WR", "cheap_midrange:WR"}
            )
            final_cards = [
                c for c in final_cards
                if c.get("story_id") not in {"elite_then_depth:WR", "cheap_midrange:WR"}
            ]
            final_cards.insert(first_idx, merged)

            # Fill only from already-generated editorial candidates. Do not
            # reintroduce evidence absorbed by a synthesis or generic format facts.
            visible_ids = {c.get("story_id") for c in final_cards}
            blocked_ids = {
                "elite_then_depth:WR", "cheap_midrange:WR",
                "flex_depth_absorption", "format_te_demand",
            }
            if "rb_top_and_depth_synth" in visible_ids:
                blocked_ids.update({
                    "crosspos_elite_preference", "crosspos_elite_priority",
                    "crosspos_equivalence_rb_wr", "crosspos_flex_preference",
                    "elite_then_depth:RB",
                })
            if "qb_roster_construction_synth" in visible_ids:
                blocked_ids.update({
                    "format_qb_demand", "elite_then_depth:QB", "waiting_cost:QB",
                })

            reserve = []
            for c in list(candidates) + list(story_candidates):
                sid = c.get("story_id")
                if sid in visible_ids or sid in blocked_ids:
                    continue
                if float(c.get("materiality", 0.0) or 0.0) < 0.90:
                    continue
                if float(c.get("confidence", 0.0) or 0.0) < 0.90:
                    continue
                if float(c.get("actionability", 0.0) or 0.0) < 1.00:
                    continue
                if "editorial_score" not in c:
                    c["editorial_score"] = (
                        float(c.get("materiality", 0.0)) * 0.40 +
                        float(c.get("confidence", 0.0)) * 0.25 +
                        float(c.get("actionability", 0.0)) * 0.35
                    )
                reserve.append(c)

            reserve = sorted(
                reserve,
                key=lambda c: (float(c.get("editorial_score", 0.0)), float(c.get("score", 0.0))),
                reverse=True,
            )
            for c in reserve:
                if len(final_cards) >= 5:
                    break
                sid = c.get("story_id")
                if sid in visible_ids:
                    continue
                final_cards.append(c)
                visible_ids.add(sid)

    # -------------------------------------------------------------------------
    # V0.9.0 DECISION-THESIS EDITOR
    # -------------------------------------------------------------------------
    # The frontend publishes manager decisions, not independent metrics. Evidence
    # that points to the same positional roster-construction decision is absorbed
    # into one thesis before the final Top 5 is selected.
    pool = []
    seen = set()
    for c in list(final_cards) + list(candidates) + list(story_candidates):
        sid = c.get("story_id")
        if not sid or sid in seen:
            continue
        seen.add(sid)
        if float(c.get("materiality", 0.0) or 0.0) < 0.90:
            continue
        if float(c.get("confidence", 0.0) or 0.0) < 0.90:
            continue
        if float(c.get("actionability", 0.0) or 0.0) < 1.00:
            continue
        if sid in {"flex_depth_absorption", "format_te_demand"}:
            continue
        if "editorial_score" not in c:
            c["editorial_score"] = (
                float(c.get("materiality", 0.0)) * 0.40 +
                float(c.get("confidence", 0.0)) * 0.25 +
                float(c.get("actionability", 0.0)) * 0.35
            )
        pool.append(c)

    ids = {c.get("story_id") for c in pool}

    # Canonical theses already synthesized upstream absorb supporting evidence.
    absorbed = set()
    if "rb_top_and_depth_synth" in ids:
        absorbed.update({
            "crosspos_elite_preference", "crosspos_elite_priority",
            "crosspos_equivalence_rb_wr", "crosspos_flex_preference",
            "elite_then_depth:RB",
        })
        # RB-vs-TE equivalence is also supporting evidence for the same broad
        # RB depth thesis when RB is the leading side of that card.
        for c in pool:
            if (c.get("family") == "cross_position_equivalence"
                    and c.get("position") == "RB"):
                absorbed.add(c.get("story_id"))

    if "wr_elite_and_midrange_synth" in ids:
        absorbed.update({"elite_then_depth:WR", "cheap_midrange:WR"})

    # QB: if format demand and/or a prior QB synthesis exists, waiting-cost and
    # elite-depth QB facts support that same lineup-construction decision rather
    # than consuming additional cards.
    qb_anchor = None
    for preferred in ("qb_roster_construction_synth", "format_qb_demand"):
        qb_anchor = next((c for c in pool if c.get("story_id") == preferred), None)
        if qb_anchor is not None:
            break
    if qb_anchor is not None:
        # The format-demand card is evidence inside the canonical QB thesis.
        # V0.9.0 absorbed waiting/elite support but forgot this source card when
        # qb_roster_construction_synth already existed upstream.
        if qb_anchor.get("story_id") == "qb_roster_construction_synth":
            absorbed.add("format_qb_demand")
        qb_support = [
            c for c in pool
            if c.get("position") == "QB"
            and c.get("story_id") in {"waiting_cost:QB", "elite_then_depth:QB"}
        ]
        absorbed.update({c.get("story_id") for c in qb_support})
        if qb_anchor.get("story_id") == "format_qb_demand" and qb_support:
            support = max(qb_support, key=lambda c: float(c.get("editorial_score", 0.0) or 0.0))
            ev = support.get("evidence", {}) or {}
            start = int(ev.get("start", 0) or 0)
            end = int(ev.get("end", 0) or 0)
            drop = float(ev.get("drop", 0.0) or 0.0)
            base_detail = str(qb_anchor.get("detail", ""))
            extra = ""
            if start > 0 and end > start and drop > 0:
                extra = f" Historically, moving from QB{start} to QB{end} also gives up {drop:.2f} WoRP."
            qb_anchor = dict(qb_anchor)
            qb_anchor["story_id"] = "qb_roster_construction_synth"
            qb_anchor["family"] = "roster_construction"
            qb_anchor["title"] = "QB requires both starting depth and timely access here"
            qb_anchor["detail"] = base_detail + extra
            qb_anchor["materiality"] = max(float(qb_anchor.get("materiality", 0.0)), 1.45)
            qb_anchor["confidence"] = max(float(qb_anchor.get("confidence", 0.0)), 1.30)
            qb_anchor["actionability"] = max(float(qb_anchor.get("actionability", 0.0)), 1.55)
            qb_anchor["editorial_score"] = 1.448
            absorbed.add("format_qb_demand")
            pool.append(qb_anchor)

    # RB elite priority + elite-depth are the same decision even when the stronger
    # top+depth synthesis did not trigger.
    rb_elite = next((c for c in pool if c.get("story_id") == "crosspos_elite_priority" and c.get("position") == "RB"), None)
    rb_depth = next((c for c in pool if c.get("story_id") == "elite_then_depth:RB"), None)
    if rb_elite is not None and rb_depth is not None and "rb_top_and_depth_synth" not in ids:
        eve = rb_depth.get("evidence", {}) or {}
        head = float(eve.get("head_drop", 0.0) or 0.0)
        end = int(eve.get("head_end", 8) or 8)
        frontier = int(eve.get("frontier", 0) or 0)
        merged = dict(rb_elite)
        merged["story_id"] = "rb_elite_access_synth"
        merged["family"] = "roster_construction"
        merged["title"] = "Prioritize elite RB access"
        merged["detail"] = (
            str(rb_elite.get("detail", "")) +
            (f" RB1 to RB{end} also loses {head:.2f} WoRP" if head > 0 else "") +
            (f" before replacement near RB{frontier}." if frontier > 0 else ".")
        )
        merged["materiality"] = max(float(rb_elite.get("materiality", 0.0)), 1.50)
        merged["confidence"] = max(float(rb_elite.get("confidence", 0.0)), 1.30)
        merged["actionability"] = max(float(rb_elite.get("actionability", 0.0)), 1.55)
        merged["editorial_score"] = 1.475
        absorbed.update({"crosspos_elite_priority", "elite_then_depth:RB"})
        pool.append(merged)

    thesis_pool = [c for c in pool if c.get("story_id") not in absorbed]

    # One semantic thesis per story ID, strongest representation wins.
    best = {}
    for c in thesis_pool:
        sid = c.get("story_id")
        if sid not in best or float(c.get("editorial_score", 0.0)) > float(best[sid].get("editorial_score", 0.0)):
            best[sid] = c
    thesis_pool = list(best.values())

    # Rank after synthesis. Do not force positional diversity; five strongest
    # distinct manager decisions win.
    thesis_pool = sorted(
        thesis_pool,
        key=lambda c: (float(c.get("editorial_score", 0.0)), float(c.get("score", 0.0))),
        reverse=True,
    )

    structural_insights = thesis_pool[:5]

    # Backward-compatible frontend contract: downstream UI/session-state code
    # still consumes a DataFrame named insight_df. Story Engine V0.7.6 changed
    # candidate semantics, not the public return shape.
    insight_df = pd.DataFrame(structural_insights)

    audit = {
        "source": "Sleeper weekly stats",
        "seasons": list(seasons),
        "rows": (int(len(all_weeks)) if not all_weeks.empty else None),
        "replacement_band": 6,
        "engine_cache": {
            "version": ENGINE_CACHE_VERSION,
            "season_hits": {str(k): bool(v) for k, v in cache_hits.items()},
            "missing_seasons_computed": [int(x) for x in missing_seasons],
        },
        "n_sims": int(n_sims),
        "seed": int(seed),
        "endpoint_examples": {
            str(s): (urls[0] if urls else None)
            for s, urls in endpoint_log.items()
        },
        "timing": {
            "historical_input_seconds": round(t_after_load - t_calc0, 3),
            "engine_total_seconds": round(t_after_engine - t_after_load, 3),
            "engine_by_season_seconds": {str(season): round(sec, 3) for season, sec in engine_timings},
            "postprocess_seconds": round(time.perf_counter() - t_after_engine, 3),
            "total_seconds": round(time.perf_counter() - t_calc0, 3),
        },
    }

    return curve, player_summary, player_seasons, cliff_df, insight_df, audit


calc_key = (
    league.get("league_id"),
    selected_seasons,
    int(n_sims_ui),
)

if compute:
    with st.spinner(
        f"Calculating {window_label} WoRP from Sleeper weekly stats "
        "for this exact league…"
    ):
        try:
            scoring_json = json.dumps(
                league.get("scoring_settings", {}),
                sort_keys=True,
            )

            (
                curve,
                player_summary,
                player_seasons,
                cliff_df,
                insight_df,
                audit,
            ) = calculate_league_intelligence_cached(
                league.get("total_rosters", 0),
                counts.get("QB", 0),
                counts.get("RB", 0),
                counts.get("WR", 0),
                counts.get("TE", 0),
                counts.get("FLEX", 0),
                counts.get("SUPER_FLEX", 0),
                scoring_json,
                seasons=selected_seasons,
                n_sims=int(n_sims_ui),
            )

            st.session_state["worp_result_key"] = calc_key
            st.session_state["league_curve"] = curve
            st.session_state["league_player_summary"] = player_summary
            st.session_state["league_player_seasons"] = player_seasons
            st.session_state["league_cliffs"] = cliff_df
            st.session_state["league_insights"] = insight_df
            st.session_state["league_curve_audit"] = audit

        except Exception as e:
            st.error(f"League-specific WoRP calculation failed: {e}")

has_result = st.session_state.get("worp_result_key") == calc_key

if not has_result:
    st.info(
        "Choose the 3-year window and click Calculate. Results are cached for "
        "the same league, scoring, window and simulation count."
    )
else:
    curve = st.session_state["league_curve"].copy()
    player_summary = st.session_state["league_player_summary"].copy()
    player_seasons = st.session_state["league_player_seasons"].copy()
    cliff_df = st.session_state["league_cliffs"].copy()
    insight_df = st.session_state["league_insights"].copy()
    audit = st.session_state["league_curve_audit"]

    curve = curve[curve["position_rank"] <= int(top_n)].copy()

    # Product-level headline signals.
    rank1 = (
        curve[curve["position_rank"] == 1]
        .sort_values("three_year_worp_avg", ascending=False)
    )
    rank12 = (
        curve[curve["position_rank"] == 12]
        .sort_values("three_year_worp_avg", ascending=False)
    )

    signal_a, signal_b, signal_c, signal_d = st.columns(4)

    if not rank1.empty:
        top_row = rank1.iloc[0]
        signal_a.metric(
            "Highest Rank-1 WoRP",
            f"{top_row['position']}1 · {top_row['three_year_worp_avg']:.2f}",
        )
    else:
        signal_a.metric("Highest elite premium", "—")

    if not rank12.empty:
        depth_row = rank12.iloc[0]
        signal_b.metric(
            "Highest Pos12 WoRP",
            f"{depth_row['position']}12 · {depth_row['three_year_worp_avg']:.2f}",
        )
    else:
        signal_b.metric("Strongest depth at Pos12", "—")

    if not cliff_df.empty:
        biggest_cliff = cliff_df.sort_values("worp_drop", ascending=False).iloc[0]
        signal_c.metric(
            "Sharpest 5-rank drop",
            (
                f"{biggest_cliff['position']}"
                f"{int(biggest_cliff['cliff_start_rank'])}"
                f"→{int(biggest_cliff['cliff_end_rank'])} · "
                f"{biggest_cliff['worp_drop']:.2f}"
            ),
        )
    else:
        signal_c.metric("Sharpest 5-rank cliff", "—")

    signal_d.metric(
        "Historical window",
        window_label,
    )

    st.caption(
        "WoRP Lab measures what happened. It does not estimate what will happen. "
        "Player identity describes observed historical performance; positional "
        "rank describes historical structural value."
    )

    tab_curve, tab_players, tab_method = st.tabs(
        ["STRUCTURAL INSIGHTS", "PLAYER BOARD", "METHODOLOGY"]
    )

    with tab_curve:
        st.markdown("#### 3-Year Positional Value Curve")
        st.caption(
            f"{window_label} · concept-first aggregation. Example: QB1 = "
            f"QB1/{selected_seasons[0]} + QB1/{selected_seasons[1]} + "
            f"QB1/{selected_seasons[2]}, divided by 3. Player names do not "
            "enter the curve aggregation."
        )

        try:
            import altair as alt

            domain = ["QB", "RB", "WR", "TE"]
            colors = ["#ff4b4b", "#21c56e", "#3b82f6", "#f5b301"]

            legend_hide = alt.selection_point(
                fields=["position"],
                bind="legend",
                toggle=True,
                empty=False,
            )

            base = (
                alt.Chart(curve)
                .mark_line(
                    point=alt.OverlayMarkDef(size=38),
                    strokeWidth=2.5,
                )
                .encode(
                    x=alt.X(
                        "position_rank:Q",
                        title="Position Rank",
                        scale=alt.Scale(domain=[1, int(top_n)]),
                        axis=alt.Axis(
                            values=list(range(1, int(top_n) + 1, 2))
                        ),
                    ),
                    y=alt.Y(
                        "three_year_worp_avg:Q",
                        title="3-Year WoRP Avg",
                        scale=alt.Scale(zero=False),
                    ),
                    color=alt.Color(
                        "position:N",
                        title=None,
                        scale=alt.Scale(domain=domain, range=colors),
                        legend=alt.Legend(
                            orient="top",
                            direction="horizontal",
                            title="Click to hide · shift-click for multiple",
                        ),
                    ),
                    opacity=alt.condition(
                        legend_hide,
                        alt.value(0.0),
                        alt.value(1.0),
                    ),
                    tooltip=(
                        [
                            alt.Tooltip("concept:N", title="Concept"),
                        ]
                        + [
                            alt.Tooltip(
                                f"worp_{int(s)}:Q",
                                title=f"{int(s)}",
                                format=".3f",
                            )
                            for s in selected_seasons
                        ]
                        + [
                            alt.Tooltip(
                                "three_year_worp_avg:Q",
                                title="3Y Avg",
                                format=".3f",
                            ),
                        ]
                    ),
                )
                .add_params(legend_hide)
                .properties(height=520)
            )

            st.caption(
                "Tip: click a position in the legend to hide it. "
                "Shift-click hides multiple positions; click blank chart space to restore all lines."
            )
            st.altair_chart(base, width="stretch")

        except Exception as e:
            st.warning(f"Positional curve could not render: {e}")

        st.markdown("##### What this league is telling you")
        st.caption("Five historical, league-specific roster signals. Built to inform decisions — not project players.")

        if insight_df is not None and not insight_df.empty:
            for _, insight in insight_df.head(5).iterrows():
                st.markdown(f"**{insight['title']}**  \n{insight['detail']}")
        else:
            st.caption("No Structural Insights available for this curve.")

        st.markdown("##### Value Cliffs")
        st.caption("Where does waiting a few ranks cost the most WoRP? The five insights summarize; this table lets you inspect the marginal delta.")
        if cliff_df is not None and not cliff_df.empty:
            cliff_view = cliff_df.copy().sort_values("worp_drop", ascending=False)
            cliff_view["Range"] = cliff_view.apply(lambda r: f"{r['position']}{int(r['cliff_start_rank'])}–{r['position']}{int(r['cliff_end_rank'])}", axis=1)
            cliff_view["WoRP drop"] = cliff_view["worp_drop"].round(2)
            st.dataframe(
                cliff_view[["position", "Range", "WoRP drop"]].rename(columns={"position": "Position"}),
                hide_index=True,
                use_container_width=True,
            )

        _teams=int(league.get("total_rosters",0) or 0)
        _qb=int(counts.get("QB",0)); _rb=int(counts.get("RB",0)); _wr=int(counts.get("WR",0)); _te=int(counts.get("TE",0))
        _flex=int(counts.get("FLEX",0)); _superflex=int(counts.get("SUPER_FLEX",0)); _sc=league.get("scoring_settings",{}) or {}

        st.markdown("##### Lineup Economics")
        st.caption("How much of this league's expected starting-lineup scoring comes from each slot — and which positions fill flexible slots.")
        try:
            _pw,_ = load_sleeper_player_weeks([2023,2024,2025], _sc, player_map=fetch_player_map())
            lineup_rows=build_lineup_scoring_share(_pw,_teams,_qb,_rb,_wr,_te,_flex,_superflex)
            cards=[]
            for lr in lineup_rows:
                occ=lr['occupancy']
                is_flexible=lr['slot'].startswith('FLEX') or lr['slot'].startswith('SUPER_FLEX')
                mix=(''.join(f'<span>{p} {100*v:.0f}%</span>' for p,v in sorted(occ.items(),key=lambda kv:kv[1],reverse=True)) if is_flexible else '')
                cards.append(
                    f'<div class="ls-card"><div class="ls-slot">{lr["slot"]}</div>'
                    f'<div class="ls-share">{100*lr["lineup_share"]:.1f}%</div>'
                    f'<div class="ls-label">of expected lineup scoring</div>'
                    f'<div class="ls-pts">{lr["points_week"]:.1f} pts/week</div>'
                    f'<div class="ls-mix">{mix}</div></div>'
                )
            st.markdown("""<style>
            .ls-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:8px 0 16px 0}
            .ls-card{border:1px solid rgba(128,128,128,.35);border-radius:14px;padding:16px 14px;text-align:center;min-height:164px;background:rgba(128,128,128,.04)}
            .ls-slot{font-weight:700;font-size:15px;margin-bottom:10px}.ls-share{font-weight:800;font-size:34px;line-height:1.05}.ls-label{font-size:11px;opacity:.62;margin-top:4px}.ls-pts{font-size:16px;margin:10px 0 8px}.ls-mix{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;font-size:12px;opacity:.72;line-height:1.45;min-height:18px}
            </style>""",unsafe_allow_html=True)
            st.markdown('<div class="ls-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
            st.caption("Historical 2023–25 average under this league's exact Sleeper scoring. Share is fantasy-point contribution to the expected starting lineup; flexible-slot mix is modeled positional occupancy. WoRP is not used in this panel.")
        except Exception as exc:
            st.caption(f"Lineup Economics unavailable: {exc}")

        # Frozen V0.32 presentation. Universal derived-format support remains
        # the next task after V0.9.4 visual validation.
        st.markdown("##### Roster Construction")
        st.caption("League-native Scoring Core ranges. Use these as construction envelopes, not exact quotas or player rankings.")
        try:
            rc=pd.read_csv("worp_roster_construction_product_ranges_v0_32.csv")
            start_n=_qb+_rb+_wr+_te+_flex+_superflex
            tep=float(_sc.get("bonus_rec_te",0.0))>0
            fmt_key=(f"{_teams}T "+("SF " if _superflex>0 else "1QB ")
                     +f"Start{start_n} QB{_qb} RB{_rb} WR{_wr} TE{_te} "
                     +f"FLEX{_flex} SFLEX{_superflex}"+(" TEP" if tep else ""))
            hit=rc[rc["format_key"]==fmt_key]
            if hit.empty:
                st.caption("Roster Construction: exact format not yet supported by the frozen empirical envelope. No nearest-format substitution is made.")
            else:
                r=hit.iloc[0]
                st.markdown(
                    f"**Scoring Core: {int(r['scoring_core_low'])}–{int(r['scoring_core_high'])}**  \n"
                    f"QB {int(r['QB_low'])}–{int(r['QB_high'])} · RB {int(r['RB_low'])}–{int(r['RB_high'])} · "
                    f"WR {int(r['WR_low'])}–{int(r['WR_high'])} · TE {int(r['TE_low'])}–{int(r['TE_high'])}"
                )
                st.caption("Independent positional lows/highs are decision-equivalent constraints, not additive quotas. Once meaningful Scoring capacity is satisfied, remaining roster capacity belongs to Non-Scoring optionality.")
        except Exception as exc:
            st.caption(f"Roster Construction unavailable: {exc}")

    with tab_players:
        st.markdown("#### Player board")
        st.caption(
            "Player-specific average WoRP across the selected 3-year window. "
            "Use Seasons to distinguish established samples from rookies or "
            "shorter historical samples."
        )

        filter_a, filter_b, filter_c = st.columns([1, 1, 2])

        with filter_a:
            pos_filter = st.selectbox(
                "Position",
                ["ALL", "QB", "RB", "WR", "TE"],
                key="player_board_position",
            )

        with filter_b:
            min_seasons = st.selectbox(
                "Minimum seasons",
                [1, 2, 3],
                index=0,
                help=(
                    "Sample-size filter only. A player does not need three "
                    "seasons to appear because this board reports observed "
                    "results, not a forward projection."
                ),
            )

        with filter_c:
            player_search = st.text_input(
                "Find player",
                placeholder="e.g. Josh Allen, Trey McBride",
            )

        board = player_summary.copy()
        board = board[board["seasons"] >= int(min_seasons)]

        if pos_filter != "ALL":
            board = board[board["position"] == pos_filter]

        if player_search.strip():
            board = board[
                board["player_name"]
                .str.contains(player_search.strip(), case=False, na=False)
            ]

        board = board.sort_values(
            ["three_year_worp_avg", "seasons"],
            ascending=[False, False],
        ).reset_index(drop=True)

        board.insert(0, "board_rank", range(1, len(board) + 1))

        display_cols = [
            "board_rank", "position", "player_name",
            "three_year_worp_avg", "seasons",
            "avg_position_rank", "best_position_rank",
            "latest_worp", "latest_position_rank",
        ]
        optional_map = [
            ("avg_worp_per_game", "avg_worp_per_game"),
            ("avg_porp", "avg_porp"),
            ("games", "games"),
        ]
        for col, _ in optional_map:
            if col in board.columns:
                display_cols.append(col)

        board_view = board[display_cols].rename(columns={
            "board_rank": "#",
            "position": "Pos",
            "player_name": "Player",
            "three_year_worp_avg": "Window Avg WoRP",
            "seasons": "Seasons",
            "avg_position_rank": "Avg Pos Rank",
            "best_position_rank": "Best Pos Rank",
            "latest_worp": f"{max(selected_seasons)} WoRP",
            "latest_position_rank": f"{max(selected_seasons)} Pos Rank",
            "avg_worp_per_game": "Avg WoRP/G",
            "avg_porp": "Avg PORP",
            "games": "Games",
        }).copy()

        for col in ["Window Avg WoRP", "Avg Pos Rank", f"{max(selected_seasons)} WoRP", "Avg WoRP/G", "Avg PORP"]:
            if col in board_view.columns:
                board_view[col] = board_view[col].round(3)

        st.dataframe(
            board_view.head(150),
            hide_index=True,
            width="stretch",
            height=520,
        )

        if not board.empty:
            st.markdown("##### Player explorer")
            player_options = (
                board["player_name"]
                .drop_duplicates()
                .tolist()
            )
            selected_player = st.selectbox(
                "Player",
                player_options,
                key="player_explorer",
            )

            ps = player_seasons[
                player_seasons["player_name"] == selected_player
            ].sort_values("season").copy()

            if not ps.empty:
                pos = ps.iloc[-1]["position"]
                p1, p2, p3, p4 = st.columns(4)

                p1.metric(
                    "Window Avg WoRP",
                    f"{ps['worp'].mean():.3f}",
                )
                p2.metric(
                    "Best season",
                    f"{ps['worp'].max():.3f}",
                )
                p3.metric(
                    "Best Pos Rank",
                    f"{int(ps['position_rank'].min())}",
                )
                p4.metric(
                    "Position",
                    pos,
                )

                season_cols = [
                    "season", "position", "position_rank", "worp"
                ]
                for optional in ["games", "porp", "worp_per_game"]:
                    if optional in ps.columns:
                        season_cols.append(optional)

                ps_view = ps[season_cols].rename(columns={
                    "season": "Season",
                    "position": "Pos",
                    "position_rank": "Pos Rank",
                    "worp": "WoRP",
                    "games": "Games",
                    "porp": "PORP",
                    "worp_per_game": "WoRP/G",
                }).copy()

                for col in ["WoRP", "PORP", "WoRP/G"]:
                    if col in ps_view.columns:
                        ps_view[col] = ps_view[col].round(3)

                st.dataframe(
                    ps_view,
                    hide_index=True,
                    width="stretch",
                )

                try:
                    import altair as alt

                    player_chart = (
                        alt.Chart(ps)
                        .mark_line(point=True, strokeWidth=3)
                        .encode(
                            x=alt.X(
                                "season:O",
                                title="Season",
                            ),
                            y=alt.Y(
                                "worp:Q",
                                title="Season WoRP",
                                scale=alt.Scale(zero=False),
                            ),
                            tooltip=[
                                alt.Tooltip("season:O", title="Season"),
                                alt.Tooltip("position_rank:Q", title="Pos Rank"),
                                alt.Tooltip("worp:Q", title="WoRP", format=".3f"),
                            ],
                        )
                        .properties(height=280)
                    )
                    st.altair_chart(player_chart, width="stretch")
                except Exception:
                    pass

    with tab_method:
        st.markdown("#### What this view means")
        st.write(
            "**WoRP is descriptive, not predictive.** It estimates how many "
            "fantasy matchup wins were added compared with replacement in the "
            "observed historical sample."
        )
        st.write(
            "**The positional curve is concept-first.** QB1 for a three-year "
            "window is the average of that season's QB1 WoRP in each of the "
            "three seasons — regardless of which player occupied QB1."
        )
        st.write(
            "**Replacement level** is derived from the number and type of "
            "starters your format requires, rather than from one universal "
            "positional rank."
        )
        st.write(
            "**3-Year Positional Value Curve** ranks players within position in each "
            "season, then averages the WoRP attached to each positional rank. "
            "It describes the positional historical positional shape, not a single player's "
            "three-year career value."
        )
        st.write(
            "**Player Board** averages each player's season WoRP over the "
            "seasons in which that player appears. Always read it together "
            "with the Seasons column."
        )
        st.write(
            "**Structural insights** are deterministic summaries derived from "
            "the positional curve (elite concentration, depth, cliffs, positive-value "
            "depth and flatness). They do not change WoRP and they do not project future performance."
        )
        st.write(
            "**Interactive legend focus** is visual only. Clicking a position "
            "does not recalculate or filter the underlying WoRP values."
        )
        st.info(
            "The WoRP Engine V0.2.1 mathematics are unchanged. V0.7.1 changes "
            "only the product/presentation layer around the validated "
            "Sleeper-native input."
        )

        with st.expander("Calculation audit"):
            st.write("Data source:", audit.get("source"))
            st.write("League ID:", league.get("league_id"))
            st.write("Lineup:", league.get("roster_positions", []))
            st.write(
                "Sleeper scoring settings:",
                league.get("scoring_settings", {}),
            )
            st.write("Seasons:", audit.get("seasons"))
            st.write("Weekly offensive rows:", audit.get("rows"))
            st.write("Replacement band:", audit.get("replacement_band"))
            st.write(
                "Monte Carlo:",
                f"{audit.get('n_sims')} sims / season · seed {audit.get('seed')}",
            )

st.markdown("### Rosters detected")
st.dataframe(roster_df, hide_index=True, width="stretch")

st.caption(
    "WoRP Lab UI V0.9.4.1 · Sleeper-native scoring · Engine V0.2.1 frozen."
)
