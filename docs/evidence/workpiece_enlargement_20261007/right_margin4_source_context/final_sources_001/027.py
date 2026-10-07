"""Read only closed JSON summaries and documentation; no numerical imports."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
paths={
 'production':'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/run_001/result/result.json',
 'reference':'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference/summary.json',
 'view':'functional_views/right_margin_20261007/complete_001/view/view.json',
 'case_view':'functional_views/right_margin_20261007/complete_001/view/right2col/summary.json',
 'progress':'docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json'
}
data={k:json.loads((ROOT/p).read_text(encoding='utf-8')) for k,p in paths.items()}
print(json.dumps({k:list(v) for k,v in data.items()},ensure_ascii=False))
print(json.dumps({'production_states':data['production']['accepted_states'],'reference_states':data['reference']['accepted_states'],'HP_calls':data['reference']['HP_calls_completed'],'checks':data['reference']['checks_completed']},ensure_ascii=False))
case=data['case_view']
for key in ('loading_peak','last','states','rows','peak','final','actual_loading_peak'):
 if key in case:
  value=case[key]
  if isinstance(value,list): print(json.dumps({key+'first':value[0],key+'last':value[-1]},ensure_ascii=False))
  else: print(json.dumps({key:value},ensure_ascii=False))
