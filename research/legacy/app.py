from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="WoRP Lab", page_icon="🏈", layout="wide")

DATA_CANDIDATES = [
    Path("worp_2016_2025_normalized.csv"),
    Path("worp_2016_2025_rankings.csv"),
]

@st.cache_data
def load_data():
    for path in DATA_CANDIDATES:
        if path.exists():
            df = pd.read_csv(path)
            if "worp_per_game" not in df.columns:
                df["worp_per_game"] = df["worp"] / df["games"]
            if "porp_per_game" not in df.columns and "porp" in df.columns:
                df["porp_per_game"] = df["porp"] / df["games"]
            if "worp_17g_pace" not in df.columns:
                df["worp_17g_pace"] = df["worp_per_game"] * 17
            return df, path.name
    return None, None

df, source = load_data()

st.title("WoRP Lab")
st.caption("Wins Over Replacement Player · Engine V0.2.1 frozen")

if df is None:
    st.error("Data file not found.")
    st.markdown("""
Put this app in the same folder as either:

- `worp_2016_2025_normalized.csv` **preferred**
- `worp_2016_2025_rankings.csv`

Then reload the page.
""")
    st.stop()

with st.sidebar:
    st.header("League format")
    st.write("**12 teams · SF · 2TE · TEP**")
    st.caption("1QB · 2RB · 3WR · 2TE · 2FLEX · 1SF")
    st.write("0.5 PPR · +1.0 TE Premium")
    st.write("Replacement band: **6**")
    st.divider()
    st.caption(f"Data: {source}")
    st.caption("Historical window: 2016–2025")

tab_leader, tab_player, tab_format, tab_method = st.tabs(
    ["LEADERBOARD", "PLAYER", "FORMAT", "METHODOLOGY"]
)

with tab_leader:
    c1, c2, c3, c4 = st.columns([1.3, 1.2, 1.2, 1.2])
    with c1:
        view = st.radio("Value view", ["TOTAL", "PER GAME"], horizontal=True)
    with c2:
        pos = st.selectbox("Position", ["ALL", "QB", "RB", "WR", "TE"])
    with c3:
        season_mode = st.selectbox("Season", ["ALL-TIME"] + [str(y) for y in sorted(df["season"].unique(), reverse=True)])
    with c4:
        min_games = st.number_input(
            "Min games",
            min_value=1,
            max_value=17,
            value=12 if view == "PER GAME" and season_mode == "ALL-TIME" else 1,
            step=1,
        )

    board = df.copy()
    if pos != "ALL":
        board = board[board["position"] == pos]
    if season_mode != "ALL-TIME":
        board = board[board["season"] == int(season_mode)]
    board = board[board["games"] >= min_games]

    metric = "worp" if view == "TOTAL" else "worp_per_game"
    board = board.sort_values(metric, ascending=False).copy()
    board.insert(0, "Rank", range(1, len(board) + 1))

    st.subheader("Historical Leaderboard" if season_mode == "ALL-TIME" else f"{season_mode} Leaderboard")
    if view == "TOTAL":
        st.caption("TOTAL measures season value, including availability.")
    else:
        st.caption("PER GAME measures weekly dominance. Historical default: minimum 12 games.")

    show_cols = ["Rank", "player_name", "season", "position", "games", "worp", "worp_per_game"]
    if "porp" in board.columns:
        show_cols.append("porp")
    if "worp_17g_pace" in board.columns:
        show_cols.append("worp_17g_pace")

    rename = {
        "player_name": "Player",
        "season": "Season",
        "position": "Pos",
        "games": "G",
        "worp": "WoRP",
        "worp_per_game": "WoRP/G",
        "porp": "PORP",
        "worp_17g_pace": "17G Pace",
    }

    st.dataframe(
        board[show_cols].rename(columns=rename).head(100),
        hide_index=True,
        use_container_width=True,
        column_config={
            "WoRP": st.column_config.NumberColumn(format="%.3f"),
            "WoRP/G": st.column_config.NumberColumn(format="%.3f"),
            "PORP": st.column_config.NumberColumn(format="%.1f"),
            "17G Pace": st.column_config.NumberColumn(format="%.3f"),
        },
    )
    st.caption(f"{len(board):,} qualifying player-seasons · showing top 100")

with tab_player:
    names = sorted(df["player_name"].dropna().unique())
    player = st.selectbox("Player", names, index=names.index("Trey McBride") if "Trey McBride" in names else 0)
    p = df[df["player_name"] == player].sort_values("season", ascending=False)

    if p.empty:
        st.info("No seasons found.")
    else:
        season = st.selectbox("Season", p["season"].astype(int).tolist())
        row = p[p["season"] == season].iloc[0]

        st.subheader(f"{player} · {int(season)}")
        a, b, c, d = st.columns(4)
        a.metric("WoRP", f"{row['worp']:.3f}")
        b.metric("WoRP / Game", f"{row['worp_per_game']:.3f}")
        c.metric("Games", f"{int(row['games'])}")
        d.metric("17G Pace", f"{row['worp_17g_pace']:.3f}")

        a, b, c, d = st.columns(4)
        if "porp" in row.index:
            a.metric("PORP", f"{row['porp']:.1f}")
        if "porp_per_game" in row.index:
            b.metric("PORP / Game", f"{row['porp_per_game']:.1f}")
        if "avg_replacement_points" in row.index:
            c.metric("Avg Replacement Pts", f"{row['avg_replacement_points']:.2f}")
        repl_rank = "avg_replacement_effective_rank" if "avg_replacement_effective_rank" in row.index else "avg_replacement_rank"
        if repl_rank in row.index:
            d.metric("Avg Replacement Rank", f"{row[repl_rank]:.1f}")

        st.markdown("#### Career / historical seasons")
        cols = [c for c in ["season", "position", "games", "worp", "worp_per_game", "porp", "worp_17g_pace"] if c in p.columns]
        st.dataframe(
            p[cols].rename(columns={
                "season":"Season","position":"Pos","games":"G","worp":"WoRP",
                "worp_per_game":"WoRP/G","porp":"PORP","worp_17g_pace":"17G Pace"
            }),
            hide_index=True,
            use_container_width=True,
        )
        st.info("Weekly breakdown enters in UI V0.2 after we wire the validated weekly historical file.")

with tab_format:
    st.subheader("Official validated reference format")
    st.markdown("""
| Setting | Value |
|---|---:|
| Teams | 12 |
| QB | 1 |
| RB | 2 |
| WR | 3 |
| TE | 2 |
| FLEX | 2 |
| Superflex | 1 |
| PPR | 0.5 |
| TE Premium | +1.0 |
| Replacement band | 6 |
| Simulations | 8,000 |
| Seed | 7 |
""")
    st.info("V0.1 is intentionally read-only. Custom format calculation comes after the frozen historical UI is validated.")

with tab_method:
    st.subheader("What is WoRP?")
    st.write(
        "WoRP estimates how many fantasy matchup wins a player added compared with "
        "a replacement-level player in the league format."
    )
    st.markdown("""
**Model chain**

`League Format → Weekly Scoring → Aggregate Starter Allocation → Dynamic Replacement → PORP → Empirical Simulation → Weekly WoRP → Season WoRP`

**TOTAL** is the canonical season-value metric and includes availability.

**PER GAME** measures weekly dominance. Historical leaderboards default to a 12-game minimum.

**17G Pace** is display-only and is never fed back into the engine.

Replacement is format-derived: it is based on the starter pool and the next six players at each position, rather than a universal fixed positional rank.

The current engine uses an **ex-post optimal aggregate starter pool**. It models league-wide scarcity; it does not reconstruct actual historical fantasy rosters or manager lineup decisions.
""")
    st.caption("Engine V0.2.1 · validated 2016–2025 · frozen")
