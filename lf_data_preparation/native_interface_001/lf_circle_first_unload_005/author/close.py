"""Close the bounded remaining circle return using ordinary records and seals."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_005'
BASE = '8a78fbf54fcd45640879ad357c880d12ee38aca9'
CARD = 'L-CUNLOAD5'
LABEL = 'wave_circle_unload0'
FRONTS = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md','docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']
PNG_NAMES = ['view/comparison.png','view/distances_forces.png','view/peak_fields.png','convergence/convergence.png']


def read(name, optional=False):
    path=ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def write(name, value):
    (ROOT/STAGE/name).write_text(value,encoding='utf-8',newline='\n')


def git_bytes(*args):
    return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*args],cwd=ROOT)


def shown(value):
    return '未提供' if value is None else str(value)


def main():
    protocol,launch=read('protocol.json'),read('unload_launch.json')
    receipt=read('run_001/execution_receipt.json',True)
    result=read('run_001/'+LABEL+'/result.json',True)
    response=read('run_001/'+LABEL+'/response.json',True)
    summary=read('run_001/view/'+LABEL+'/summary.json',True)
    view=read('run_001/view/view.json',True)
    convergence=read('run_001/convergence/convergence.json',True)
    pair=read('run_001/load_unload_pair.json',True)
    review,pixel=read('author/ACTUAL_REVIEW.json'),read('author/pixel_QA.json',True)
    task=json.loads((ROOT/protocol['task_file']).read_bytes())
    source_task=json.loads((ROOT/protocol['original_task_file']).read_bytes())
    parent=json.loads((ROOT/protocol['parent_result']).read_bytes())
    selected=parent['states'][protocol['selected_state_index']]
    assert launch['card']==protocol['card']==CARD and protocol['source_baseline_commit']==BASE
    assert launch['invocations']==1 and launch['status'] in ('pass','not_pass')
    assert launch.get('cleanup_verified') is True
    assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
    assert receipt is None or receipt['card']==CARD and receipt['status'] in ('pass','not_pass')
    assert receipt is None or receipt['protocol_sha256']==launch['protocol_sha256']
    assert task['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[71.,40.],radius_mm=9.,fixed_components=[0,1])
    assert task['path']==dict(kind='ordered_cycle',targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35,1.4,1.35,1.25,1.15,1.,.75,.5,.25,0.])
    unchanged=deepcopy(task)
    unchanged['path']['targets_mm']=unchanged['path']['targets_mm'][:-6]
    assert unchanged==source_task, 'Same-kind return only appends the six declared targets; all metadata remains exact'
    assert task['input']['target_mm']==1.4
    assert protocol['targets_mm']==[1.25,1.15,1.,.75,.5,.25,0.]
    assert protocol['selected_state_index']==1 and parent['status']=='success' and parent['path_completed']
    assert selected['original_target_index']==10 and selected['d']==1.25
    expected_settings=parent['settings'] | {'time_limit_seconds':5400.}
    assert parent['path_kind']=='ordered_cycle' and protocol['settings']==expected_settings
    assert protocol['cpu_thread_limit']==16 and protocol['sampled_RSS_bytes']==64*1024**3
    assert protocol['cpu_thread_environment']==dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16')
    assert not git_bytes('diff',BASE,'--name-only','--','hf_repo/src').strip()
    assert not git_bytes('status','--porcelain','--','hf_repo/src').strip()
    helper=receipt or {}
    outcome='pass' if launch['status']==helper.get('status')=='pass' else 'not_pass'
    assert review.get('execution_status',outcome)==outcome
    states=result.get('states') if result is not None else None
    observed={row['index']:row for row in summary['rows']} if summary is not None else {}
    rows=[]
    for index,state in enumerate(states or []):
        observation=observed.get(index)
        if observation is not None:
            assert (observation['state_sha256'],observation['d_mm'],observation['leg'],observation['original_target_index'])==(state['state_sha256'],state['d'],state['leg'],state['original_target_index'])
            assert observation['R_input_N']==state['R_input'] and observation['q_out_mm']==state['q_out']
        rows.append(dict(index=index,state_sha256=state['state_sha256'],d_mm=state['d'],R_input_N=state['R_input'],q_out_mm=state['q_out'],
            leg=state.get('leg'),original_target_index=state.get('original_target_index'),child_original_target_index=state.get('child_original_target_index'),
            is_original_target=state.get('is_original_target'),continuation_anchor=state.get('continuation_anchor'),
            workpiece=state.get('workpiece'),minimum_J=state.get('minimum_J'),relative_residual=state.get('relative_residual'),
            relative_global_force_balance=state.get('relative_global_force_balance'),constraint_residual_mm=state.get('constraint_residual'),
            constraint_bound_mm=state.get('constraint_bound'),view_observation=observation))
    cached=helper.get('cached_production_gates')
    continuation=result.get('continuation') if result is not None else None
    outputs=helper.get('outputs') or {}
    for name,seal in outputs.items():
        assert (ROOT/name).stat().st_size==seal['bytes'],name
    if outcome=='pass':
        assert result is not None and result['status']=='success' and result['path_completed'] and result['unload_endpoint_reached']
        assert result['path_kind']=='ordered_cycle' and result['targets_mm']==[1.25,1.15,1.,.75,.5,.25,0.] and result['reached_displacement']==0.
        assert result['loading_peak_reached'] is False
        assert result['settings']==expected_settings and cached is not None and cached['passed'] is True
        assert continuation['segment_completed'] and continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['continuation_mode']=='explicit_task_extension'
        assert 'task_transition' not in continuation
        assert continuation['parent_continuation']==parent['continuation']
        ancestor=continuation.get('parent_continuation')
        transitions=[]
        while isinstance(ancestor,dict):
            if 'task_transition' in ancestor:
                transitions.append(ancestor['task_transition'])
            ancestor=ancestor.get('parent_continuation')
        assert transitions==[dict(source_path_kind='load_only',extended_path_kind='ordered_cycle',first_unload=True,loading_peak_mm=1.4,first_unload_target_mm=1.35)]
        assert continuation['saved_matrix_or_force_or_tangent_read'] is False
        for part in (result,continuation):
            assert all(part[key] is False for key in ('task_target_executed','full_original_path_completed','full_extended_path_completed'))
            assert 'new_peak_reached' not in part and 'extended_segment_completed' not in part
        originals=[row for row in states if row['is_original_target']]
        assert [(r['original_target_index'],r['child_original_target_index'],r['d']) for r in originals]==[(10+i,i,d) for i,d in enumerate(protocol['targets_mm'])]
        assert states[0]['state_sha256']==selected['state_sha256'] and float(states[0]['R_input']).hex()==float(selected['R_input']).hex()
        assert states[0]['newton_checks']==1 and states[0]['assembler_force_call']==states[0]['assembler_tangent_call']==1
        assert helper.get('new_tests')==helper.get('default_installations')==helper.get('HP_calls_by_wrapper')==0
        assert result['call_counts']['HP_calls']==result['call_counts']['JIT_calls']==0
        assert response is not None and response['status']=='success' and response['target_response'] is None
        assert response['requested_endpoint_response']['d_mm']==protocol['targets_mm'][-1] and response['maximum_loading_stroke']['d_mm']==1.25
        assert summary is not None and len(summary['rows'])==len(states) and convergence is not None and pair is not None
        assert pixel is not None and pixel['card']==CARD and pixel['status'].startswith('pass') and pixel['inspections']==4
        expected={STAGE+'/run_001/'+name for name in PNG_NAMES}
        assert {row['path'] for row in pixel['media']}==expected
        assert all(name in outputs for name in expected)
        assert helper['output_identity_seal']=='complete_inside_original_helper_window'
    media={}
    for name in PNG_NAMES+['view/'+LABEL+'/actual_states.gif']:
        relative=STAGE+'/run_001/'+name
        if relative in outputs:
            media[name]=outputs[relative]
    last=rows[-1] if rows else None
    last_observation=last['view_observation'] if last is not None else None
    if outcome!='pass':
        next_step=('先依据实际停止phase、原API/显示错误及已保存partial定位问题；生产成功与显示失败分别记录。'
            '若平衡已完成则不重新求解，只为尚未完成的显示安排最小后续。无自动重试、修复重跑、延期或force。')
    elif last_observation is None or any(last_observation.get(k) is not False for k in ('boundary_intersects','raw_overlap','roundoff_ambiguous')):
        next_step=('先核对已保存的几何相交、重叠、数值不确定或缺项，再汇总输入回零结果；不把未提供观察解释为无接触或稳定。')
    else:
        next_step=('将本次回到0输入的末态与CPILOT原始0态分开列示，保留R、q_out、工件材料/Hu/总弱力、J/Hu及几何的真实微量；'
            '汇总圆形加载与分段回程的现有记录、可视化及未完成资格，再依据实际差异确定最小后续功能或参考工作。'
            '输入回到0不表示力或全部变形严格为0，也不证明自由释放、唯一性、稳定性、压力或有效夹持。')
    path_flags={key:result.get(key) for key in ('path_kind','targets_mm','reached_displacement','path_completed','loading_peak_reached','unload_endpoint_reached','task_target_executed','full_original_path_completed','full_extended_path_completed')} if result is not None else None
    closure=dict(card=CARD,status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,science_version='0.5.0',science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'],helper_status=helper.get('status'),outer_status=launch['status'],production_status=result.get('status') if result is not None else None,
        helper_phase=helper.get('phase'),helper_error=helper.get('error'),API_failure=helper.get('API_failure'),outer_stop_reason=launch.get('stop_reason'),
        saved_accepted_states=len(states) if states is not None else None,helper_on_accept_count=helper.get('accepted_states'),
        saved_count_basis='Actual len(result.states); null if result absent, not zero. Original bisection may add accepted states.',
        requested_endpoint_mm=protocol['targets_mm'][-1],input_return_zero_completed=bool(result is not None and result.get('status')=='success' and result.get('path_completed') and result.get('reached_displacement')==0.),
        controller_clock_only_change=dict(source_seconds=parent['settings']['time_limit_seconds'],new_seconds=protocol['settings']['time_limit_seconds']),
        path_flags=path_flags,continuation=continuation,original_gates=protocol['gates'],cached_production_gates=cached,
        source_parent=dict(result_file=protocol['parent_result'],selected_state_index=protocol['selected_state_index'],selected_original_target_index=selected['original_target_index'],selected_displacement_mm=selected['d'],state_sha256=selected['state_sha256'],parent_continuation=parent.get('continuation')),
        rows=rows,last_saved_state=last,load_unload_pair=pair,production_call_counts=result.get('call_counts') if result is not None else helper.get('production_call_counts'),
        wrapper_call_counts=helper.get('call_counts'),convergence_counts=convergence.get('counts') if convergence is not None else None,
        view_status=view.get('status') if view is not None else None,view_actual_counts=helper.get('view_actual_counts'),
        default_sources_unchanged=True,new_tests=helper.get('new_tests'),default_installations=helper.get('default_installations'),HP_calls_by_wrapper=helper.get('HP_calls_by_wrapper'),
        independent_reference=response.get('independent_reference') if response is not None else None,producer_flags=response.get('producer_flags') if response is not None else None,
        independent_reference_inheritance_scope='L-CREF1 covers only circle1.15/global5 and one PORT direction; source returned1.25/global10 and new returned states global11..16 have no fresh HP. Initial0/global0 and returned0/global16 are distinct saved states.',
        helper_elapsed_seconds=helper.get('elapsed_seconds'),outer_elapsed_seconds=launch.get('elapsed_seconds'),peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=launch.get('cleanup_verified'),
        cpu_thread_limit=protocol['cpu_thread_limit'],cpu_thread_environment=protocol['cpu_thread_environment'],
        cpu_configuration_scope='Thread environment cap/configuration, not measured use of16 cores; no affinity or GPU/backend change',viewer_internal_RSS_limit_bytes=helper.get('viewer_internal_RSS_limit_bytes'),
        resources={k:protocol[k] for k in ('controller_seconds','viewer_seconds','helper_seconds','outer_seconds','sampled_RSS_bytes')},
        sealed_output_files=len(outputs),sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),output_identity_seal=helper.get('output_identity_seal'),
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status') if pixel is not None else None,pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        available_sealed_visualizations=media,next_step=next_step,
        qualification_scope='Bounded saved circle remaining return1.25 to requested0 only; actual partial progress is recorded if unsuccessful. No original loading replay, full extended path, HP, pressure, effective grip, free release, stability, manufacturing or HF5 qualification.',
        closure_read_scope='Ordinary source/JSON/MD and original producer seals/stat only; no scientific/media read/hash/decode, mechanics, tests or rendering')
    lines=[f'# {CARD}：圆形固定工件1.25→0 mm剩余输入回程','',
        f'执行 **{outcome.upper()}**；生产 `{shown(closure["production_status"])}`、helper `{shown(helper.get("status"))}`／outer `{launch["status"]}`；停止阶段 `{shown(helper.get("phase"))}`。','',
        '整体目标是普通LF设计进入独立HF后的非线性加载、工件传力与卸载可检查。本轮从C4成功1.25 mm末态沿既有ordered_cycle入口，一次请求[1.25,1.15,1.00,0.75,0.50,0.25,0]，保留原数值状态与完整任务前缀；若未到0，仅报告实际最后接受位置与失败；通过实际变形、反力、工件力、距离和收敛与已有同值加载态比较。','',
        'r9 mm、圆心(71,40) mm工件固定ux/uy；其余E=1 MPa、nu=0.3、plane strain、厚20 mm、h=0.5 mm、gamma=1e-6、alpha=5e-7、Lr=80 mm及边界/平均端口不变。完整[0,0.25,0.5,0.75,1,1.15,1.25,1.35,1.40,1.35,1.25]前缀精确保留，kind维持ordered_cycle，仅追加[1.15,1.00,0.75,0.50,0.25,0]六目标；input峰值仍1.40，四说明字段及其他任务元数据原值不变。','',
        f'来源 `{protocol["parent_result"]}`，接受行1/global10/d1.25，state SHA `{selected["state_sha256"]}`。新子段原目标global10..16、本地0..6；fresh原锚使用原lift/fluctuation和带符号R，以新F/T复核原门，不读旧力/切线。默认生产源码零修改，测试/安装/HP均不新增。','',
        f'实际保存接受态 `{shown(closure["saved_accepted_states"])}`，回调计数 `{shown(helper.get("accepted_states"))}`。原二分可能产生额外接受态，不锁定N=7；缺结果保持None。路径原标志 `{shown(path_flags)}`。','',
        '|接受行|global目标|路段|d mm|输入R N|q_out mm|下半体总Fy N|边界距离 mm|solid minJ|free-medium minJ|relative residual|',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        observation=row['view_observation'] or {}
        force=(row.get('workpiece') or {}).get('force_on_lower_body_N',{}).get('total')
        values=[row['index'],row['original_target_index'],row['leg'],row['d_mm'],row['R_input_N'],row['q_out_mm'],force[1] if force is not None else None,observation.get('minimum_boundary_distance_mm'),observation.get('solid_min_J'),observation.get('medium_min_J'),row['relative_residual']]
        lines.append('|'+'|'.join(shown(value) for value in values)+'|')
    lines+=['',f'实际F/T与生产计数 `{shown(closure["production_call_counts"])}`；wrapper `{shown(helper.get("call_counts"))}`。原门 `{protocol["gates"]}`；缓存门 `{shown(cached)}`；收敛计数 `{shown(closure["convergence_counts"])}`。','',
        f'目标0的原始/返回普通对照原值 `{shown(pair)}`。它比较不同保存态，不把相同位移当作同一个数值解或参考资格。','',
        f'来源转换和状态身份 `{shown(continuation)}`。本次segment/path完成只表示原锚复核及该请求子段，成功才称输入到0；失败保留真实partial；task_target_executed/full_original_path_completed/full_extended_path_completed仍False。new_peak_reached与extended_segment_completed不新增；本层无task_transition，C3首次转换五键沿parent_continuation历史链保留。全任务峰值1.40不在本子段，loading_peak_reached为False；maximum_loading_stroke的1.25只表示子段锚点观察，不代表重做加载。零端点的R、q_out、弱力和变形均按真实值记录，不强制或裁成精确零。','',
        '×1实际变形和对称镜像示意保持区分；解析圆与选中Q1工件阶梯边界分别标示。q_out是平均端口位移，不是表面间隙；边界距离为无符号观察，tip距离是另一见证。圆周法向随位置变化，材料/Hu/总Fx/Fy是下半固定体弱式合力，不是连续压力或圆周总法向夹持力。','',
        '场图中cell mean J、Hu Frobenius与原九点Simpson min J、最大绝对Hu分量分别解释。包含关系/机构自重叠未完成；几何False、None和不确定观察不互换。固定工件的输入卸载不等于自由释放。','',
        f'末态已保存几何/分区场 `{shown(last_observation)}`。缺项不能解释为正间隙、无接触或稳定性。独立实际审阅 `{review["status"]}`；4PNG像素检查 `{shown(closure["pixel_QA_status"])}`。','']
    for name in media:
        lines += [f'![{name}](run_001/{name})','']
    lines += [f'资源：controller5400 s、共享显示600 s、helper6600 s、outer6660 s；采样内存上限64 GiB，实际树峰值 `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B，helper/outer耗时 `{shown(helper.get("elapsed_seconds"))}`／`{shown(launch.get("elapsed_seconds"))}` s。原SUP2清理 `{shown(launch.get("cleanup_verified"))}`。','',
        f'CPU线程环境 `{protocol["cpu_thread_environment"]}` 是16线程配置上限，不是实测使用16核。无affinity、GPU或数学后端更改；viewer内部内存门实录 `{shown(helper.get("viewer_internal_RSS_limit_bytes"))}` B。','',
        f'原窗口封存 `{len(outputs)}` 输出／`{closure["sealed_output_bytes"]}` B，状态 `{shown(helper.get("output_identity_seal"))}`。真实错误：helper `{shown(helper.get("error"))}`；API `{shown(helper.get("API_failure"))}`；outer `{shown(launch.get("error"))}`。生产成功和显示失败分别保留，不自动重跑。','',
        '本卡不授整条前缀从零执行、完整循环、独立HP、压力、有效夹持、自由释放、稳定性或HF5资格。CREF1只覆盖1.15/global5一个PORT方向；来源回程1.25及本次各新目标均无新HP；再次经过1.15或0不转授旧参考。S1失败、S2有限小模型PASS、C3/C4真实回程成功及全部旧证据原样保留。输入回到0不等于固定工件自由释放。','',
        '下一步：'+next_step,'']
    links=[('原响应','run_001/'+LABEL+'/response.json'),('原结果','run_001/'+LABEL+'/result.json'),('人工页','run_001/REVIEW.md'),('显示摘要','run_001/view/'+LABEL+'/summary.json'),('收敛','run_001/convergence/convergence.json'),('同值对照','run_001/load_unload_pair.json'),('helper','run_001/execution_receipt.json'),('outer','unload_launch.json'),('实际审阅','author/ACTUAL_REVIEW.md'),('闭卡','author/closure.json')]
    lines += ['审查入口：'+'、'.join(f'[{label}]({name})' for label,name in links if (ROOT/STAGE/name).is_file())+'。','']
    old_fronts={name:git_bytes('show',BASE+':'+name) for name in FRONTS}
    for name,old in old_fronts.items():
        assert (ROOT/name).read_bytes()==old,'Front already differs: '+name
    write('RESULTS.md','\n'.join(lines))
    write('NEXT_STEPS.md','# L-CUNLOAD5后续\n\n'+next_step+'\n\n下一阶段根据真实保存态和已核同值对照决定；本页不启动新目标、不授权新增资源，不例行补HP。原历史、未通过部分和资格边界保持。\n')
    write('author/closure.json',json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    history=dict(source_baseline_commit=BASE,files=[])
    for name,old in old_fronts.items():
        link=os.path.relpath(ROOT/STAGE/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix=(f'> 2026-10-18 L-CUNLOAD5 **{outcome.upper()}**：固定圆形工件从保存1.25 mm请求完成到0的剩余输入回程；生产 `{shown(closure["production_status"])}`，实际保存态 `{shown(closure["saved_accepted_states"])}`，原资格及历史保持。见[实际记录]({link})。原历史保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current=(ROOT/name).read_bytes()
        assert current.endswith(old) and current.count(old)==1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    write('author/front_history.json',json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='closed',execution_status=outcome,production_status=closure['production_status'],saved_accepted_states=closure['saved_accepted_states'],fronts=7),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
