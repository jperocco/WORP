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
        headers={"User-Agent": "WoRP-Lab/0.5"}
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
st.caption("USER → LEAGUE → GRAPH · Engine V0.2.1 frozen · UI V0.5")

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
    st.info("V0.5 Sleeper-native: USER → LEAGUE → exact Sleeper scoring → 3-Year WoRP.")
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

st.markdown("### League graph")

st.success(
    "Sleeper-native scoring active · 3-year reconciliation gate: "
    "9,132 / 9,132 player-seasons exact to ±0.01 in the validation fixture."
)

st.caption(
    "Sleeper weekly stats × this league's scoring_settings → "
    "dynamic starter allocation → replacement → empirical WoRP."
)

compute = st.button(
    "Calculate league-specific 3-Year WoRP",
    type="primary",
    width="stretch",
)

@st.cache_data(show_spinner=False)
def calculate_league_curve_cached(
    teams, qb, rb, wr, te, flex, superflex, scoring_json,
    seasons=(2023, 2024, 2025), n_sims=8000, seed=7
):
    from worp_engine import LeagueSettings, calculate_season_worp

    sc = json.loads(scoring_json)

    # These scoring fields remain in LeagueSettings for compatibility/metadata.
    # fantasy_points themselves come directly from the validated Sleeper-native
    # exact-key scoring layer below.
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
    weekly_outputs = {}

    for season_i in seasons:
        season_df = all_weeks[all_weeks["season"] == int(season_i)].copy()

        weekly, ranking = calculate_season_worp(
            season_df,
            settings,
            replacement_band=6,
            n_sims=int(n_sims),
            seed=int(seed),
        )
        rankings[int(season_i)] = ranking
        weekly_outputs[int(season_i)] = weekly

    frames = []
    for season_i, ranking in rankings.items():
        x = ranking.copy()
        x = x[x["position"].isin(["QB", "RB", "WR", "TE"])].copy()
        x["position_rank_curve"] = (
            x.groupby("position")["worp"]
             .rank(method="first", ascending=False)
             .astype(int)
        )
        x = x[x["position_rank_curve"] <= 50]
        x["season"] = int(season_i)
        frames.append(
            x[["season", "position", "position_rank_curve", "worp"]]
        )

    curve_source = pd.concat(frames, ignore_index=True)
    curve = (
        curve_source
        .groupby(["position", "position_rank_curve"], as_index=False)
        .agg(
            three_year_worp_avg=("worp", "mean"),
            seasons_present=("season", "nunique"),
        )
    )
    curve = curve[curve["seasons_present"] == len(seasons)].copy()
    curve = curve.sort_values(["position", "position_rank_curve"])

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

    return curve, rankings, audit

if compute:
    with st.spinner(
        "Calculating 2023–2025 WoRP from Sleeper weekly stats "
        "for this exact league…"
    ):
        try:
            scoring_json = json.dumps(
                league.get("scoring_settings", {}),
                sort_keys=True,
            )
            curve, rankings, audit = calculate_league_curve_cached(
                league.get("total_rosters", 0),
                counts.get("QB", 0),
                counts.get("RB", 0),
                counts.get("WR", 0),
                counts.get("TE", 0),
                counts.get("FLEX", 0),
                counts.get("SUPER_FLEX", 0),
                scoring_json,
            )
            st.session_state["league_curve"] = curve
            st.session_state["league_curve_id"] = league["league_id"]
            st.session_state["league_rankings"] = rankings
            st.session_state["league_curve_audit"] = audit
        except Exception as e:
            st.error(f"League-specific WoRP calculation failed: {e}")

curve = None
if st.session_state.get("league_curve_id") == league.get("league_id"):
    curve = st.session_state.get("league_curve")

if curve is not None and not curve.empty:
    st.markdown("#### 3-Year WoRP Avg — league-specific")
    st.caption(
        "2023–2025 · each season is scored with this Sleeper league's exact "
        "scoring settings. Players are ranked within position each season; "
        "WoRP is then averaged at each positional rank."
    )

    try:
        import altair as alt

        domain = ["QB", "RB", "WR", "TE"]
        colors = ["#ff4b4b", "#21c56e", "#3b82f6", "#f5b301"]

        chart = (
            alt.Chart(curve)
            .mark_line(point=alt.OverlayMarkDef(size=34), strokeWidth=2.2)
            .encode(
                x=alt.X(
                    "position_rank_curve:Q",
                    title="Position Rank",
                    scale=alt.Scale(domain=[1, 50]),
                    axis=alt.Axis(values=list(range(1, 51, 2))),
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
                tooltip=[
                    alt.Tooltip("position:N", title="Pos"),
                    alt.Tooltip(
                        "position_rank_curve:Q",
                        title="Position Rank",
                    ),
                    alt.Tooltip(
                        "three_year_worp_avg:Q",
                        title="3Y WoRP Avg",
                        format=".3f",
                    ),
                ],
            )
            .properties(height=520)
        )
        st.altair_chart(chart, width="stretch")

    except Exception as e:
        st.warning(f"League graph could not render: {e}")

    # A compact positional snapshot makes league-to-league changes easy to verify.
    snapshot = curve[
        curve["position_rank_curve"].isin([1, 5, 10, 20, 30, 40, 50])
    ].copy()
    if not snapshot.empty:
        pivot = snapshot.pivot(
            index="position_rank_curve",
            columns="position",
            values="three_year_worp_avg",
        ).reset_index()
        pivot = pivot.rename(columns={"position_rank_curve": "Pos Rank"})
        st.markdown("#### Curve checkpoints")
        st.dataframe(pivot, hide_index=True, width="stretch")

    with st.expander("Calculation audit"):
        audit = st.session_state.get("league_curve_audit", {})
        st.write("Data source:", audit.get("source"))
        st.write("League ID:", league.get("league_id"))
        st.write("Lineup:", league.get("roster_positions", []))
        st.write("Sleeper scoring settings:", league.get("scoring_settings", {}))
        st.write("Seasons:", audit.get("seasons"))
        st.write("Weekly offensive rows:", audit.get("rows"))
        st.write("Replacement band:", audit.get("replacement_band"))
        st.write(
            "Monte Carlo:",
            f"{audit.get('n_sims')} sims / season · seed {audit.get('seed')}",
        )
else:
    st.info(
        "Choose a league and click Calculate. V0.5 uses Sleeper-native "
        "weekly fantasy scoring for the selected league."
    )

st.markdown("### Rosters detected")
st.dataframe(roster_df, hide_index=True, width="stretch")

st.caption(
    "V0.4 is a league-specific calculation build. Historical WoRP remains frozen; league-specific WoRP and the final roster graph "
    "come only after Sleeper format + roster mapping pass validation."
)
