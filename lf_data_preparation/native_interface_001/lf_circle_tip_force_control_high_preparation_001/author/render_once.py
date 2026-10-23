"""Bounded new preparation schematic, independent of any closed science window."""
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
assert not (HERE / 'SCHEMATIC_SUPERVISION.json').exists()
sys.path.insert(0, 'D:/hfr1_001')
from windows_owned_process_sup2 import run_owned
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg', OMP_NUM_THREADS='16',
           OPENBLAS_NUM_THREADS='16', MKL_NUM_THREADS='16', NUMEXPR_NUM_THREADS='16')
row = run_owned([sys.executable, '-X', 'utf8', '-B', str(HERE / 'draw_control_schematic.py')],
    cwd=str(HERE), env=env, log=HERE / 'schematic.log',
    deadline=time.monotonic()+60, seconds=60, rss_limit=1024**3,
    instance_log_path=HERE / 'schematic.instances.ndjson',
    instance_identity=dict(stage='L-CTIPFHIGHPREP1', phase='new_schematic_no_mechanics'))
(HERE / 'SCHEMATIC_SUPERVISION.json').write_bytes((json.dumps(row, indent=2)+'\n').encode())
print(json.dumps({key: row[key] for key in ('reason', 'returncode', 'cleanup_verified', 'elapsed_seconds', 'peak_tree_rss_bytes')}))
raise SystemExit(0 if row['reason']=='normal_exit' and row['returncode']==0 and row['cleanup_verified'] else 1)
