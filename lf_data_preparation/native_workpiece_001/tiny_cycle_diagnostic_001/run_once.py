"""One tiny code-stage cycle diagnostic; persist failed or successful cache."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'hf_repo/src'))
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_mean import solve_native_mean,write_native_mean
HERE=Path(__file__).resolve().parent
task=json.loads((HERE/'task.json').read_text(encoding='utf-8'))
result=solve_native_mean(HERE/'inputs/geometry.json',task,task['path']['targets_mm'],
 settings=DisplacementSettings(minimum_increment=.0005/16,time_limit_seconds=15.))
path=write_native_mean(result,HERE/'result')
print(json.dumps(dict(diagnostic='captured',result_file=str(path),production_status=result.path['status'],
 failure=result.path['failure'],call_counts=result.metadata['call_counts'],accepted_states=len(result.accepted),
 accepted_d=[row.record['d'] for row in result.accepted],reached=result.path['reached_displacement'],
 path_timing=result.path['timing_seconds']),indent=2))

