"""One bounded data-free schematic rendering for the newly authorized preparation."""
import json
import os
from pathlib import Path
import sys
import time
HERE=Path(__file__).resolve().parent
assert not (HERE/'SCHEMATIC_SUPERVISION.json').exists()
sys.path.insert(0,'D:/hfl1_001')
from windows_owned_process_sup2 import run_owned
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg',OMP_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',MKL_NUM_THREADS='16',NUMEXPR_NUM_THREADS='16')
row=run_owned([sys.executable,'-X','utf8','-B',str(HERE/'draw_control_schematic.py')],
    cwd=str(HERE),env=env,log=HERE/'schematic.log',deadline=time.monotonic()+60,seconds=60,
    rss_limit=1024**3,instance_log_path=HERE/'schematic.instances.ndjson',
    instance_identity=dict(stage='L-CTIPFREALPREP1',phase='schematic_only_no_mechanics'))
(HERE/'SCHEMATIC_SUPERVISION.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:row[k] for k in ('reason','returncode','cleanup_verified','elapsed_seconds','peak_tree_rss_bytes')}))
raise SystemExit(0 if row['reason']=='normal_exit' and row['returncode']==0 and row['cleanup_verified'] else 1)
