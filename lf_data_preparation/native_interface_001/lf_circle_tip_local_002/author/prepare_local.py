"""Assemble ordinary preparation records; existing payload identities use seal/stat."""
from datetime import datetime, timezone
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_002'
SOURCE = 'lf_data_preparation/native_interface_001/lf_circle_tip_step_008'
OLDLOC = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_001'
BASE = '261bc7be72211b428a6d1eaa6aa2b733f894b837'
CARD = 'L-CTIPLOCAL2'
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def read(name):
    return json.loads((ROOT/name).read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def main():
    assert subprocess.check_output(GIT+['rev-parse','HEAD'],cwd=ROOT).decode().strip() == BASE
    stage = ROOT/STAGE
    assert not stage.exists()
    names = ('execute_local.py','render_local.py','launch_local.py')
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
    run = SOURCE+'/run_001/wave_circle_tip_step8'
    view = SOURCE+'/run_001/view/wave_circle_tip_step8'
    old = read(SOURCE+'/run_001/execution_receipt.json')
    result = read(run+'/result.json')
    assert old['status']=='pass' and result['status']=='success' and len(result['states'])==2
    seals = old['outputs']

    def pin(name):
        seal = seals[name]
        assert (ROOT/name).stat().st_size == seal['bytes'], name
        return dict(path=name, **seal)

    observer = dict(model_npz=pin(run+'/model/model.npz'), model_descriptor_json=run+'/model/model.json',
        summary_json=view+'/summary.json', result_json=run+'/result.json', states=[],
        localization_json=OLDLOC+'/run_001/localization.json', field_ranges_json=OLDLOC+'/run_001/execution_receipt.json',
        existing_links=dict(tip=OLDLOC+'/run_001/tip_closeup.png', reaction=SOURCE+'/run_001/view/distances_forces.png',
            convergence=SOURCE+'/run_001/convergence/convergence.png'))
    ordinary = [run+'/model/model.json', run+'/result.json', view+'/summary.json', SOURCE+'/protocol.json',
        SOURCE+'/step_task.json', SOURCE+'/run_001/execution_receipt.json',
        OLDLOC+'/run_001/localization.json', OLDLOC+'/run_001/execution_receipt.json',
        OLDLOC+'/author/pixel_QA.json', OLDLOC+'/protocol.json']
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
        expected_outputs=['medium_locations.png','render.json','manual.html'],
        direct_user_request='批准按 L-CTIPLOCAL2 计划实施并执行',
        qualifications='Saved-state geometry and field localization only; original qualifications/history unchanged',
        stop_policy='Unique launch, first terminal error stops; no retry, repair rerun, extension, force, rollback or deletion',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(stage/'protocol.json',protocol)
    auth = dict(card=CARD,approval_card=CARD,authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=protocol['direct_user_request'],
        authorized_execution_source_commit=BASE,protocol_sha256=sha256((stage/'protocol.json').read_bytes()).hexdigest(),
        status='explicitly_approved',scope='One saved-array localization; 5NPZ/12fields,1PNG,render JSON/manual HTML;180/240s,8GiB,16threads; records,main push and local Git restore')
    write(stage/'author/authorization.json',auth)
    card = '# L-CTIPLOCAL2：补齐介质定位图排版\n\n用户已明确批准本卡实施及执行。整体目标是独立可恢复的TMC大变形分析；LOCAL1已完成1.03/1.04 mm两态的数值定位与尖端近景，但介质图顶部标题重叠。本卡仅修复该显示缺口，保留原LOCAL1执行PASS/视觉NOT_PASS历史。\n\n保持r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm和其它物理、设置及原门。复用同两态，原J/Hu、Q1坐标、全部9861非工件介质、见证并列语义、地图范围与色标不变。新候选仅修medium图rect高度为.85（bottom .075，top .925）和suptitle y=.985；新图实际效果仍需一次像素检查。\n\n唯一启动，helper180秒/outer240秒，采样8GiB、四库线程上限16。5NPZ/12字段限于model coordinates/connectivity/solid/workpiece_cells；两态各lift/fluctuation/J/Hu，各原NPZ在窗口内一次hash与选定字段解码。读取原LOCAL1普通定位/producer回执，精确核对位置、值、共同视野与色标；差异保留并停止，不改门或裁剪数据。\n\n只生成1张新medium_locations.png、render.json与manual.html。已通过tip图仅链接，不重开或重绘旧媒体，不生成第二张PNG或GIF。首个终端错误停止，无重试、修复重跑、延期、force、回滚或删除；无新测试、构模、F/T/HP/Newton/平衡求解、默认HF改动或安装。含记录、main普通推送和同机异目录local Git恢复核对。\n\n通过新图才补足视觉缺口，不改写旧失败。根据真实结果另行决定是否准备1.04→1.05 mm；不自动加载，不升级压力、有效夹持、完整路径、释放、稳定性、网格/域宽或HF5资格。\n'
    (stage/'L-CTIPLOCAL2_CARD.md').write_text(card,encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(source_bindings),ordinary_inputs=len(bindings),payload_preparation_reads=0,protocol_sha256=auth['protocol_sha256'])))


if __name__=='__main__':
    main()
