"""One shared 1200-second, at most three-source-version no-solve campaign.

First author review precedes --begin. Preparation, imports, tests, compilation,
references, figures and sealing are charged. A repair is a new attempt within
the SAME monotonic deadline and requires a recorded implementation-only reason.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import psutil
from windows_owned_process import run_owned

MANUFACTURED='hf4_c2_independent_recheck_20260927/manufactured_001/results'
SAVED='hf4_c2_stable_f_validation/saved_all_c2_001/driver_output'
CARD='docs/HF4_C2_NEAR_ROTATION_DIAGNOSTIC_20260928.md'
TESTS=('test_windows_owned_process.py','test_compensated_invariants.py',
       'test_split_kernel_invariants_hu.py')
HP={'hf2_precision_reference.py':'97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55',
    'hf4_split_precision_reference.py':'308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2'}
FATAL={'rss_limit','global_deadline','phase_timeout','supervision_error','cleanup_failure'}
_ACTIVE=None

def now(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False); f.write('\n')
def replace_json(p,v):
    temp=p.with_suffix('.new.json'); dump(temp,v); os.replace(temp,p)
def require(v,s):
    if not v: raise ValueError(s)

def long_path(path):
    value=str(Path(path).resolve())
    return Path('\\\\?\\'+value) if os.name=='nt' and not value.startswith('\\\\?\\') else Path(value)

def review_v1_destination_path_failure(campaign,ledger):
    """Narrow retrospective classification; preserve every v1 receipt byte."""
    prior=campaign/'version_001'
    require(len(ledger['attempts'])==1,'Only the recorded first preparation failure is covered')
    require([p['name'] for p in ledger['attempts'][0]['phases']]==['prepare','seal'],
            'Path repair cannot reinterpret a scientific failure')
    require(all(p['cleanup_verified'] for p in ledger['attempts'][0]['phases']),
            'Cannot repair failed process cleanup')
    require(read(prior/'source_preservation.json')['changes']==[],
            'Source changes terminate the campaign')
    log=(prior/'prepare.log').read_text(encoding='utf-8')
    require('FileNotFoundError' in log and 'shutil.copyfile(src,dest)' in log,
            'Failure is not the recorded destination copy defect')
    journal=[json.loads(line) for line in (prior/'preparation_bindings.jsonl').read_text(encoding='utf-8').splitlines()]
    row=journal[-1]
    require(row['status']=='before_copy' and len(str(prior/row['path']))>=260,
            'No MAX_PATH destination evidence')
    require(sha(row['source'])==row['sha256'] and not (prior/row['path']).exists(),
            'Failed copy source changed or destination exists')
    review={'original_status':ledger['status'],
        'reviewed_status':'implementation_failure','reason':'destination MAX_PATH copy defect; no source identity changed',
        'failed_binding':row,'destination_length':len(str(prior/row['path'])),
        'original_receipt_sha256':sha(prior/'execution_receipt.json'),
        'preservation_sha256':sha(prior/'source_preservation.json'),'reviewed_utc':now(),
        'deadline_unchanged':ledger['deadline_monotonic']}
    review_path=campaign/'classification_review_001.json'
    if review_path.exists():
        prior_review=read(review_path)
        require(prior_review['original_receipt_sha256']==review['original_receipt_sha256'] and
                prior_review['deadline_unchanged']==review['deadline_unchanged'],
                'Classification record changed')
    else: dump(review_path,review)

def source_files(repo):
    files=[]
    for part in ('src','scripts','tests'):
        files.extend(p for p in (repo/'hf_repo'/part).rglob('*.py') if '__pycache__' not in p.parts)
    files.extend([repo/'hf_repo/pyproject.toml',repo/CARD,
                  repo/'docs/HF4_C2_INVARIANTS_HU_ARITHMETIC.md'])
    return sorted(set(files))

def prepare(repo,baseline,root):
    records=[]
    def journal(row):
        with (root/'preparation_bindings.jsonl').open('a',encoding='utf-8') as handle:
            handle.write(json.dumps(row,ensure_ascii=False)+'\n'); handle.flush()
    def copy(src,dest,expected=None):
        src=src.resolve(); dest=root/dest
        digest=sha(src)
        journal({'path':dest.relative_to(root).as_posix(),'source':str(src),
                 'sha256':digest,'expected_sha256':expected,'status':'before_copy'})
        require(expected is None or digest==expected,'Input identity changed: '+str(src))
        if dest.exists():
            require(sha(dest)==digest,'Conflicting source '+str(dest)); return
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
        require(sha(dest)==digest,'Copy failed: '+str(dest))
        records.append({'path':dest.relative_to(root).as_posix(),'source':str(src),
            'bytes':dest.stat().st_size,'sha256':digest})
        journal({**records[-1],'status':'copied'})
    for p in source_files(repo): copy(p,'source/'+p.relative_to(repo).as_posix())
    for name,digest in HP.items():
        require(sha(root/'source/hf_repo/scripts'/name)==digest,'Independent HP source changed')
    mdir=repo/MANUFACTURED
    oldhash=read(mdir/'output_sha256.json')
    for name,digest in oldhash.items(): require(sha(mdir/name)==digest,'Old manufactured output changed: '+name)
    for p in mdir.rglob('*'):
        if p.is_file(): copy(p,'data/'+p.relative_to(repo).as_posix(),oldhash.get(p.relative_to(mdir).as_posix()))
    savedhash=read(repo/SAVED/'output_sha256.json')
    unused_assets=[]
    for name,digest in savedhash.items():
        p=repo/SAVED/name
        if not p.exists() and name.endswith('/production.npz'):
            unused_assets.append({'path':name,'sha256':digest,'reason':'archived legacy candidate arrays; not read by new validation'})
            continue
        require(sha(p)==digest,'Old saved output changed: '+name)
    dump(root/'unused_legacy_saved_arrays.json',unused_assets)
    for p in (repo/SAVED).rglob('*'):
        if p.is_file(): copy(p,'data/'+p.relative_to(repo).as_posix(),savedhash.get(p.relative_to(repo/SAVED).as_posix()))
    # Binding has its original historical namespace, separate from new source.
    bound=read(repo/SAVED/'saved_input_freeze.json')['files']
    for name,digest in bound.items():
        if name.startswith(('hf4_c1_results/','hf4_c2_diagnostics/','handoff/')):
            copy(baseline/name,'data/'+name,digest)
    manifest=read(baseline/'handoff/repository_manifest.json')['files']
    assets=read(baseline/'handoff/evidence_assets.json')['assets']
    bindings={row['path']:row['sha256'] for row in manifest}
    for asset in assets:
        if asset.get('mode')=='restore_relative_files':
            for row in asset['files']:
                require(row['path'] not in bindings or bindings[row['path']]==row['sha256'],
                        'Historical binding collision')
                bindings[row['path']]=row['sha256']
    # Completion/controller evidence supplements the old saved force freeze.
    runs=['hf4_c1_results/TMC_'+x+'_r2' for x in
          ('h025_uniform','h0125_uniform','h025_perturbation','h0125_perturbation')]
    runs += ['hf4_c2_diagnostics/experiments/'+x for x in
             ('mesh_h00625','outer_free','padding_2p5')]
    for run in runs:
        for p in (baseline/run).rglob('*'):
            if not p.is_file(): continue
            rel=p.relative_to(baseline).as_posix()
            # Include metadata/controllers and all recorded small records; state
            # NPZs already copied only when selected by original input freeze.
            if p.suffix in ('.json','.gz') or p.name in ('model.npz','controller.npz'):
                require(rel in bindings,'Unbound historical file: '+rel)
                copy(p,'data/'+rel,bindings[rel])
    dump(root/'input_manifest.json',{'schema':'invariants-hu-inputs-1','files':records})
    print(json.dumps({'prepared_files':len(records),'bytes':sum(r['bytes'] for r in records)}),flush=True)

def verify(root,manifest_hash=None):
    changes=[]
    if manifest_hash is not None and sha(root/'input_manifest.json')!=manifest_hash:
        return ['input_manifest.json changed']
    for row in read(root/'input_manifest.json')['files']:
        for location in (root/row['path'],Path(row['source'])):
            if not location.is_file() or sha(location)!=row['sha256']: changes.append(str(location))
    return changes

def seal(root):
    changes=verify(root)
    dump(root/'source_preservation.json',{'checked_utc':now(),'changes':changes,
        'pairs':len(read(root/'input_manifest.json')['files'])})
    if (root/'resources.json').exists():
        phases=read(root/'resources.json')['phases']
        width,height=900,100+55*len(phases)
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="14" fill="#152b43">',
             '<text x="24" y="30">Candidate campaign: completed phase resources (sampled RSS)</text>']
        for i,r in enumerate(phases):
            y=65+55*i
            svg += [f'<text x="24" y="{y}">{r["name"]}</text>',
                    f'<rect x="250" y="{y-14}" width="{500*min(r["elapsed_seconds"]/300,1):.2f}" height="12" fill="#277da1"/>',
                    f'<text x="250" y="{y+18}">{r["elapsed_seconds"]:.3f} s; peak {r["peak_tree_rss_bytes"]/1024**2:.1f} MiB; {r["reason"]}</text>']
        svg.append('</g></svg>')
        (root/'resources.svg').write_text('\n'.join(svg),encoding='utf-8')
    hashes={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()
            and p.name!='output_sha256.json' and p.name!='seal.log'}
    dump(root/'output_sha256.json',hashes)
    require(not changes,'Source changed during attempt')

def main():
    global _ACTIVE
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--begin',action='store_true')
    parser.add_argument('--repair-note')
    parser.add_argument('--worker',choices=('prepare','seal'))
    parser.add_argument('--root',type=Path)
    args=parser.parse_args()
    repo=args.repo.resolve(); campaign=args.campaign.resolve(); baseline=args.baseline.resolve()
    if args.worker:
        try:
            if args.worker=='prepare': prepare(repo,baseline,args.root.resolve())
            else: seal(args.root.resolve())
        except Exception:
            if args.worker=='prepare' and not (args.root/'input_manifest.json').exists():
                journal=args.root/'preparation_bindings.jsonl'
                rows=[json.loads(line) for line in journal.read_text(encoding='utf-8').splitlines()] if journal.exists() else []
                copied={r['path']:{k:v for k,v in r.items() if k!='status'} for r in rows if r['status']=='copied'}
                dump(args.root/'input_manifest.json',{'schema':'invariants-hu-inputs-1','partial_preparation':True,'files':list(copied.values())})
            traceback.print_exc(); return 3
        return 0
    if args.begin:
        require(not campaign.exists(),'Refuse to reset or overwrite an existing campaign')
        start=time.monotonic(); campaign.mkdir(parents=True)
        ledger={'schema':'invariants-hu-campaign-1','start_monotonic':start,
            'deadline_monotonic':start+1200.,'started_utc':now(),'boot_time':psutil.boot_time(),
            'seconds':1200,'rss_limit_bytes':8*1024**3,'phase_seconds':300,'max_versions':3,
            'card_sha256':sha(repo/CARD),'attempts':[],'status':'active'}
        dump(campaign/'ledger.json',ledger)
    else:
        ledger=read(campaign/'ledger.json')
        require(args.repair_note,'Record the implementation-only repair reason')
        if ledger['status']=='source_not_pass':
            review_v1_destination_path_failure(campaign,ledger)
        else:
            require(ledger['status']=='implementation_failure','Campaign cannot resume from this status')
    # psutil estimates Windows boot wall time from two separately sampled
    # clocks; exact float equality falsely rejects the same boot by ~1 ms.
    require(abs(ledger['boot_time']-psutil.boot_time())<1. and
            time.monotonic()>=ledger['start_monotonic'],
            'Boot/time-base changed; the monotonic window is invalid')
    require(sha(repo/CARD)==ledger['card_sha256'],'Approved card changed inside campaign')
    require(len(ledger['attempts'])<3,'Maximum frozen versions reached')
    require(time.monotonic()<ledger['deadline_monotonic']-20,'No time remains for another attempt')
    root=long_path(campaign/('version_%03d'%(len(ledger['attempts'])+1))); root.mkdir()
    attempt={'name':root.name,'started_utc':now(),'repair_note':args.repair_note,
        'phases':[],'status':'running','no_equilibrium_paths':True}
    ledger['attempts'].append(attempt)
    _ACTIVE=(campaign,root,ledger,attempt)
    replace_json(campaign/'ledger.json',ledger)
    dump(root/'plan.json',{'candidate':'p26_q1_split_invariants_hu_v1',
        'card_sha256':ledger['card_sha256'],'deadline_monotonic':ledger['deadline_monotonic'],
        'scientific_matrix':{'old_manufactured':33,'new_manufactured':36,'directions':138,'saved':63},
        'attempt':len(ledger['attempts']),'repair_note':args.repair_note,
        'source_tree':str(repo),'historical_evidence':str(baseline),'python':sys.version,
        'limits':{'seconds':1200,'phase_seconds':300,'rss_bytes':8*1024**3},
        'phase_order':['prepare','supervisor_tests','arithmetic_kernel_tests','closure',
                       'near_rotation','manufactured','new_fields','saved','plots','seal']})
    env=os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        PYTHONPATH=str(root/'source/hf_repo/src')+os.pathsep+str(root/'source/hf_repo/scripts'),
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLBACKEND='Agg',
        MPLCONFIGDIR=str(root/'matplotlib-cache'),JAX_ENABLE_X64='true')
    common=['--repo',str(repo),'--baseline',str(baseline),'--campaign',str(campaign),'--root',str(root)]
    manifest_hash=None
    def run(name,command):
        nonlocal manifest_hash
        print(json.dumps({'phase':name,'started_utc':now(),'remaining_seconds':ledger['deadline_monotonic']-time.monotonic()}),flush=True)
        r=run_owned(command,cwd=str(root),env=env,log=root/(name+'.log'),
            deadline=ledger['deadline_monotonic']-(5 if name=='seal' else 20),seconds=300)
        r['name']=name; attempt['phases'].append(r)
        replace_json(campaign/'ledger.json',ledger)
        print(json.dumps({'phase':name,'reason':r['reason'],'returncode':r['returncode'],
                          'elapsed_seconds':r['elapsed_seconds'],'peak_rss':r['peak_tree_rss_bytes']}),flush=True)
        if r['reason'] in FATAL: return 'resource_or_supervision_stop'
        if name=='prepare' and (root/'input_manifest.json').exists():
            manifest_hash=sha(root/'input_manifest.json')
        try:
            if name!='prepare' and verify(root,manifest_hash): return 'source_not_pass'
        except Exception as exc:
            r['verification_error']=repr(exc); return 'source_not_pass'
        if r['returncode']!=0:
            if name in ('prepare','seal'): return 'source_not_pass'
            statusfile=root/'results'/name/'summary.json'
            if statusfile.exists():
                status=read(statusfile).get('status')
                if status in ('reference_not_pass','source_not_pass','candidate_not_pass'): return status
            return 'implementation_failure'
        return 'pass'
    status=run('prepare',[sys.executable,'-B',str(Path(__file__).resolve()),*common,'--worker','prepare'])
    script=root/'source/hf_repo/scripts/validate_invariants_hu.py'
    if status=='pass':
        testroot=root/'source/hf_repo/tests'
        for phase,tests in (('supervisor_tests',TESTS[:1]),('arithmetic_kernel_tests',TESTS[1:])):
            status=run(phase,[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',
                *[str(testroot/t) for t in tests],'--junitxml='+str(root/(phase+'.xml'))])
            if status!='pass': break
    if status=='pass':
        for phase in ('closure','near_rotation','manufactured','new_fields','saved','plots'):
            if phase=='plots': dump(root/'resources.json',{'phases':attempt['phases']})
            status=run(phase,[sys.executable,'-B',str(script),'--root',str(root),'--phase',phase])
            if status!='pass': break
    attempt['status']=status
    if not (root/'resources.json').exists(): dump(root/'resources.json',{'phases':attempt['phases']})
    # Evidence finalization is charged. No numerical phase follows a failure.
    if (root/'input_manifest.json').exists() and time.monotonic()<ledger['deadline_monotonic']-8:
        sealstatus=run('seal',[sys.executable,'-B',str(root/'source/hf_repo/scripts/run_invariants_hu_campaign.py'),*common,'--worker','seal'])
        if sealstatus!='pass': status=sealstatus
    elif status=='pass': status='resource_or_supervision_stop'
    attempt.update(status=status,finished_utc=now(),
        elapsed_campaign_seconds=time.monotonic()-ledger['start_monotonic'])
    if time.monotonic()>ledger['deadline_monotonic']: status='resource_or_supervision_stop'
    ledger['status']=status; ledger['finished_utc']=now()
    ledger['elapsed_seconds']=time.monotonic()-ledger['start_monotonic']
    replace_json(campaign/'ledger.json',ledger)
    dump(root/'execution_receipt.json',attempt)
    dump(root/'receipt_binding.json',{'plan_sha256':sha(root/'plan.json'),
        'input_manifest_sha256':manifest_hash,'receipt_sha256':sha(root/'execution_receipt.json'),
        'output_manifest_sha256':sha(root/'output_sha256.json') if (root/'output_sha256.json').exists() else None,
        'sealed_utc':now(),'elapsed_campaign_seconds':time.monotonic()-ledger['start_monotonic']})
    _ACTIVE=None
    return 0 if status=='pass' else 1

if __name__=='__main__':
    try:
        result=main()
    except BaseException as exc:
        if _ACTIVE is not None:
            campaign,root,ledger,attempt=_ACTIVE
            attempt.update(status='supervisor_exception',finished_utc=now(),exception=repr(exc))
            ledger.update(status='supervisor_exception',finished_utc=now(),
                          elapsed_seconds=time.monotonic()-ledger['start_monotonic'])
            replace_json(campaign/'ledger.json',ledger)
            dump(root/'parent_exception.json',{'error':repr(exc),'traceback':traceback.format_exc(),
                'stopped_campaign':True,'scientific_children':'run_owned always performs finally cleanup'})
            if not (root/'execution_receipt.json').exists(): dump(root/'execution_receipt.json',attempt)
        traceback.print_exc(); result=2
    raise SystemExit(result)
