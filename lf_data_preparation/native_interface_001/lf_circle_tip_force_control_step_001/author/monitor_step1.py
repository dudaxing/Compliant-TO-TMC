# Read only new ordinary progress/supervision records;never touch科学payload or media.
import json
from pathlib import Path
from time import monotonic
B=Path('D:/hfst1_001');R=B/'run_001';out={}
for path in [B/'top_start.json',B/'helper_start.json',R/'science_progress.json',R/'display_start.json',R/'science_receipt.json',R/'continuation_check.json',B/'helper_receipt.json',B/'seal_receipt.json']:
 if not path.exists():continue
 try:v=json.loads(path.read_bytes())
 except (OSError,json.JSONDecodeError):continue
 if path.name in ('top_start.json','helper_start.json','display_start.json'):
  out[path.name]=dict(elapsed_seconds=monotonic()-v['start_monotonic'],**{k:x for k,x in v.items() if k!='start_monotonic'})
 elif path.name=='science_progress.json':out[path.name]=v
 else:out[path.name]={k:v[k] for k in ('status','error','failure','production_status','target_reached','accepted_states','accepted_count','api_attempts','api_returns','call_counts','elapsed_worker_seconds','elapsed_seconds','elapsed_helper_before_final_tree_cleanup_seconds','elapsed_outer_seconds','elapsed_helper_seconds','archive','members','attempts') if k in v}
for name,path in [('top',B/'top_supervision.json'),('science',R/'science_supervision.json'),('ordinary',R/'ordinary_check_supervision.json'),('viewer',R/'viewer_supervision.json')]:
 if path.exists():
  v=json.loads(path.read_bytes());out[name+'_supervision']={k:v.get(k) for k in ('reason','returncode','elapsed_seconds','cleanup_verified','peak_tree_rss_bytes')};out[name+'_supervision']['proof_pass']=v.get('cleanup_proof',{}).get('pass')
print(json.dumps(out,ensure_ascii=False))
