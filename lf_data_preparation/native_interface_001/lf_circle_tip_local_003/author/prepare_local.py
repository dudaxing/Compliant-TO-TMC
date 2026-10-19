"""Assemble ordinary preparation records; existing payload identities use seal/stat."""
from datetime import datetime, timezone
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_003'
SOURCE = 'lf_data_preparation/native_interface_001/lf_circle_tip_step_010'
BASE = '6e77bf0e874c939fee23158f57a2f87d662f8aaa'
CARD = 'L-CTIPLOCAL3'
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def read(name):
    return json.loads((ROOT/name).read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def main():
    assert subprocess.check_output(GIT+['rev-parse','HEAD'],cwd=ROOT).decode().strip() == BASE
    stage = ROOT/STAGE
    assert not stage.exists()
    assert not subprocess.check_output(GIT+['status','--porcelain'],cwd=ROOT).decode().strip()
    names = ('execute_local.py','observe_local.py','launch_local.py')
    support = ('prepare_local.py','close_local.py','publish_local.py','archive_publication.py')
    for name in names+support:
        raw = (AUTHOR/name).read_bytes()
        ast.parse(raw)
        assert all(row.rstrip(b' \t') == row for row in raw.splitlines()), name
    (AUTHOR/'execution_cwd').mkdir(exist_ok=False)
    (stage/'author').mkdir(parents=True)
    for name in names:
        (stage/name).write_bytes((AUTHOR/name).read_bytes())
    for name in ('prepare_local.py','close_local.py'):
        (stage/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    run = SOURCE+'/run_001/wave_circle_tip_step10'
    view = SOURCE+'/run_001/view/wave_circle_tip_step10'
    old = read(SOURCE+'/run_001/execution_receipt.json')
    result = read(run+'/result.json')
    assert old['status']=='pass' and result['status']=='success' and len(result['states'])==2
    assert [(s['d'],s['original_target_index']) for s in result['states']]==[(1.05,11),(1.06,12)]
    assert result['states'][1]['state_sha256']=='dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6'
    seals = old['outputs']

    def pin(name):
        seal = seals[name]
        assert (ROOT/name).stat().st_size == seal['bytes'], name
        return dict(path=name, **seal)

    observer = dict(model_npz=pin(run+'/model/model.npz'), model_descriptor_json=run+'/model/model.json',
        summary_json=view+'/summary.json', result_json=run+'/result.json', states=[],
        existing_links=dict(reaction=SOURCE+'/run_001/view/distances_forces.png',
            convergence=SOURCE+'/run_001/convergence/convergence.png'))
    ordinary = [run+'/model/model.json', run+'/result.json', view+'/summary.json', SOURCE+'/protocol.json',
        SOURCE+'/step_task.json', SOURCE+'/run_001/execution_receipt.json']
    for i, state in enumerate(result['states']):
        a = run+f'/accepted/{i:03d}'
        v = view+f'/{i:03d}'
        observer['states'].append(dict(accepted_index=i, global_index=state['original_target_index'],
            d_mm=state['d'], state_sha256=state['state_sha256'], state_npz=pin(a+'/state.npz'),
            forces_npz=pin(a+'/forces.npz'), state_descriptor_json=a+'/state.json',
            derived_json=v+'/derived.json', geometry_json=v+'/geometry.json'))
        ordinary += [a+'/state.json', v+'/derived.json', v+'/geometry.json']
    bindings = {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in ordinary}
    sources = [STAGE+'/'+name for name in names]+['hf_repo/scripts/windows_owned_process_sup2.py']
    source_bindings = {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in sources}
    old_protocol = read(SOURCE+'/protocol.json')
    protocol = dict(schema_version='lf-circle-tip-local-observation-1.0',card=CARD, source_baseline_commit=BASE,
        repository_root=str(ROOT), working_directory=str(AUTHOR/'execution_cwd'), output_directory=STAGE+'/run_001',
        helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=8*1024**3, cpu_thread_limit=16,
        cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        observer=observer,input_bindings=bindings,source_bindings=source_bindings,
        original_gates=old_protocol['gates'],original_settings=old_protocol['settings'],
        physical_task=read(SOURCE+'/step_task.json'),
        payload_scope=dict(archives=5,fields=12,model=['coordinates','connectivity','solid','workpiece_cells'],
            per_state_split=['lift','fluctuation'],per_state_forces=['J','Hu']),
        expected_outputs=['tip_closeup.png','medium_locations.png','localization.json','manual.html'],
        direct_user_request='批准按 L-CTIPLOCAL3 计划实施并执行',
        qualifications='Saved-state geometry and field localization only; original qualifications/history unchanged',
        stop_policy='Unique launch, first terminal error stops; no retry, repair rerun, extension, force, rollback or deletion',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(stage/'protocol.json',protocol)
    auth = dict(card=CARD,approval_card=CARD,authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=protocol['direct_user_request'],
        authorized_execution_source_commit=BASE,protocol_sha256=sha256((stage/'protocol.json').read_bytes()).hexdigest(),
        status='explicitly_approved',scope='One saved-array localization; 5NPZ/12fields,2PNG,JSON/manual HTML;180/240s,8GiB,16threads; records,main push and local Git restore')
    write(stage/'author/authorization.json',auth)
    (stage/'L-CTIPLOCAL3_CARD.md').write_bytes((AUTHOR/'L-CTIPLOCAL3_CARD.md').read_bytes())
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(source_bindings),ordinary_inputs=len(bindings),payload_preparation_reads=0,protocol_sha256=auth['protocol_sha256'])))


if __name__=='__main__':
    main()
