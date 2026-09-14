"""Sequential gate-bound replay of the remaining three frozen combinations."""
from pathlib import Path
import hashlib,json,subprocess

root=Path(__file__).resolve().parents[1]
out=root/'hf4_repair_results'
python=root/'hf_repo/.venv-hf2-repair/Scripts/python.exe'
assert json.loads((out/'stage3_gate.json').read_text())['status']=='pass'
frozen=json.loads((out/'source_paths_001/source_freeze.json').read_text())['files']
for gi,mi in ((0,0),(0,1),(1,0)):
    for name,expected in frozen.items():
        if name.startswith('src/hf_eval/'):
            assert hashlib.sha256((root/'hf_repo'/name).read_bytes()).hexdigest()==expected,name
    case=f'g{gi}_m{mi}_001'
    commands=[
        ('path',f'g{gi}_m{mi}_path',120,
         ['scripts/run_hf4_split_normal.py','--spec','configs/hf4/validation_spec.json',
          '--gamma-index',str(gi),'--mesh-index',str(mi),'--output',str(out/case)]),
        ('hp','other_hp',150,
         ['scripts/audit_hf4_split_normal.py','--spec','configs/hf4/validation_spec.json',
          '--source-freeze',str(out/'source_paths_001/source_freeze.json'),
          '--run',str(out/case),'--output',str(out/(case+'_audit'))])]
    for phase,category,limit,args in commands:
        command=[str(python),str(out/'run_budgeted.py'),'--name',case+'_'+phase,
                 '--category',category,'--limit',str(limit),'--',str(python),*args]
        result=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (out/(case+'_'+phase+'_launcher.log')).write_bytes(result.stdout)
        print(case,phase,'exit',result.returncode,flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
    summary=json.loads((out/(case+'_audit')/'summary.json').read_text())
    assert summary['status']=='pass' and summary['execution_scope']=='full_path'
print('All three remaining production paths and independent audits passed.',flush=True)
