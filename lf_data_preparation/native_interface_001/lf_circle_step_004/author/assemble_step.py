"""Assemble the authorized S4 metadata; ordinary records and old payload stat only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
OLD = 'lf_data_preparation/native_interface_001/lf_circle_step_003'
REL = 'lf_data_preparation/native_interface_001/lf_circle_step_004'
PARENT = OLD+'/run_001/wave_circle_step'
REF = 'lf_data_preparation/native_interface_001/lf_circle_reference_001'
BASE = 'df5398ba0903970e5f139d1679ee5f2cbc8f11d7'
REQUEST = '请继续进行下一步'
read = lambda p: json.loads(p.read_bytes())
pin = lambda p: sha256(p.read_bytes()).hexdigest()


def write(name, value):
    with (AUTHOR/name).open('x', encoding='utf-8', newline='\n') as handle:
        if isinstance(value, str):
            handle.write(value)
        else:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASE
    assert not subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip()
    assert not (ROOT/REL).exists()
    old = read(ROOT/OLD/'protocol.json')
    parent = read(ROOT/PARENT/'result.json')
    model_name = PARENT+'/'+parent['model']['descriptor_path']
    model = read(ROOT/model_name)
    original_task = OLD+'/step_task.json'
    assert model['task'] == read(ROOT/original_task)
    selected = parent['states'][1]
    reference = read(ROOT/REF/'run_001/reference/summary.json')
    assert parent['status'] == 'success' and parent['targets_mm'] == [1.15,1.25]
    assert selected['d'] == 1.25 and selected['original_target_index'] == 6
    assert selected['state_sha256'] == 'd5b74358bf076a7d858efd710e61cf31fa2f9ddb1648a7a488e2cbc299213fc5'
    assert reference['status'] == 'pass' and reference['HP_calls_completed'] == 2
    assert reference['states'][0]['state_sha256'] == parent['states'][0]['state_sha256']
    assert reference['states'][0]['state_sha256'] != selected['state_sha256']
    metadata = dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load135__L_CSTEP4',
        purpose='fixed_circle_LF_saved_load_only_step',
        parameter_origin='L-CSTEP4 direct continuation approval of published S3 plan: preserve full prefix through1.25 mm and append1.35 from accepted1/global6. CREF1 covers ancestor1.15 only.',
        description='Fixed circular half-workpiece; child revalidates1.25 mm and advances to1.35 mm. Complete task prefix inherited, not freshly executed.')
    task = deepcopy(model['task'])
    task.update(metadata)
    task['path']['targets_mm'].append(1.35)
    task['input']['target_mm'] = 1.35
    reversed_task = deepcopy(task)
    reversed_task.update({key:model['task'][key] for key in metadata})
    reversed_task['path']['targets_mm'].pop()
    reversed_task['input']['target_mm'] = 1.25
    assert reversed_task == model['task']
    write('step_task.json', task)
    sources = {name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    assert all(sources[name] == old['source_bindings'][name] for name in sources)
    for name in ('execute_step.py','launch_step.py'):
        ast.parse((AUTHOR/name).read_bytes())
        sources[REL+'/'+name] = pin(AUTHOR/name)
    for name in (old['viewer_source'], old['convergence_source']):
        sources[name] = pin(ROOT/name)
        assert sources[name] == old['source_bindings'][name]
    geometry = (Path(model_name).parent/model['source_geometry']['snapshot']['descriptor']).as_posix()
    geometry_payload = (Path(geometry).parent/read(ROOT/geometry)['arrays']['path']).as_posix()
    state_descriptor = PARENT+'/'+selected['descriptor_path']
    state_payload = PARENT+'/'+selected['state']['path']
    seals = read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    inherited = []
    for name in (geometry_payload, state_payload):
        seal = seals[name]
        assert (ROOT/name).stat().st_size == seal['bytes']
        inherited.append(dict(path=name, **seal))
    inputs = {name:pin(ROOT/name) for name in (PARENT+'/result.json',model_name,geometry,state_descriptor,
        original_task,OLD+'/protocol.json',REF+'/run_001/reference/summary.json')}
    inputs.update({row['path']:row['sha256'] for row in inherited})
    inputs[REL+'/step_task.json'] = pin(AUTHOR/'step_task.json')
    cwd = AUTHOR/'execution_cwd'
    cwd.mkdir(exist_ok=False)
    p = deepcopy(old)
    p.pop('existing_selected_reference', None)
    p.update(card='L-CSTEP4',source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_step',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task,task_file=REL+'/step_task.json',
        task_metadata=metadata,complete_task_targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35],targets_mm=[1.25,1.35],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in old['pure_view_bindings']},
        old_scientific_inputs=inherited,
        accepted_states_policy='Two requested child targets; original bounded bisections may add actual accepts.1.25 mm freshly revalidated; complete prefix not re-executed.',
        qualification_scope='Only1.25/1.35 child segment. CREF1 covers ancestor1.15 only; neither parent1.25 nor new1.35 has fresh HP. No full path, pressure, effective grip, unloading, release, stability, manufacturing or HF5 qualification.',
        approved_plan=dict(path=OLD+'/NEXT_STEPS.md',sha256=pin(ROOT/OLD/'NEXT_STEPS.md')),
        existing_ancestor_reference=dict(path=REF+'/run_001/reference/summary.json',selected_d_mm=1.15,global_target_index=5,
            state_sha256=reference['states'][0]['state_sha256'],scope='Ancestor1.15 saved model and one PORT direction only; ordinary evidence, not selected1.25/new1.35 qualification or continuation state.'),
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',p)
    write('authorization.json',dict(card='L-CSTEP4',approval_card='L-CSTEP4',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        resolved_request='Continue the immediately preceding final recommendation and published S3 NEXT_STEPS: installed load_only1.25→1.35 mm, unchanged physics/gates/settings/resources, actual saved-state visuals, records and ordinary main publication/restoration.',
        approved_plan=p['approved_plan'],authorized_execution_source_commit=BASE,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),recorded_utc=datetime.now(timezone.utc).isoformat()))
    card=f'''# L-CSTEP4：圆形工件1.25→1.35 mm保存态延伸

2026-10-17 Asia/Seoul。用户“请继续进行下一步”批准上一回复和已发布S3 NEXT_STEPS的明确建议。main基线{BASE}，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。本文件为执行前快照，尚未启动。

整体目标仍是普通LF几何进入独立HF/TMC非线性前向分析，逐步实现可检查的变形、作用力和卸载功能；HF不优化、不调用/安装dmftd，MPM暂不实现。S3新目标6检查/5线搜索全部接受/0失败二分，原门通过；min free-medium J=0.155533、unsigned最近边距0.163972 mm、最右尖端距3.104708 mm，Hu约占弱式工件Fy的81.3%。采用相同0.10 mm增量观察实际变化，不能预言接触或相同收敛成本。

父源{PARENT}/result.json accepted1/global6/1.25 mm，stateSHA {selected['state_sha256']}，R={selected['R_input']!r} N；parent.continuation.selected_state为祖先1.15，不能误选。新完整任务[0,.25,.5,.75,1,1.15,1.25,1.35]，inputpeak1.35，实际child[1.25,1.35]/global6,7/child0,1；只更新四说明字段、追加目标和峰值，其余任务精确保持。

圆形半径9 mm、圆心(71,40) mm固定ux/uy；E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440元素/27378DOF、gamma1e-6/alpha5e-7/Lr80mm及原支撑/对称/平均端口/mechanical/chunk256/port_projection保持。settings和原门精确继承，minimum_increment=.00625、max_bisections4、controller1800秒。默认HF源码和绘图实现不改，无新测试、HP或安装。

一次evaluate_native(None,newtask,newout,...saved_result=父result,selected_state_index=1,extend_path=True)，以fresh F/T先复核1.25 mm原lift/fluctuation、带符号R、原门及SHA/R身份，第一检查须接受，不复用旧力/T/矩阵，再求1.35。保relative residual1e-9、逐态constraint_bound系数1e-10、globalbalance1e-6、fixed fsum8e-11 mm和全部GP J>0；原内部回溯/二分允许，保全部实际接受态，不锁定仅两态。

成功后复用S1纯viewer和收敛投影，一次新进程生成4PNG、实际N帧GIF、逐态表和人工页，显示×1变形/全结构视觉镜像、R/qout、工件有符号材料/Hu/总Fx/Fy、unsigned最近梁段/尖端距离、分区J/Green/Hu、残差/约束界/线搜索/二分。镜像不加倍数值，qout非表面间隙；圆周法向变化，全局弱式Fy非圆周压力或有效夹持力。保原图例标题轻微重叠注记，不修图重绘。

旧科学输入仅父geometry.npz和selected001 split state.npz；准备只继承producer seal/stat，helper唯一窗口才打开。CREF1普通summary仅属祖先1.15参考，不是parent1.25或新态资格，不读其gzip/NPZ/媒体。viewer为原五源，解码1+2N新NPZ/27+18N字段，无切线解码；原helper窗口封存新输出，成功后四新PNG各最多一次像素检查，不另解码GIF。

一次controller1800/共享显示600/helper2700/outer2760秒（最多46分钟），采样8GiB。共享显示含binding/viewer/收敛/表/页，seal仍限helper。原SUP2 CPU-CLEAN1同实例终止、全成员覆盖、句柄释放及固定5秒清理在outer内保持。唯一启动，首个终端错误停止后续科学/显示并保真实partial；仅原窗口仍开时允许部分seal。无外部重试、修复重跑、延期、force、回滚或删除。

new_peak_reached/extended_segment_completed仅本子段；task_target/full_original/full_extended仍False、target_response=None，requested_endpoint_response为新1.35。未授全前缀重算、独立HP/全列切线、独立圆mask、压力/有效夹持/卸载/释放/稳定性/制造/HF5资格。包含实际记录、图表、资源/清理回执、后续决策、普通main推送及异目录恢复核对。首错如实闭卡，不静默改门或物理条件；下一步根据本次实际证据再定。
'''
    write('L-CSTEP4_CARD.md',card)
    write('preparation_receipt.json',dict(card='L-CSTEP4',status='prepared_authorized_not_executed',
        source_baseline_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0,scientific_invocations=0,
        files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in
            ('execute_step.py','launch_step.py','protocol.proposed.json','step_task.json','authorization.json','L-CSTEP4_CARD.md')},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs))))


if __name__=='__main__':
    main()
