#!/usr/bin/env python3
"""Static arithmetic and uniqueness checks only. No model or experimental data access."""
import json, math, pathlib
root=pathlib.Path(__file__).resolve().parent
p=json.loads((root/'02_SMOKE_FINAL_PROTOCOL_PROPOSED.json').read_text(encoding='utf-8'))
s=p['smoke']; f=p['new_final_main']
assert len(s['centers'])==8 and len(set(s['centers']))==8
assert len(f['centers'])==32 and len(set(f['centers']))==32
assert not(set(s['centers'])&set(f['centers']))
assert len(p['baseline_ids_6_core'])==6 and len(p['original_cmc_baselines_6'])==6
assert 8*2*3*6==288 and 288*24==6912
assert 2*2*2*6==48 and 48*24==1152
assert (6912+1152)*50+8*2*50==404000
assert 32*3*3*12==3456 and 3456*24==82944
assert 82944*50+32*3*50==4152000
assert math.floor(0.05*8*2*24)==19
assert math.floor(0.05*32*3*24)==115
assert set(p['mandatory_stop'].values())=={True}
assert len(p['baseline_ids_6_core'])-1 + len(p['original_cmc_baselines_6'])==11
assert 'all_11_declared_baselines' in p['new_final_main']['primary_comparator_lock']['scope']
assert p['new_final_main']['primary_comparator_lock']['if_none']=='FINAL_MAIN_INCONCLUSIVE'
print('STATIC_QA_PASS: 336 smoke trajectories, 8064 smoke stages, 404000 nominal SGD bound; 3456 final trajectories, 82944 final stages, 4152000 nominal bound.')
print('NOTE: No scientific data read, no model assets audited, no optimizer work generated, no experiment launched.')
