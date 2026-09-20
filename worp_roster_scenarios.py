"""User-authored positional scenarios. No optimization or player membership."""
import hashlib
import json
from numbers import Integral

POSITIONS = ('QB', 'RB', 'WR', 'TE')


def evaluate_scenario(core, extra, capacity, slots, envelope):
    for counts in (core, extra):
        if set(counts) != set(POSITIONS) or any(isinstance(v,bool) or not isinstance(v,Integral) or v < 0 for v in counts.values()):
            raise ValueError('Use non-negative whole numbers for all four positions.')
    if isinstance(capacity,bool) or not isinstance(capacity,Integral) or capacity < 0:
        raise ValueError('Invalid active-roster capacity.')
    unsupported=set(slots)-set(POSITIONS)-{'FLEX','SUPER_FLEX','BN','BENCH','IR','TAXI'}
    total={p:int(core[p]+extra[p]) for p in POSITIONS}
    core_n=sum(core.values());extra_n=sum(extra.values());allocated=core_n+extra_n
    fixed={p:slots.count(p) for p in POSITIONS}
    remaining={p:total[p]-fixed[p] for p in POSITIONS}
    can_start=(not unsupported and all(v>=0 for v in remaining.values())
               and sum(remaining[p] for p in ('RB','WR','TE'))>=slots.count('FLEX')
               and sum(remaining.values())>=slots.count('FLEX')+slots.count('SUPER_FLEX'))
    checks=[]
    for p in POSITIONS:
        lo,hi=int(envelope[p+'_low']),int(envelope[p+'_high'])
        status='Below range' if core[p]<lo else 'Above range' if core[p]>hi else 'Within range'
        checks.append(dict(Position=p,Scoring=int(core[p]),Reference=f'{lo}–{hi}',
                           Comparison=status,Extra=int(extra[p]),Total=total[p]))
    low,high=int(envelope['scoring_core_low']),int(envelope['scoring_core_high'])
    return dict(total=total,core=core_n,extra=extra_n,allocated=allocated,remaining=capacity-allocated,
                extra_budget=max(0,capacity-core_n),can_start=can_start,
                complete=allocated==capacity,saveable=allocated==capacity and can_start,
                core_in_range=low<=core_n<=high,reference_fits=low<=capacity,
                unsupported=sorted(unsupported),rows=checks)


def scenario_key(league_id,slots,scoring,envelope,capacity):
    payload=json.dumps([str(league_id),slots,scoring,envelope,capacity],sort_keys=True,default=str)
    return 'worp_scenario_'+hashlib.sha256(payload.encode()).hexdigest()[:20]


def render_roster_scenarios(envelope,capacity,slots,league_id,scoring):
    import pandas as pd
    import streamlit as st
    key=scenario_key(league_id,slots,scoring,envelope,capacity)
    low,high=int(envelope['scoring_core_low']),int(envelope['scoring_core_high'])
    a,b=st.columns(2)
    a.metric('Active roster',capacity)
    b.metric('Scoring Core reference',f'{low}–{high}')
    st.write(' · '.join(f"{p} {envelope[p+'_low']}–{envelope[p+'_high']}" for p in POSITIONS))
    if envelope.get('source')=='LEAGUE_NATIVE_DERIVED':
        st.write('These reference ranges are model estimates.')
    if high>capacity:
        st.warning('The reference Core range extends beyond this roster size. Use the capacity limit below; the reference has not been reduced automatically.')
    st.markdown('**Build your roster scenario**')
    st.write('Choose Scoring and extra places by position. This is your construction choice; the app does not recommend an ideal split.')
    core,extra={},{}
    for p,col in zip(POSITIONS,st.columns(4)):
        with col:
            st.markdown(f'**{p}**')
            core[p]=int(st.number_input(f'{p} Scoring',min_value=0,max_value=capacity,value=0,step=1,key=key+'core'+p))
            extra[p]=int(st.number_input(f'{p} Extra',min_value=0,max_value=capacity,value=0,step=1,key=key+'extra'+p))
            st.metric(f'Total {p}',core[p]+extra[p])
    result=evaluate_scenario(core,extra,capacity,slots,envelope)
    a,b,c=st.columns(3)
    a.metric('Scoring chosen',result['core'])
    b.metric('Extra places chosen',result['extra'])
    c.metric('Places remaining',result['remaining'])
    if result['remaining']>0:
        st.info(f"Assign {result['remaining']} more places to complete the {capacity}-player roster.")
    elif result['remaining']<0:
        st.warning(f"Remove {-result['remaining']} places to fit the {capacity}-player roster.")
    elif result['can_start']:
        st.success(f"{capacity}/{capacity} places assigned. The roster can fill this league's starting slots.")
    if result['unsupported']:
        st.warning('This editor cannot check these starting slots: '+', '.join(result['unsupported']))
    elif result['complete'] and not result['can_start']:
        st.warning('This distribution cannot fill every starting slot. Adjust the positional counts, including FLEX/SF eligibility.')
    if result['core']:
        st.write(f"With {result['core']} Scoring places, this roster has {result['extra_budget']} places left for optionality.")
        if not result['core_in_range']:
            st.warning(f"Your Scoring total is outside the {low}–{high} reference range.")
    st.dataframe(pd.DataFrame(result['rows']),hide_index=True,width='stretch')
    st.write('The reference ranges describe each position separately. Being within every range does not validate the combination or identify individual Scoring players.')
    saved=st.session_state.setdefault(key+'saved',{})
    name=st.text_input('Scenario name',value='',placeholder='e.g. More QB depth',key=key+'name')
    if st.button('Save scenario',disabled=not result['saveable'] or not name.strip(),key=key+'save'):
        saved[name.strip()]={
            'Scenario':name.strip(),**result['total'],'Scoring':result['core'],'Extra':result['extra'],
            'Total':result['allocated'],'Core comparison':'Within total range' if result['core_in_range'] else 'Outside total range',
            **{p+' Scoring':core[p] for p in POSITIONS},**{p+' Extra':extra[p] for p in POSITIONS}}
    if saved:
        st.markdown('**Compare your scenarios**')
        st.write('Scenarios remain available during this app session. Saving the same name replaces that scenario.')
        table=pd.DataFrame(saved.values())
        st.dataframe(table,hide_index=True,width='stretch')
        st.download_button('Export scenarios',table.to_csv(index=False).encode(),file_name='worp_roster_scenarios.csv',mime='text/csv',key=key+'export')
