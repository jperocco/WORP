from pathlib import Path

SRC = Path("app_v0_9_2.py")
DST = Path("app_v0_9_3.py")
if not SRC.exists(): raise SystemExit("STOP: app_v0_9_2.py not found")
s = SRC.read_text(encoding="utf-8")
s = s.replace('UI V0.9.2','UI V0.9.3').replace('WoRP-Lab/0.9.2','WoRP-Lab/0.9.3').replace('WoRP Lab UI V0.9.2','WoRP Lab UI V0.9.3')

fn_marker='@st.cache_data(show_spinner=False)\ndef calculate_league_intelligence_cached(\n'
helper=r'''def build_lineup_economics(curve, teams, qb, rb, wr, te, flex, superflex):
    """Player-free slot occupancy from league-native positional WoRP ranks.

    For each flexible layer, eligible positional rank entries compete directly
    for exactly `teams` lineup vacancies. Share = count of winning rank entries
    by position / teams. It is NOT a ratio of positional WoRP means.
    """
    teams=int(teams); fixed={"QB":int(qb),"RB":int(rb),"WR":int(wr),"TE":int(te)}
    consumed={p: fixed[p]*teams for p in fixed}; rows=[]

    def rank_slice(pos, lo, hi):
        x=curve[(curve["position"]==pos)&(curve["position_rank"].between(lo,hi))].copy()
        return x[["position","position_rank","three_year_worp_avg"]].dropna()

    for pos in ("QB","RB","WR","TE"):
        for i in range(fixed[pos]):
            lo=i*teams+1; hi=(i+1)*teams; x=rank_slice(pos,lo,hi)
            rows.append({"slot":pos if fixed[pos]==1 else f"{pos}{i+1}","shares":{pos:1.0},
                         "avg_worp":float(x["three_year_worp_avg"].mean()) if len(x) else float("nan"),
                         "rank_range":f"{pos}{lo}–{pos}{hi}"})

    def flexible(label, eligible):
        pool=[]; evidence=[]
        # Pull enough next ranks from every eligible position to fill one full
        # league-wide slot layer. Winners are the top `teams` WoRP rank entries.
        for pos in eligible:
            lo=consumed[pos]+1; hi=consumed[pos]+teams
            x=rank_slice(pos,lo,hi); pool.append(x); evidence.append(f"{pos}{lo}–{pos}{hi}")
        import pandas as pd
        cand=pd.concat(pool,ignore_index=True) if pool else pd.DataFrame()
        cand=cand[cand["three_year_worp_avg"]>0].sort_values(["three_year_worp_avg","position_rank"],ascending=[False,True])
        winners=cand.head(teams)
        counts=winners["position"].value_counts().to_dict() if len(winners) else {}
        denom=len(winners)
        shares={p:(counts.get(p,0)/denom if denom else 0.0) for p in eligible}
        # Only ranks that actually win vacancies are consumed. This lets the next
        # FLEX layer continue from the correct positional frontier.
        for pos in eligible: consumed[pos]+=int(counts.get(pos,0))
        rows.append({"slot":label,"shares":shares,
                     "avg_worp":float(winners["three_year_worp_avg"].mean()) if len(winners) else float("nan"),
                     "rank_range":" · ".join(evidence)})

    for i in range(int(flex)): flexible(f"FLEX {i+1}",["RB","WR","TE"])
    for i in range(int(superflex)): flexible(f"SUPER_FLEX {i+1}",["QB","RB","WR","TE"])
    return rows


'''
if fn_marker not in s: raise SystemExit("STOP: calculate marker not found")
s=s.replace(fn_marker,helper+fn_marker,1)
ui_marker='        # V0.9.2 — league-native Roster Construction product layer.\n'
ui=r'''        _teams=int(league.get("total_rosters",0) or 0)
        _qb=int(counts.get("QB",0)); _rb=int(counts.get("RB",0)); _wr=int(counts.get("WR",0)); _te=int(counts.get("TE",0))
        _flex=int(counts.get("FLEX",0)); _superflex=int(counts.get("SUPER_FLEX",0)); _sc=league.get("scoring_settings",{}) or {}
        st.markdown("##### Lineup Economics")
        st.caption("Who wins this league's starting vacancies by position. Flexible-slot share is vacancy occupancy, not a ratio of WoRP averages.")
        try:
            lineup_rows=build_lineup_economics(curve,_teams,_qb,_rb,_wr,_te,_flex,_superflex)
            display=[]
            for lr in lineup_rows:
                mix=" · ".join(f"{p} {100*v:.0f}%" for p,v in sorted(lr["shares"].items(),key=lambda kv:kv[1],reverse=True) if v>0) or "No positive-WoRP occupancy"
                display.append({"Slot":lr["slot"],"Lineup share":mix,"WoRP layer":round(lr["avg_worp"],2) if pd.notna(lr["avg_worp"]) else "—","Rank evidence":lr["rank_range"]})
            st.dataframe(pd.DataFrame(display),hide_index=True,use_container_width=True)
            st.caption("Each flexible layer has one vacancy per team. Eligible positional ranks compete directly for those vacancies under this league's scoring; shares count the positions that win them. Rank depth scales with team count.")
        except Exception as exc: st.caption(f"Lineup Economics unavailable: {exc}")

'''
if ui_marker not in s: raise SystemExit("STOP: RC marker not found")
s=s.replace(ui_marker,ui+ui_marker,1)
s=s.replace('start_n = int(qb) + int(rb) + int(wr) + int(te) + int(flex) + int(superflex)','start_n = _qb + _rb + _wr + _te + _flex + _superflex')
s=s.replace('tep = float(sc.get("bonus_rec_te", 0.0)) > 0','tep = float(_sc.get("bonus_rec_te", 0.0)) > 0')
s=s.replace('f"{int(teams)}T "','f"{_teams}T "').replace('(\"SF \" if int(superflex) > 0 else \"1QB \")','("SF " if _superflex > 0 else "1QB ")')
s=s.replace('f"Start{start_n} QB{int(qb)} RB{int(rb)} WR{int(wr)} TE{int(te)} "','f"Start{start_n} QB{_qb} RB{_rb} WR{_wr} TE{_te} "').replace('f"FLEX{int(flex)} SFLEX{int(superflex)}"','f"FLEX{_flex} SFLEX{_superflex}"')
DST.write_text(s,encoding="utf-8"); compile(s,str(DST),"exec")
print("PASS: app_v0_9_3.py created")
print("Lineup Share = flexible-slot vacancy occupancy by position")
print("Removed WoRP-ratio pseudo-share")
print("One vacancy per team per flexible layer; team-count adaptive")
print("Engine V0.2.1 and frozen Roster Construction unchanged")
