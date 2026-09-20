"""Joint QB/RB allocation diagnostic on lagged ownership, not product quotas.

Uses frozen engine V0.2.1 and exact Sleeper scoring. Compares equal budgets
on identical roster-week support, with league-season weighting in summaries.
No target-week outcomes select the roster, baseline or option pool.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
from sleeper_native_loader import normalize_stats_payload, score_stats_exact
from worp_engine import LeagueSettings, calculate_season_worp
from worp_optionality_capacity_audit import fetch, compositions, cumulative, positive_oracle_ids, POS


def cached_json(url, path):
    if path.exists():
        return json.loads(path.read_text())
    value = fetch(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(",", ":")))
    return value


def select_leagues(inventory):
    """Pre-outcome sample: three format strata, six league-seasons each."""
    d = inventory.copy()
    d["slots"] = d.roster_positions.map(json.loads)
    allowed = set(POS) | {"FLEX", "SUPER_FLEX", "BN"}
    d = d[d.slots.map(lambda xs: bool(xs) and set(xs) <= allowed)]
    d = d[d.season.isin([2023, 2024, 2025])]
    d = d[d.settings.map(lambda x: not json.loads(x).get("best_ball", 0))]
    d = d[d.slots.map(lambda xs: "SUPER_FLEX" in xs or xs.count("QB") == 1)]
    d["stratum"] = d.slots.map(lambda xs: "1QB" if "SUPER_FLEX" not in xs
                                else "SF_2TE" if xs.count("TE") >= 2 else "SF_1TE")
    chosen = []
    for (stratum, season), group in d.groupby(["stratum", "season"], sort=True):
        # Balance on team count where possible. No outcome-based selection.
        group = group.sort_values(["total_rosters", "league_id"])
        first = group.iloc[0]
        chosen.append(first)
        rest = group[group.league_id.ne(first.league_id)]
        if not rest.empty:
            different = rest[rest.total_rosters.ne(first.total_rosters)]
            chosen.append((different if not different.empty else rest).iloc[0])
    return pd.DataFrame(chosen).drop(columns="slots")


def slot_contributions(base, options, orders, outcomes, legal, position):
    j = POS.index(position)
    pad = int(legal[:, j].max())
    answer = np.zeros((len(options) + 1, len(orders), len(legal)))
    for draw, order in enumerate(orders):
        kept = set(base)
        answer[0, draw] = cumulative(kept, outcomes, position, pad)[legal[:, j]]
        for k, pid in enumerate(order, 1):
            kept.add(pid)
            answer[k, draw] = cumulative(kept, outcomes, position, pad)[legal[:, j]]
    return answer


def joint_values(base, qb_options, rb_options, future, legal, budgets, draws, rng):
    """Coupled random orderings allow paired equal-budget comparisons."""
    qo = [rng.permutation(sorted(qb_options)) for _ in range(draws)]
    ro = [rng.permutation(sorted(rb_options)) for _ in range(draws)]
    allocations = [(b, q, b-q) for b in budgets for q in range(b+1)
                   if q <= len(qb_options) and b-q <= len(rb_options)]
    value = {key: np.zeros(draws) for key in allocations}
    for outcomes in future:
        qc = slot_contributions(base, qb_options, qo, outcomes, legal, "QB")
        rc = slot_contributions(base, rb_options, ro, outcomes, legal, "RB")
        other = np.zeros(len(legal))
        for p in ("WR", "TE"):
            j = POS.index(p)
            other += cumulative(base, outcomes, p, int(legal[:,j].max()))[legal[:,j]]
        baseline = (qc[0] + rc[0] + other).max(axis=1)
        for key in allocations:
            _, q, r = key
            value[key] += (qc[q] + rc[r] + other).max(axis=1) - baseline
    return value


def run(root, out, cache, draws=64):
    out.mkdir(parents=True, exist_ok=True)
    inventory_path = root / "sleeper_user_league_inventory_v0_14.csv"
    manifest = out / "selected_league_seasons.csv"
    if manifest.exists():
        chosen = pd.read_csv(manifest, dtype={"league_id": str})
    else:
        inventory = pd.read_csv(inventory_path, dtype={"league_id": str})
        chosen = select_leagues(inventory)
    chosen.to_csv(out / "selected_league_seasons.csv", index=False)
    print(f"Selected {len(chosen)} league-seasons across {chosen.stratum.nunique()} strata", flush=True)
    pmap = cached_json("https://api.sleeper.app/v1/players/nfl", cache / "players.json")
    def stats_job(key):
        season, week = key
        path = cache / f"stats_{season}_{week}.json"
        urls = [f"https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular",
                f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}"]
        error = None
        for url in urls:
            try:
                return key, normalize_stats_payload(cached_json(url, path))
            except Exception as exc:
                error = exc
        raise RuntimeError(f"Stats failed for {key}: {error}")
    with ThreadPoolExecutor(max_workers=8) as ex:
        stats = dict(ex.map(stats_job, [(s,w) for s in sorted(chosen.season.unique()) for w in range(1,19)]))
    print("Shared raw stats ready", flush=True)
    detail, pairs, support, failures = [], [], [], []
    for row in chosen.itertuples():
        lid, season = str(row.league_id), int(row.season)
        try:
            slots, scoring = json.loads(row.roster_positions), json.loads(row.scoring_settings)
            legal = compositions(slots)
            settings = LeagueSettings(teams=int(row.total_rosters), qb=slots.count("QB"),
                rb=slots.count("RB"), wr=slots.count("WR"), te=slots.count("TE"),
                flex=slots.count("FLEX"), superflex=slots.count("SUPER_FLEX"),
                ppr=float(scoring.get("rec",0)), te_premium=float(scoring.get("bonus_rec_te",0)))
            native_path = cache / f"weekly_{lid}.csv"
            if native_path.exists():
                weekly = pd.read_csv(native_path, dtype={"player_id":str})
            else:
                records=[]
                for week in range(1,19):
                    for pid, st in stats[season,week].items():
                        pos=pmap.get(pid,{}).get("position")
                        if pos not in POS:
                            continue
                        records.append({"season":season,"week":week,"player_id":pid,
                            "player_name":pid,"position":pos,"fantasy_points":score_stats_exact(st,scoring)})
                weekly,_=calculate_season_worp(pd.DataFrame(records),settings,n_sims=2500,seed=7)
                weekly.to_csv(native_path,index=False)
            outcomes={int(w):{r.player_id:(r.position,max(0.,float(r.weekly_worp)))
                for r in g.itertuples()} for w,g in weekly.groupby("week")}
            def snap_job(week):
                return week,cached_json(f"https://api.sleeper.app/v1/league/{lid}/matchups/{week}",cache/f"matchups_{lid}_{week}.json")
            with ThreadPoolExecutor(max_workers=8) as ex:
                snaps=dict(ex.map(snap_job,range(1,19)))
            history={}
            for week, entries in snaps.items():
                for entry in entries:
                    owned={str(pid) for pid in entry.get("players") or []}
                    used={str(pid) for pid in entry.get("starters") or []}
                    used |= positive_oracle_ids(owned,outcomes.get(week,{}),legal)
                    history[week,entry["roster_id"]]=(owned,used)
            for week in range(4,16):
                for snapshot in snaps[week-1]:
                    rid=snapshot["roster_id"]
                    prior=[history.get((w,rid)) for w in range(max(1,week-5),week)]
                    if any(x is None for x in prior):
                        continue
                    # Only past ownership and usage are consulted here.
                    owned=prior[-1][0]
                    eligible={pid for pid in owned if pid in prior[-2][0] and pid in prior[-3][0]
                              and not any(pid in used for _,used in prior)}
                    eligible={pid for pid in eligible if pmap.get(pid,{}).get("position") in POS}
                    base={pid for pid in owned-eligible if pmap.get(pid,{}).get("position") in POS}
                    qpool={pid for pid in eligible if pmap[pid]["position"]=="QB"}
                    rpool={pid for pid in eligible if pmap[pid]["position"]=="RB"}
                    feasible=[b for b in (8,9) if len(base)+b<=len(slots) and len(qpool)+len(rpool)>=b]
                    support.append({"league_id":lid,"season":season,"stratum":row.stratum,
                        "week":week,"roster_id":rid,"active_capacity":len(slots),"baseline_size":len(base),
                        "qb_pool":len(qpool),"rb_pool":len(rpool),"budget8_feasible":8 in feasible,"budget9_feasible":9 in feasible})
                    if not feasible:
                        continue
                    seed=int(hashlib.sha256(f"{lid}:{rid}:{week}".encode()).hexdigest()[:8],16)
                    values=joint_values(base,qpool,rpool,[outcomes[w] for w in range(week,week+4)],
                                        legal,feasible,draws,np.random.default_rng(seed))
                    for (budget,q,r), gains in values.items():
                        record={"league_id":lid,"season":season,"stratum":row.stratum,"week":week,"roster_id":rid,
                                "budget":budget,"qb_options":q,"rb_options":r,"mean_gain":float(gains.mean())}
                        for hurdle in (.25, .50, .75):
                            record[f"chance_gain_ge_{int(hurdle*100):03d}"]=float((gains>=hurdle).mean())
                        detail.append(record)
                        alternative=values.get((budget,q+1,r-1))
                        if alternative is not None:
                            diff=alternative-gains
                            pairs.append({**record,"delta_more_qb":float(diff.mean()),
                                "delta_chance_ge_050":float(((alternative>=.50).astype(float)-(gains>=.50)).mean()),
                                "mc_standard_error":float(diff.std(ddof=1)/np.sqrt(draws))})
            print(f"PASS {season} {lid} {row.stratum}: cumulative {len(pairs)} paired comparisons",flush=True)
        except Exception as exc:
            failures.append({"league_id":lid,"season":season,"error":str(exc)})
            print(f"FAIL {lid}: {exc}",flush=True)
        # Checkpoint all computed results after every league.
        for name,data in (("portfolio_detail",detail),("paired_detail",pairs),("pool_support",support),("failures",failures)):
            pd.DataFrame(data).to_csv(out/f"{name}.csv",index=False)
    if not pairs:
        raise RuntimeError("No paired portfolio comparisons; inspect support and failures")
    p=pd.DataFrame(pairs)
    keys=["stratum","budget","qb_options","rb_options"]
    league_means=p.groupby(keys+["league_id","season"],as_index=False).agg(
        paired_roster_weeks=("delta_more_qb","size"),mean_delta_more_qb=("delta_more_qb","mean"))
    tail_means=p.groupby(keys+["league_id","season"],as_index=False).delta_chance_ge_050.mean()
    league_means=league_means.merge(tail_means,on=keys+["league_id","season"],validate="one_to_one")
    league_means.to_csv(out/"paired_league_means.csv",index=False)
    summary=league_means.groupby(keys,as_index=False).agg(
        league_seasons=("league_id","size"),seasons=("season","nunique"),
        equal_weight_mean_delta=("mean_delta_more_qb","mean"),
        equal_weight_tail_probability_delta=("delta_chance_ge_050","mean"),
        minimum_league_delta=("mean_delta_more_qb","min"),maximum_league_delta=("mean_delta_more_qb","max"),
        paired_roster_weeks=("paired_roster_weeks","sum"))
    summary.to_csv(out/"paired_summary.csv",index=False)
    print(summary.to_string(index=False))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).parent)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--cache",type=Path,required=True)
    ap.add_argument("--draws",type=int,default=64)
    a=ap.parse_args()
    run(a.root,a.out,a.cache,a.draws)
