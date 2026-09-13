from pathlib import Path

SRC = Path("app_v0_7_1.py")
DST = Path("app_v0_7_2.py")

if not SRC.exists():
    raise SystemExit("STOP: app_v0_7_1.py not found")

s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.7.1', 'UI V0.7.2')
s = s.replace('WoRP-Lab/0.7.1', 'WoRP-Lab/0.7.2')
s = s.replace(
    'V0.7.1: five league-specific Structural Insights. Clean, actionable, historical.',
    'V0.7.2: five league-specific Structural Insights + faster default compute path.'
)
s = s.replace(
    'WoRP Lab UI V0.7.1 · Five actionable Structural Insights · Sleeper-native scoring · Engine V0.2.1 frozen.',
    'WoRP Lab UI V0.7.2 · Fast default compute · Five actionable Structural Insights · Engine V0.2.1 frozen.'
)

old_mc = '''    n_sims_ui = st.selectbox(
        "Monte Carlo",
        [4000, 8000],
        index=1,
        help="8,000 is the validated control setting.",
    )'''
new_mc = '''    n_sims_ui = st.selectbox(
        "Monte Carlo",
        [2000, 4000, 8000],
        index=1,
        format_func=lambda x: {2000: "2,000 · Fast preview", 4000: "4,000 · Standard", 8000: "8,000 · Validated control"}[x],
        help="4,000 is the default for product exploration. 8,000 remains the validated control setting.",
    )'''
if old_mc not in s:
    raise SystemExit("STOP: Monte Carlo control block not found")
s = s.replace(old_mc, new_mc)

marker = '''@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached('''
helper = '''@st.cache_data(ttl=86400, show_spinner=False)
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


@st.cache_data(show_spinner=False)
def calculate_league_intelligence_cached('''
if marker not in s:
    raise SystemExit("STOP: calculate cache marker not found")
s = s.replace(marker, helper, 1)

old_load = '''    player_map = fetch_player_map()
    all_weeks, endpoint_log = load_sleeper_player_weeks(
        seasons=seasons,
        scoring_settings=sc,
        player_map=player_map,
    )
    validate_weekly_contract(all_weeks)
'''
new_load = '''    # Historical Sleeper scoring/input preparation is cached independently from
    # Monte Carlo settings, so switching 2k/4k/8k does not refetch/rebuild the base data.
    all_weeks, endpoint_log = load_scored_history_cached(tuple(seasons), scoring_json)
'''
if old_load not in s:
    raise SystemExit("STOP: historical input block not found")
s = s.replace(old_load, new_load, 1)

# Make the function's fallback/default consistent with the faster product default.
s = s.replace('seasons=(2023, 2024, 2025), n_sims=8000, seed=7',
              'seasons=(2023, 2024, 2025), n_sims=4000, seed=7')

# Surface the performance contract without adding backoffice clutter.
needle = '''compute = st.button(
    "Calculate league-specific 3-Year WoRP",
    type="primary",
    width="stretch",
)
'''
replacement = needle + '''st.caption("Performance: 4,000 simulations is the standard product mode; 8,000 remains available for validated-control reruns. Repeated runs reuse cached historical Sleeper inputs.")
'''
if needle not in s:
    raise SystemExit("STOP: compute button block not found")
s = s.replace(needle, replacement, 1)

DST.write_text(s, encoding="utf-8")
compile(s, str(DST), "exec")
print("PASS: app_v0_7_2.py created")
print("Engine V0.2.1 unchanged")
print("Performance: 4k default, 2k preview, 8k validated control, historical Sleeper inputs cached for 24h")
