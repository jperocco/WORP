#!/usr/bin/env python3
"""WoRP Lab — Scoring Depth Absorption V0.6.2

Uses V0.6.1 transition detail to ask the next roster-construction question:
when a player is STARTED in week t after NOT starting in week t-1, where did that
starter come from? Existing scoring bench, rostered non-scoring, or FREE?

This measures the observed source of new lineup demand. FREE is not required to
produce WoRP while it remains Non-Scoring; only actual FREE->START transitions
count as direct waiver scoring.

Wookiee 2023-25 reference audit only.
"""
from pathlib import Path
import pandas as pd
P=Path('worp_roster_state_transitions_detail_v0_6_1.csv')
POS=['QB','RB','WR','TE']
def main():
 if not P.exists():raise FileNotFoundError(P)
 d=pd.read_csv(P)
 # New starter = STARTED now, but not STARTED in prior snapshot.
 x=d[(d.next_state=='STARTED')&(d.state!='STARTED')&d.position.isin(POS)].copy()
 x['source']=x.state.map({'BENCHED_SCORING':'SCORING_BENCH','ROSTERED_NON_SCORING':'ROSTERED_NON_SCORING','FREE':'FREE_DIRECT'}).fillna(x.state)
 # next_worp is the WoRP actually captured by that new starter in the target week.
 rows=[]
 for pos,g in x.groupby('position'):
  total=len(g)
  for src,h in g.groupby('source'):
   rows.append({'position':pos,'source':src,'new_starts':len(h),'share_of_new_starts':len(h)/total if total else 0,
                'positive_new_starts':int((h.next_worp>0).sum()),'positive_rate':(h.next_worp>0).mean(),
                'total_next_week_worp':h.next_worp.sum(),'mean_next_week_worp':h.next_worp.mean()})
 out=pd.DataFrame(rows)
 piv=out.pivot(index='position',columns='source',values='share_of_new_starts').fillna(0).reset_index()
 for c in ['SCORING_BENCH','ROSTERED_NON_SCORING','FREE_DIRECT']:
  if c not in piv.columns:piv[c]=0.0
 piv['EXISTING_ROSTER']=piv['SCORING_BENCH']+piv['ROSTERED_NON_SCORING']
 piv=piv[['position','SCORING_BENCH','ROSTERED_NON_SCORING','FREE_DIRECT','EXISTING_ROSTER']]
 out.to_csv('worp_depth_absorption_detail_v0_6_2.csv',index=False);piv.to_csv('worp_depth_absorption_summary_v0_6_2.csv',index=False)
 print('='*105);print('WORP SCORING-DEPTH ABSORPTION V0.6.2');print('='*105)
 print(piv.to_string(index=False))
 print('\nSOURCE QUALITY / CAPTURED WORP');print(out.to_string(index=False))
 print('\nREAD: EXISTING_ROSTER is the observed share of new starts supplied without direct FREE->START scoring.')
 print('This still does NOT prove optimal roster depth; next step is rank/depth of the promoted existing-roster players.')
if __name__=='__main__':main()
