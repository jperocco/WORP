from pathlib import Path
import json
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
        headers={"User-Agent": "WoRP-Lab/0.6"}
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
st.caption("USER → LEAGUE → GRAPH · Engine V0.2.1 frozen · UI V0.6.1")

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
    st.info("V0.6.1: historical positional concepts + observed player results. No projections.")
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
        [4000, 8000],
        index=1,
        help="8,000 is the validated control setting.",
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

@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    seasons=(2023, 2024, 2025), n_sims=8000, seed=7
):
    from worp_engine import LeagueSettings, calculate_season_worp

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

    player_map = fetch_player_map()
    all_weeks, endpoint_log = load_sleeper_player_weeks(
        seasons=seasons,
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)

    rankings = {}

    for season_i in seasons:
        season_df = all_weeks[all_weeks["season"] == int(season_i)].copy()

        weekly, ranking = calculate_season_worp(
            season_df,
            settings,
            replacement_band=6,
            n_sims=int(n_sims),
            seed=int(seed),
        )

        ranking = ranking.copy()
        ranking["season"] = int(season_i)
        ranking["position_rank"] = (
            ranking.groupby("position")["worp"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
        rankings[int(season_i)] = ranking

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

    audit = {
        "source": "Sleeper weekly stats",
        "seasons": list(seasons),
        "rows": int(len(all_weeks)),
        "replacement_band": 6,
        "n_sims": int(n_sims),
        "seed": int(seed),
        "endpoint_examples": {
            str(s): (urls[0] if urls else None)
            for s, urls in endpoint_log.items()
        },
    }

    return curve, player_summary, player_seasons, cliff_df, audit


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
        ["POSITIONAL CURVE", "PLAYER BOARD", "METHODOLOGY"]
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
                        ),
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
                .properties(height=520)
            )

            st.altair_chart(base, width="stretch")

        except Exception as e:
            st.warning(f"Positional curve could not render: {e}")

        st.markdown("##### Value cliffs")
        st.caption(
            "Descriptive signal: largest decline in average WoRP across the "
            "next five positional ranks. It is not a new engine metric."
        )

        if not cliff_df.empty:
            cliff_view = cliff_df.rename(columns={
                "position": "Pos",
                "cliff_start_rank": "From",
                "cliff_end_rank": "To",
                "worp_drop": "WoRP Drop",
                "start_worp": "Start WoRP",
            }).copy()
            cliff_view["WoRP Drop"] = cliff_view["WoRP Drop"].round(3)
            cliff_view["Start WoRP"] = cliff_view["Start WoRP"].round(3)
            st.dataframe(
                cliff_view[["Pos", "From", "To", "Start WoRP", "WoRP Drop"]],
                hide_index=True,
                width="stretch",
            )

        checkpoint_ranks = [r for r in [1, 5, 10, 20, 30, 40, 50] if r <= int(top_n)]
        snapshot = curve[curve["position_rank"].isin(checkpoint_ranks)].copy()

        if not snapshot.empty:
            pivot = snapshot.pivot(
                index="position_rank",
                columns="position",
                values="three_year_worp_avg",
            ).reset_index()
            pivot = pivot.rename(columns={"position_rank": "Pos Rank"})
            for col in ["QB", "RB", "WR", "TE"]:
                if col in pivot.columns:
                    pivot[col] = pivot[col].round(3)

            st.markdown("##### Curve checkpoints")
            st.dataframe(pivot, hide_index=True, width="stretch")

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
        st.info(
            "The WoRP Engine V0.2.1 mathematics are unchanged. V0.6 changes "
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
    "WoRP Lab UI V0.6.1 · Sleeper-native scoring · Engine V0.2.1 frozen."
)
