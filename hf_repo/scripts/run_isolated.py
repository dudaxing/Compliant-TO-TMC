"""Run the installed HF package under an auditable ban on source-workspace access.

This acceptance helper is not a runtime dependency. Invoke with isolated Python
(-I) in a clean environment from a cwd outside the copied repository.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.abc
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument("--dataset",required=True)
parser.add_argument("--output",required=True)
parser.add_argument("--forbid",action="append",required=True,
                    help="Original source root or file to forbid; supply at least one")
args=parser.parse_args()
if any(not value.strip() for value in args.forbid):
    parser.error("--forbid must name a nonempty original source path")
dataset=Path(args.dataset).resolve()
output=Path(args.output).resolve()
output.mkdir(parents=True,exist_ok=False)
forbidden=[os.path.normcase(os.path.abspath(p)) for p in args.forbid]
opened=set(); denied=[]; blocked_imports=[]

def within(path, parent):
    try:
        return os.path.commonpath((path,parent))==parent
    except ValueError:
        return False

def audit(event, arguments):
    if event not in {"open","os.listdir","os.scandir"} or not arguments:
        return
    candidate=arguments[0]
    if not isinstance(candidate,(str,bytes,os.PathLike)):
        return
    resolved=os.path.normcase(os.path.abspath(os.fsdecode(candidate)))
    if any(within(resolved,parent) for parent in forbidden):
        denied.append({"event":event,"path":resolved})
        raise PermissionError("Detached acceptance forbids access to source material")
    if event=="open":
        opened.add(resolved)

class NoLF(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0].casefold() in {"dmftd","mma","auto"}:
            blocked_imports.append(fullname)
            raise ImportError("LF package import is forbidden in detached acceptance")
        return None

sys.addaudithook(audit)
sys.meta_path.insert(0,NoLF())
start=time.perf_counter()
import numpy as np
import hf_eval
from hf_eval.evaluation import evaluate, inspect_geometry

index=json.loads((dataset/'dataset_index.json').read_text(encoding='utf-8'))
records=index['canonical_subset']
bycase={r['case_family']:r for r in records}
solver=dataset/index['solver_path']
reads={}
for record in records+index.get('synthetic_samples',[]):
    inspected=inspect_geometry(dataset/record['geometry_path'])
    reads[record['case_family']]=inspected
    assert inspected['readability']['status']=='pass', inspected

saved=[]
for name,case in [('A1','inverter'),('B','gripper'),('A2','inverter')]:
    record=bycase[case]
    result=evaluate(dataset/record['geometry_path'],dataset/record['task_path'],solver,output/name)
    assert result['numerics']['status']=='success', result
    assert result.get('visualization',{}).get('status')=='success', result
    saved.append(result)

with np.load(output/'A1/fields.npz',allow_pickle=False) as first, np.load(output/'A2/fields.npz',allow_pickle=False) as last:
    equal_arrays={name:bool(np.array_equal(first[name],last[name])) for name in first.files}
numeric_names=['q_in_mm','q_out_mm','R_in_N','output_load_N','strain_energy_N_mm',
               'spring_energy_N_mm','input_work_N_mm','relative_force_residual','constraint_error_mm']
equal_metrics={name:saved[0]['metrics_at_target'][name]==saved[2]['metrics_at_target'][name] for name in numeric_names}
installed={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
module_origins=sorted({str(getattr(module,'__file__')) for module in sys.modules.values() if getattr(module,'__file__',None)})
source_path_violations=[p for p in sys.path if any(within(os.path.normcase(os.path.abspath(p)),parent) for parent in forbidden)]
summary={
    'scope':'Detached HF-1 read/qualification/solid linear diagnostic; no LF or MATLAB',
    'python':sys.executable,'python_version':platform.python_version(),'cwd':os.getcwd(),
    'isolated_flag':sys.flags.isolated,'no_user_site_flag':sys.flags.no_user_site,
    'sys_path':sys.path,'hf_module':hf_eval.__file__,'installed_distributions':installed,
    'forbidden_source_roots_record_only':args.forbid,
    'checks':{
        'all_input_packages_readable':all(x['readability']['status']=='pass' for x in reads.values()),
        'all_three_analyses_success':all(x['numerics']['status']=='success' for x in saved),
        'A_B_A_all_arrays_bitwise_equal':all(equal_arrays.values()),
        'A_B_A_physical_metrics_equal':all(equal_metrics.values()),
        'unique_evaluation_ids':len({x['evaluation_id'] for x in saved})==3,
        'isolated_python':sys.flags.isolated==1 and sys.flags.no_user_site==1,
        'no_LF_installed':not any(name.casefold() in {'dmftd','mma','auto'} for name in installed),
        'no_forbidden_path_in_sys_path':not source_path_violations,
        'no_forbidden_file_access_attempt':not denied,
        'no_LF_import_attempt':not blocked_imports,
        'no_global_site_packages':not any('site-packages' in p.casefold() and not within(os.path.normcase(os.path.abspath(p)),os.path.normcase(sys.prefix)) for p in sys.path),
        'all_analysis_times_under_300s':all(x['metrics_at_target']['timing_seconds']['total']<300 for x in saved),
    },
    'inspections':reads,'A_B_A_array_comparison':equal_arrays,'A_B_A_metric_comparison':equal_metrics,
    'evaluation_ids':[x['evaluation_id'] for x in saved],
    'metrics_by_run':{name:result['metrics_at_target'] for name,result in zip(['A1','B','A2'],saved)},
    'wall_seconds':time.perf_counter()-start,
    'note':'Python audit hooks instrument this controlled run; this is not an operating-system sandbox.',
}
(output/'access_audit.json').write_text(json.dumps({'opened_paths':sorted(opened),'denied':denied,
    'blocked_imports':blocked_imports,'module_origins':module_origins},indent=2),encoding='utf-8')
(output/'acceptance.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({'checks':summary['checks'],'output':str(output),'wall_seconds':summary['wall_seconds']},indent=2))
raise SystemExit(0 if all(summary['checks'].values()) else 1)
