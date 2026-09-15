#!/usr/bin/env python3
"""V0.16.1 — IDP-safe launcher for multi-league offensive roster-depth capture.

The first V0.16 smoke test exposed an important preflight bug: Sleeper IDP starter
slots were counted in StartN although WoRP currently models QB/RB/WR/TE offense.
V0.15 now fixes format classification. This launcher also forces V0.16's empirical
core baseline to count offensive starter slots only. Generic BN capacity in IDP
leagues is not interpreted as additional offensive Scoring demand.
"""
import worp_multileague_roster_depth_capture_v0_16 as v16

OFFENSIVE_START={'QB','RB','WR','TE','FLEX','REC_FLEX','SUPER_FLEX','SUPERFLEX','OP'}

def offensive_starter_count(lg):
    return sum(p in OFFENSIVE_START for p in (lg.get('roster_positions') or []))

v16.starter_count=offensive_starter_count

if __name__=='__main__':
    v16.main()
