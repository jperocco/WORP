from pathlib import Path

SRC=Path('app_v0_9_3.py'); DST=Path('app_v0_9_4.py')
if not SRC.exists(): raise SystemExit('STOP: app_v0_9_3.py not found')
s=SRC.read_text(encoding='utf-8')
s=s.replace('UI V0.9.3','UI V0.9.4').replace('WoRP-Lab/0.9.3','WoRP-Lab/0.9.4').replace('WoRP Lab UI V0.9.3','WoRP Lab UI V0.9.4')

# Add a scoring-only lineup model. This intentionally does not consume WoRP.
marker='def build_lineup_economics('
start=s.find(marker)
end=s.find('\n@st.cache_data(show_spinner=False)\ndef calculate_league_intelligence_cached(', start)
if start<0 or end<0: raise SystemExit('STOP: V0.9.3 lineup helper block not found')
helper=r'''def build_lineup_scoring_share(player_weeks, teams, qb, rb, wr, te, flex, superflex):
    """Historical lineup anatomy using fantasy points only — never WoRP.

    For each season/week, fixed slots consume the top N players at their position.
    FLEX and SUPER_FLEX then consume the highest-scoring remaining eligible players.
    Across league-wide vacancies, points/week is the mean score of the players who
    occupy that slot layer; lineup share is that layer's points divided by the sum
    of all slot-layer points. Occupancy is the position mix of those winners.
    """
    import pandas as pd
    teams=int(teams)
    fixed={'QB':int(qb),'RB':int(rb),'WR':int(wr),'TE':int(te)}
    slot_names=[]
    for pos in ('QB','RB','WR','TE'):
        for i in range(fixed[pos]): slot_names.append(pos if fixed[pos]==1 else f'{pos}{i+1}')
    slot_names += [f'FLEX {i+1}' for i in range(int(flex))]
    slot_names += [f'SUPER_FLEX {i+1}' for i in range(int(superflex))]
    acc={name:{'points':[],'positions':[]} for name in slot_names}

    for (_, _), week in player_weeks.groupby(['season','week']):
        week=week[week['position'].isin(['QB','RB','WR','TE'])].copy()
        week=week.sort_values('fantasy_points',ascending=False)
        used=set()
        # Fixed positional layers.
        for pos in ('QB','RB','WR','TE'):
            p=week[week['position']==pos].sort_values('fantasy_points',ascending=False)
            for i in range(fixed[pos]):
                name=pos if fixed[pos]==1 else f'{pos}{i+1}'
                winners=p.iloc[i*teams:(i+1)*teams]
                if len(winners):
                    acc[name]['points'].append(float(winners['fantasy_points'].mean()))
                    acc[name]['positions'] += winners['position'].tolist()
                    used.update(winners.index.tolist())
        # Flexible vacancies are filled successively from remaining eligible players.
        def fill(name, eligible):
            nonlocal used
            pool=week[(week['position'].isin(eligible)) & (~week.index.isin(used))]
            winners=pool.sort_values('fantasy_points',ascending=False).head(teams)
            if len(winners):
                acc[name]['points'].append(float(winners['fantasy_points'].mean()))
                acc[name]['positions'] += winners['position'].tolist()
                used.update(winners.index.tolist())
        for i in range(int(flex)): fill(f'FLEX {i+1}',['RB','WR','TE'])
        for i in range(int(superflex)): fill(f'SUPER_FLEX {i+1}',['QB','RB','WR','TE'])

    rows=[]
    for name in slot_names:
        pts=float(pd.Series(acc[name]['points']).mean()) if acc[name]['points'] else float('nan')
        vc=pd.Series(acc[name]['positions']).value_counts(normalize=True) if acc[name]['positions'] else pd.Series(dtype=float)
        rows.append({'slot':name,'points_week':pts,'occupancy':vc.to_dict()})
    total=sum(r['points_week'] for r in rows if pd.notna(r['points_week']) and r['points_week']>0)
    for r in rows: r['lineup_share']=(r['points_week']/total if total>0 and pd.notna(r['points_week']) else 0.0)
    return rows


'''
s=s[:start]+helper+s[end+1:]

# Replace old table UI with cards. We load exact Sleeper-scored 2023-25 weekly points,
# using the already validated canonical loader and the selected league scoring settings.
ui_start=s.find('        st.markdown("##### Lineup Economics")')
ui_end=s.find('        # V0.9.2 — league-native Roster Construction product layer.', ui_start)
if ui_start<0 or ui_end<0: raise SystemExit('STOP: Lineup Economics UI block not found')
ui=r'''        st.markdown("##### Lineup Share")
        st.caption("How much of this league's expected starting-lineup scoring comes from each slot — and which positions fill flexible slots.")
        try:
            _pw,_ = load_sleeper_player_weeks([2023,2024,2025], _sc, player_map=fetch_player_map())
            lineup_rows=build_lineup_scoring_share(_pw,_teams,_qb,_rb,_wr,_te,_flex,_superflex)
            cards=[]
            for lr in lineup_rows:
                occ=lr['occupancy']
                mix=''.join(f'<div class="ls-mix">{p} {100*v:.0f}%</div>' for p,v in sorted(occ.items(),key=lambda kv:kv[1],reverse=True))
                card=(
                    f'<div class="ls-card"><div class="ls-slot">{lr["slot"]}</div>'
                    f'<div class="ls-share">{100*lr["lineup_share"]:.1f}%</div>'
                    f'<div class="ls-pts">{lr["points_week"]:.1f} pts/week</div>{mix}</div>'
                )
                cards.append(card)
            st.markdown("""<style>
            .ls-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:8px 0 16px 0}
            .ls-card{border:1px solid rgba(128,128,128,.35);border-radius:14px;padding:16px 14px;text-align:center;min-height:150px;background:rgba(128,128,128,.04)}
            .ls-slot{font-weight:700;font-size:15px;margin-bottom:10px}.ls-share{font-weight:800;font-size:34px;line-height:1.05}.ls-pts{font-size:16px;margin:10px 0 8px}.ls-mix{font-size:13px;opacity:.72;line-height:1.45}
            </style>""",unsafe_allow_html=True)
            st.markdown('<div class="ls-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
            st.caption("Historical 2023–25 average under this league's exact Sleeper scoring. Share is fantasy-point contribution to the expected starting lineup; flexible-slot mix is modeled positional occupancy. WoRP is not used in this panel.")
        except Exception as exc: st.caption(f"Lineup Share unavailable: {exc}")

'''
s=s[:ui_start]+ui+s[ui_end:]
DST.write_text(s,encoding='utf-8'); compile(s,str(DST),'exec')
print('PASS: app_v0_9_4.py created')
print('Lineup Share rebuilt from fantasy points only; WoRP removed from panel')
print('Cards: slot + % lineup points + pts/week + flexible-slot occupancy')
print('Historical window: 2023-2025, exact selected-league Sleeper scoring')
print('Roster Construction block preserved')
