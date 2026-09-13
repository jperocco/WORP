from pathlib import Path
import json
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WoRP Lab", page_icon="🏈", layout="wide")

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
        headers={"User-Agent": "WoRP-Lab/0.2"}
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

history, history_source = load_history()

st.title("WoRP Lab")
st.caption("USER → LEAGUE → GRAPH · Engine V0.2.1 frozen · UI V0.2")

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
    st.info("V0.2 integration gate: USER → LEAGUES → LEAGUE FORMAT → ROSTERS. WoRP roster calculations are not enabled until this data path is validated.")
    st.stop()

st.success(f"Connected: {user.get('display_name') or user.get('username')}  ·  @{user.get('username')}")

if not leagues:
    st.warning(f"No NFL leagues found for {season}.")
    st.stop()

league_map = {f"{x.get('name','Unnamed league')}  —  {league_format_label(x)}": x for x in leagues}
choice = st.selectbox("League", list(league_map.keys()))
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
st.info(
    "Sleeper connection is live. The next gate maps Sleeper player IDs to the WoRP player universe "
    "and computes WoRP under this league's detected scoring/lineup settings. Until that mapping is validated, "
    "this build deliberately does not invent roster WoRP values."
)

st.markdown("### Rosters detected")
st.dataframe(roster_df, hide_index=True, width="stretch")

st.caption(
    "V0.2 is an integration build. Historical WoRP remains frozen; league-specific WoRP and the final roster graph "
    "come only after Sleeper format + roster mapping pass validation."
)
