"""Assemble directly authorized saved-field localization; no payload opens."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
OLD = 'lf_data_preparation/native_interface_001/lf_circle_step_004'
REL = 'lf_data_preparation/native_interface_001/lf_circle_local_001'
PARENT = OLD+'/run_001/wave_circle_step'
BASE = 'e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6'
REQUEST = '好的，按你的建议开展 L-CLOCAL1，先定位圆形工件1.35 mm保存态的最小J、最大Hu与最近边界的空间关系，不新增平衡求解，保持原物理条件和验收门，注意做好记录和局部可视化，再根据结果决定是否推进到1.40 mm。'
read = lambda path: json.loads(path.read_bytes())
pin = lambda path: sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as stream:
        if isinstance(value,str):
            stream.write(value)
        else:
            json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
            stream.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    result_file = PARENT+'/result.json'
    result = read(ROOT/result_file)
    state = result['states'][1]
    assert result['status'] == 'success' and state['d'] == 1.35 and state['original_target_index'] == 7
    assert state['state_sha256'] == '0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455'
    model_descriptor = PARENT+'/'+result['model']['descriptor_path']
    model = read(ROOT/model_descriptor)
    assert model['quadrature'] == 'tensor_product_9_point_Simpson'
    assert model['task']['workpiece'] == dict(kind='fixed_rigid',shape='circle',center_mm=[71.,40.],radius_mm=9.,fixed_components=[0,1])
    model_file = (Path(model_descriptor).parent/model['arrays']['path']).as_posix()
    state_file,forces_file = [PARENT+'/'+state[name]['path'] for name in ('state','forces')]
    requested = [(model_file,model['arrays'],['coordinates','connectivity','solid','workpiece_cells']),
        (state_file,state['state'],['lift','fluctuation']),
        (forces_file,state['forces'],['J','Hu'])]
    seals = read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs = []
    for name,descriptor,fields in requested:
        seal = seals[name]
        assert seal['sha256'] == descriptor['sha256'] and (ROOT/name).stat().st_size == seal['bytes']
        old_inputs.append(dict(path=name,**seal,fields=fields,
            field_descriptors={key:descriptor['fields'][key] for key in fields}))
    assert old_inputs[-1]['field_descriptors']['J']['shape'] == [13440,9]
    assert old_inputs[-1]['field_descriptors']['Hu']['shape'] == [13440,2,2,2]
    ordinary = [result_file,model_descriptor,PARENT+'/'+state['descriptor_path'],
        OLD+'/run_001/view/wave_circle_step/001/geometry.json',
        OLD+'/run_001/view/wave_circle_step/001/derived.json',
        OLD+'/run_001/view/wave_circle_step/summary.json',OLD+'/protocol.json',OLD+'/NEXT_STEPS.md']
    inputs = {name:pin(ROOT/name) for name in ordinary}
    inputs.update({row['path']:row['sha256'] for row in old_inputs})
    source_names = ['hf_repo/scripts/windows_owned_process_sup2.py',
        'hf_repo/src/hf_eval/tmc_kernel.py','hf_repo/src/hf_eval/tmc.py',
        'hf_repo/src/hf_eval/native_project.py',
        'lf_data_preparation/native_interface_001/lf_circle_step_001/circle_saved_views.py']
    sources = {name:pin(ROOT/name) for name in source_names}
    for name in ('execute_local.py','launch_local.py'):
        ast.parse((AUTHOR/name).read_bytes())
        sources[REL+'/'+name] = pin(AUTHOR/name)
    cwd = AUTHOR/'execution_cwd'
    cwd.mkdir(exist_ok=False)
    protocol = dict(schema_version='lf-circle-saved-localization-card-1.0',card='L-CLOCAL1',
        source_baseline_commit=BASE,helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8*1024**3,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',
        model_file=model_file,state_file=state_file,forces_file=forces_file,
        model_descriptor_file=model_descriptor,selected_state_file=PARENT+'/'+state['descriptor_path'],
        production_result_file=result_file,geometry_observation_file=ordinary[3],derived_observation_file=ordinary[4],
        saved_summary_file=ordinary[5],source_protocol_file=OLD+'/protocol.json',
        selected_accepted_index=1,original_target_index=7,selected_state_sha256=state['state_sha256'],
        d_mm=1.35,local_bounds_mm=[58.,84.,25.,40.5],top_count=10,
        source_bindings=sources,input_bindings=inputs,old_scientific_inputs=old_inputs,
        archives_decoded=3,fields_decoded=8,original_gates=read(ROOT/OLD/'protocol.json')['gates'],
        original_physics=model['task'],original_production_settings=result['settings'],
        point_definition='J: original 9-point tensor Simpson, xi slow eta fast, BL BR TR TL Q1 interpolation. No Gauss substitution.',
        Hu_definition='Stored constant reference-displacement Hessian per element, shape(ne,2,2,2), no sampling-point axis; centre marker representative only. Maximum is abs component, not Frobenius norm.',
        ranking='J: ten smallest element/point pairs incl cutoff ties and all exact global-min ties; Hu: ten largest per-cell max-abs-component scores incl cutoff ties, retain all maximizing component ties.',
        approved_plan=dict(path=OLD+'/NEXT_STEPS.md',sha256=inputs[OLD+'/NEXT_STEPS.md']),
        qualification_scope='Localization of original saved fields only. No new F/T/HP/equilibrium/test, default HF change, pressure, effective grip, release, stability, full path, or HF5 qualification.',
        old_payload_preparation='Original S4 producer seal and stat only; no old scientific/media contents opened during preparation.',
        publication_policy='Ordinary main push and restore; per-command gc.auto=0 and maintenance.auto=false, no global Git configuration changes or automatic repack.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',protocol)
    write('authorization.json',dict(card='L-CLOCAL1',approval_card='L-CLOCAL1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        approved_plan=protocol['approved_plan'],semantic_correction='Before execution, source inspection corrected Gauss wording to Simpson and per-GP Hu wording to per-element constant Hu. Same intended localization, 3NPZ/8fields, physics, original gates and resources; communicated to human.',
        recorded_utc=datetime.now(timezone.utc).isoformat()))
    card=f'''# L-CLOCAL1：圆形工件1.35 mm保存态局部定位

2026-10-17 Asia/Seoul。用户已明确批准本阶段；main基线{BASE}，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。执行前准备快照。

整体目标为普通LF几何进入独立HF/TMC前向力学，逐步实现可检查的变形、传力与卸载。S4已达到1.35 mm并过原生产门，但free-medium minJ=0.08623624515762662、max_abs_Hu=0.41607250505717375/mm，最近unsigned边界距离0.09633236207295634 mm；最右尖端仍3.007572163198815 mm，Hu约占下半工件Fy的80.5%。本次回答这些场极值位于哪里，与最近梁段是否相关。

唯一状态为{result_file} accepted1/global7/loading1.35 mm，stateSHA {state['state_sha256']}。圆形半径9 mm、圆心(71,40) mm及全部原物理/设置/生产门不改；不重算锚点或加载路径，不新增F/T/HP/平衡/测试/默认HF改动或安装。

3份既存NPZ/8字段严格限定：model coordinates/connectivity/solid/workpiece_cells，state lift/fluctuation，forces J/Hu。准备只读普通描述和producer seal/stat；唯一helper窗口才校核归档SHA并解码上述字段，核原field dtype/shape/SHA，不读切线或其他归档。free-medium沿原S1 viewer的~solid并排除workpiece_cells，非按自由DOF猜测。

源核查修正上步术语：J为原九点Simpson（xi慢eta快，坐标-1/0/1），不是Gauss；原BL/BR/TR/TL Q1形函数将原采样点映射到参考/实际几何。重建points的字节SHA与model普通descriptor一致，无需解码第九字段。保存J/Hu不重算，实际坐标×1；Hu shape(ne,2,2,2)是单元常值参考位移Hessian，没有采样点轴，按element/component定位，单元中心仅代表标记，不能伪造唯一Hu采样点。

保全部精确minJ并列；J取十个最小element/point条目并保截断并列，Hu按每cell的max(abs8components)取十个最高cell并保截断并列及全部max component ties。使用原普通geometry/derived最近梁段和尖端见证，不新做边界搜索。仅计算位置/同单元或邻接关系；此关系非因果或接触判据。

输出两PNG：整体实际×1定位和工件下方梁段局部（视窗[58,84]×[25,40.5] mm，整体图必须完整显示全部极值）；标出J实际采样点、Hu相关单元/代表中心、最近边界见证和最右尖端。单元meanJ底色与sample minJ区分，Hu为maxabs分量而非Frobenius。另输出原值JSON/CSV与人工页；原minJ/maxHu摘要需精确对账，不新增生产阈值。成功后两新PNG各最多一次像素检查，不打开旧媒体。

一次helper180秒/outer240秒，采样8GiB，原SUP2 CPU-CLEAN1同实例终止/全部成员覆盖/句柄释放，固定5秒清理在outer内。一次启动、首错停止后续处理并保实际partial，仅原窗口仍开时允许一次partial seal；无重试、修复重跑、延期、force、回滚或删除。新输出在原helper窗口封存；结束后仅普通记录和producer seal/stat核对。

完成后依据实际空间定位决定后续是否考虑另段1.35→1.40 mm，本卡不执行1.40。原结果/资格保持，CREF1仍仅祖先1.15 mm参考；不授当前独立HP、压力、有效夹持、卸载/释放、稳定性、完整路径或HF5资格。包括结果记录、普通main推送与异目录恢复。发布命令临时关闭Git自动维护，避免重现S4额外打包开销；不改Git全局/仓库配置。
'''
    write('L-CLOCAL1_CARD.md',card)
    write('preparation_receipt.json',dict(card='L-CLOCAL1',status='prepared_authorized_not_executed',
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_baseline_commit=BASE,
        source_bindings=len(sources),input_bindings=len(inputs),scientific_invocations=0,
        old_payloads_opened=0,old_media_opened=0,
        files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in
            ('execute_local.py','launch_local.py','protocol.proposed.json','authorization.json','L-CLOCAL1_CARD.md')},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0)))


if __name__ == '__main__':
    main()
