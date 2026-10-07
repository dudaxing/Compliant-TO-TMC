"""Read actual proposal deltas and closed scalar JSON only."""
import json
from pathlib import Path
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path('D:/hf-margin4-author-20261007/closure_proposals_001')
m=json.loads((OUT/'manifest.json').read_bytes())
for name,entry in m['files'].items():
    if name.endswith('.json'):continue
    new=(OUT/entry['path']).read_bytes();old=(ROOT/name).read_bytes() if (ROOT/name).exists() else b''
    if name=='docs/WORKPIECE_ENLARGEMENT_20261007.md':delta=new[len(old):]
    elif old and new.endswith(old):delta=new[:-len(old)]
    else:delta=new
    print(json.dumps({'proposal':name,'new_text':delta.decode('utf-8')},ensure_ascii=False))
data=m['closed_summary'];facts={}
for label,c in data['cases'].items():
    ref=json.loads((ROOT/c['stage']/'reference/summary.json').read_bytes())
    lifecycle=json.loads((ROOT/c['stage']/'reference/lifecycle.json').read_bytes()) if (ROOT/c['stage']/'reference/lifecycle.json').exists() else {}
    facts[label]={k:c[k] for k in ['accepted_states','call_counts','production_helper_seconds','production_outer_seconds','reference_helper_seconds','reference_outer_seconds','HP_calls','checks_completed','maximum_loading_stroke','return_state','loading_Fy_peak']}
    facts[label]['reference_lifecycle_elapsed']=lifecycle.get('elapsed_seconds')
print(json.dumps({'actual_closed_scalars':facts,'view':data['view']},ensure_ascii=False))
