"""Detached installed-wheel acceptance, without source-workspace/LF/MATLAB access."""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.abc
import importlib.metadata
import importlib.util
import json
import os
import sys
from time import perf_counter

parser=argparse.ArgumentParser()
parser.add_argument('--repository',required=True)
parser.add_argument('--dataset',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--forbid',action='append',required=True)
args=parser.parse_args()
if any(not p.strip() for p in args.forbid):
    parser.error('At least one nonempty original source path must be forbidden')
repository=Path(args.repository).resolve()
dataset=Path(args.dataset).resolve()
output=Path(args.output).resolve()
output.mkdir(parents=True,exist_ok=False)
forbidden=[os.path.normcase(os.path.abspath(p)) for p in args.forbid]
opened=set();denied=[];blocked=[]
def within(path,parent):
    try:
        return os.path.commonpath([path,parent])==parent
    except ValueError:
        return False
def audit(event,arguments):
    if event not in {'open','os.listdir','os.scandir'} or not arguments:
        return
    candidate=arguments[0]
    if not isinstance(candidate,(str,bytes,os.PathLike)):
        return
    path=os.path.normcase(os.path.abspath(os.fsdecode(candidate)))
    if any(within(path,parent) for parent in forbidden):
        denied.append({'event':event,'path':path})
        raise PermissionError('Detached HF-2 forbids original source access')
    if event=='open':
        opened.add(path)
class BlockReferenceImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0].casefold() in {'dmftd','mma','auto','matlab'}:
            blocked.append(fullname)
            raise ImportError('LF/MATLAB import forbidden in detached HF acceptance')
sys.addaudithook(audit)
sys.meta_path.insert(0,BlockReferenceImports())
start=perf_counter()
import numpy as np
import jax
import hf_eval
from hf_eval.evaluation import evaluate,implementation_hash
from hf_eval.tmc import rectangular_model,solve_path
from hf_eval.tmc_benchmark import validate_source_setup

spec=importlib.util.spec_from_file_location('portable_hf2_validation',repository/'scripts/validate_hf2.py')
validation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)
small=validation.run_validation(repository/'tests/fixtures/hf2',repository/'validation/hf2/validation_spec.json',output/'small')
targets=validate_source_setup(repository/'validation/hf2/reference/cshape_setup.npz')
index=json.loads((dataset/'dataset_index.json').read_text(encoding='utf-8'))
records={r['case_family']:r for r in index['canonical_subset']}
linear=[]
for name,case in [('A1','inverter'),('B','gripper'),('A2','inverter')]:
    record=records[case]
    result=evaluate(dataset/record['geometry_path'],dataset/record['task_path'],dataset/index['solver_path'],output/name)
    linear.append(result)
with np.load(output/'A1/fields.npz',allow_pickle=False) as first, np.load(output/'A2/fields.npz',allow_pickle=False) as last:
    linear_equal={name:bool(np.array_equal(first[name],last[name])) for name in first.files}
model=rectangular_model(2,1,2,1,fixed_dofs=[0,1,6,7])
force=np.zeros(model.ndof);force[[5,11]]=-.1
a=solve_path(model,force,[.01,.02])
b=solve_path(model,2*force,[.02])
a2=solve_path(model,force,[.01,.02])
installed={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
record_files=0
record_failures=[]
for distribution in importlib.metadata.distributions():
    for entry in distribution.files or []:
        if entry.hash is None:
            continue
        with distribution.locate_file(entry).open('rb') as stream:
            digest=hashlib.file_digest(stream,entry.hash.mode).digest()
        actual=base64.urlsafe_b64encode(digest).decode().rstrip('=')
        record_files+=1
        if actual!=entry.hash.value:
            record_failures.append(str(entry))
checks={
    'small_reference_all_checks_pass':small['status']=='pass',
    'source_setup_matches_independent_preset':len(targets)==100 and targets[-1]==1,
    'HF1_three_linear_analyses_succeed':all(r['numerics']['status']=='success' for r in linear),
    'HF1_A_B_A_all_arrays_bitwise_equal':all(linear_equal.values()),
    'HF1_fresh_evaluation_ids':len({r['evaluation_id'] for r in linear})==3,
    'TMC_small_three_paths_succeed':all(r['status']=='success' for r in [a,b,a2]),
    'TMC_A_B_A_displacement_bitwise_equal':bool(np.array_equal(a['u'],a2['u'])),
    'TMC_different_load_changes_result':not np.array_equal(a['u'],b['u']),
    'isolated_python':bool(sys.flags.isolated and sys.flags.no_user_site),
    'CPU_float64':jax.default_backend()=='cpu' and bool(jax.config.read('jax_enable_x64')),
    'no_forbidden_path_in_sys_path':not any(any(within(os.path.normcase(os.path.abspath(p)),f) for f in forbidden) for p in sys.path),
    'no_global_site_packages':not any('site-packages' in p and not within(os.path.normcase(os.path.abspath(p)),os.path.normcase(sys.prefix)) for p in sys.path),
    'no_source_file_access_attempt':not denied,
    'no_LF_MATLAB_import_attempt':not blocked,
    'no_LF_MATLAB_installed':not any(n.casefold() in {'dmftd','mma','auto','matlab','matlabengine'} for n in installed),
    'installed_hf_module': 'site-packages' in hf_eval.__file__,
    'installed_distribution_RECORD_hashes_match':not record_failures and record_files>0,
}
checks={key:bool(value) for key,value in checks.items()}
summary={'status':'pass' if all(checks.values()) else 'fail','scope':'installed HF-2 small reference replay and HF1/TMC A-B-A; no full Cshape rerun',
         'checks':checks,'small_checks':len(small['checks']),'small_cases':small['completed_cases'],
         'source_sha256':implementation_hash(),'python':sys.executable,'sys_path':sys.path,
         'installed_distributions':installed,'hf_module':hf_eval.__file__,'wall_seconds':perf_counter()-start,
         'linear_array_comparisons':linear_equal,'installed_record_files_checked':record_files,
         'installed_record_failures':record_failures}
(output/'acceptance.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(output/'access_audit.json').write_text(json.dumps({'opened_paths':sorted(opened),'denied':denied,'blocked_imports':blocked,
    'forbidden_paths_record_only':args.forbid,'method':'Python-level audit, not OS sandbox'},indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['status']=='pass' else 2)
