"""Prepare one authorized circle saved-state reference, without reading payloads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_reference_001'
OLD='lf_data_preparation/native_interface_001/extension_reference_001'
PROD='lf_data_preparation/native_interface_001/lf_circle_step_002'
ORIGIN=PROD+'/run_001/wave_circle_step'
CPREP='lf_data_preparation/native_interface_001/lf_circle_input_preparation_001'
BASE='11a8b49ebef7d18fef17ffe6c9e365ce574de074'
REQUEST='好的，按你的建议先核对圆形工件1.15 mm峰值保存态的独立高精度参考，保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录和误差可视化，再根据结果安排后续加载。'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def write_new(name,value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as handle:
        if isinstance(value,str):handle.write(value)
        else:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    template=read(ROOT/OLD/'protocol.json')
    result=read(ROOT/ORIGIN/'result.json');model=read(ROOT/ORIGIN/'model/model.json')
    receipt=read(ROOT/PROD/'run_001/execution_receipt.json')
    task=read(ROOT/PROD/'step_task.json');row=result['states'][1]
    assert result['status']=='success' and receipt['status']=='pass'
    assert row['d']==1.15 and row['original_target_index']==5 and row['child_original_target_index']==1
    assert model['task']==task and task['path']['kind']=='load_only'
    refs=template['reference_sources']
    assert len(refs)==len({Path(name).name for name in refs})==11
    for name,digest in refs.items():assert pin(ROOT/name)==digest
    plot=OLD+'/plot_reference_observation.py'
    launcher=(ROOT/'lf_data_preparation/native_interface_001/lf_third_reference_001/launch_reference.py').read_text(encoding='utf-8')
    launcher=launcher.replace('L-TREF1','L-CREF1').replace('execute_partial_reference.py','execute_circle_reference.py')
    assert "summary['accepted_states'] == 2" in launcher and "summary['HP_calls_completed'] == 4" in launcher
    launcher=launcher.replace("summary['accepted_states'] == 2","summary['accepted_states'] == 1")
    launcher=launcher.replace("summary['HP_calls_completed'] == 4","summary['HP_calls_completed'] == 2")
    write_new('launch_reference.py',launcher)
    ordinary=[PROD+'/protocol.json',PROD+'/author/authorization.json',PROD+'/step_launch.json',
        PROD+'/run_001/execution_receipt.json',PROD+'/step_task.json',ORIGIN+'/result.json',ORIGIN+'/response.json',
        ORIGIN+'/model/model.json',ORIGIN+'/model/source_geometry/geometry.json',ORIGIN+'/'+row['descriptor_path'],
        CPREP+'/run_001/model/model.json',CPREP+'/run_001/execution_receipt.json']
    bindings={name:pin(ROOT/name) for name in ordinary}
    payload_names=[ORIGIN+'/model/model.npz']+[ORIGIN+'/'+row[key]['path'] for key in ('state','forces','tangents','matrix')]+[ORIGIN+'/model/source_geometry/geometry.npz']
    inherited=[]
    for name in payload_names:
        seal=receipt['outputs'][name]
        assert (ROOT/name).stat().st_size==seal['bytes']
        inherited.append(dict(path=name,**seal));bindings[name]=seal['sha256']
    bindings.update(refs)
    for name,digest in result['mechanics_source_sha256'].items():
        assert pin(ROOT/name)==digest;bindings[name]=digest
    bindings[plot]=pin(ROOT/plot)
    for name in ('execute_circle_reference.py','launch_reference.py'):
        ast.parse((AUTHOR/name).read_bytes());bindings[REL+'/'+name]=pin(AUTHOR/name)
    protocol=dict(schema_version='circle-saved-state-independent-reference-card-1.0',card='L-CREF1',
        prepared=True,authorized=False,executed=False,source_baseline_commit=BASE,science_version='0.5.0',
        reference_sources=deepcopy(refs),bindings=bindings,
        production_stage=PROD+'/run_001',production_result_dir='wave_circle_step',
        production_launch_file=PROD+'/step_launch.json',production_protocol_file=PROD+'/protocol.json',
        production_targets_mm=[1.,1.15],production_original_target_indices=[4,5],production_accepted_states=2,
        production_settings=deepcopy(result['settings']),producer_mechanics_source_sha256=deepcopy(result['mechanics_source_sha256']),
        task_file=PROD+'/step_task.json',task_sha256=result['task_sha256'],
        original_targets_mm=task['path']['targets_mm'],source_task_targets_mm=result['continuation']['source_task_targets_mm'],
        source_task_sha256=result['continuation']['source_task_sha256'],targets_mm=[1.15],original_target_indices=[5],
        execution_indices=[5],top_summary_child_indices=[1],selected_child_accepted_index=1,
        selected_state_sha256=row['state_sha256'],expected_accepted_states=1,expected_new_HP_calls=2,
        gates=deepcopy(template['gates']),grid=deepcopy(model['grid']),material=deepcopy(model['material']),
        workpiece=deepcopy(task['workpiece']),expected_counts=deepcopy(model['region_metadata']['counts']),
        direction=deepcopy(template['direction']),reference_output=REL+'/run_001/reference',plot_source=plot,
        circle_preparation_model_file=CPREP+'/run_001/model/model.json',
        circle_preparation_receipt_file=CPREP+'/run_001/execution_receipt.json',
        phases=dict(reference=dict(helper_seconds=900,outer_seconds=960)),sampled_RSS_bytes=8*1024**3,
        old_scientific_inputs=inherited,old_payload_preparation_scope='Producer seal plus stat only; no header/array read before authorized execution window.',
        decoder_scope='Five unique decoded NPZ plus source geometry raw identity; workpiece_checks rereads selected state/forces. Fifty-one descriptor fields, eighteen repeated appearances, plus CSC format/shape and optional _is_array probe.',
        source_archive_scope='Eleven unchanged dependencies with distinct basenames, plus this driver and unchanged pure plot; all original mathematics and denominators retained.',
        qualification_scope='Selected saved circular model numerical reference and one PORT direction only; no independent geometric mask, full child/path/all columns/stress-energy/pressure/effective grip/release/stability/HF5 qualification.',
        stop_policy='One invocation, first terminal error stops; actual partial retained with original-window seal only. No repair rerun/retry/extension/force or new production F/T/equilibrium/tests/API association/install.',
        plot_scope='One unchanged pure plot after reference gates pass, reading new ordinary summary only; one new PNG pixel inspection after terminal success, no redraw.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write_new('protocol.proposed.json',protocol)
    write_new('authorization.json',dict(card='L-CREF1',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=REQUEST,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_baseline_commit=BASE,helper_seconds=900,outer_seconds=960,sampled_RSS_bytes=8*1024**3,
        scope='Direct human approval of the published L-CREF1 next plan: selected circle1.15 peak HP80/120, original conditions/gates, error visualization, records and ordinary main publication/restore.',
        recorded_utc=datetime.now(timezone.utc).isoformat()))
    card='''# L-CREF1：圆形工件1.15 mm峰值保存态独立参考

2026-10-17 Asia/Seoul，用户直接授权按已发布L-CSTEP2/NEXT_STEPS计划执行。main基线11a8b49ebef7d18fef17ffe6c9e365ce574de074，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。此为准备/静审快照，尚未执行HP。

整体目标为普通LF几何进入独立HF的TMC前向力学，输出可比较的实际响应与接触相关量。HF不优化、不导入/安装/调用dmftd，MPM暂不实现。本阶段首次核圆形较强介质压缩新峰值的数值一致性，供下一加载决策；不重做已有平衡路径。

唯一来源为lf_circle_step_002/run_001/wave_circle_step/result.json中accepted1/global5/child1/loading1.15 mm，stateSHA3db267551ea6cb5817c2a1946a80363ecccb0329078d516e90e0106f27e709ef；不能误用其continuation里的1.00 mm祖锚。原子段[1,1.15]、完整任务前缀到1.15及原资格保持，未重新从零执行。

原r9/c(71,40) mm固定圆形、E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440单元/13689节点/27378DOF、fixed1272/free26106、gamma1e-6/alpha5e-7/Lr80mm、支撑/对称/平均端口、全部数值门保持。只读取保存模型与split及缓存，不新增生产F/T、构模、Newton、测试、安装或API关联。

独立数学原B850 Audit.run_state(5,row)与aa86 workpiece_checks字节不改；HP80/120各一次，覆盖全局/逐元材料/Hu/总力、同一PORT方向v=b_in/maxabs(b_in)且fixed0/deltaR0、精确Decimal3000 scatter/trap、CSC全系数组装身份、KKT和工件/支撑投影。不等于核全部切线列。新loader按圆形保存overlay与L-CPREP1普通模型证据核对，不继承旧square load()，不新增独立圆mask/边界资格。

原十五门及其分母/floor/局部规则/投影顺序原样保持：production residual1e-9、independent residual1e-8、force evaluation1e-9、constraint1e-10、balance1e-6、fixed8e-11mm、HP80/120一致1e-40；total/material/Hu force=1e-11/1e-9/1e-9，三切线方向=1e-10/1e-9/1e-9，KKT force/mean各1e-10。检查数量按实际原检查报告，不把十五类门当总检查数。stress/energy/独立Hu数组资格不增加。

六份原NPZ仅从producer seal+stat准备绑定：model、所选state/forces/tangents/CSC、source_geometry。前五份唯一解码；source_geometry只原字节身份。原workpiece方法重开state/forces，两次重复loader，不能混同unique数。51 descriptor字段+18重复出现，CSC另format/shape必需容器及原可选_is_array探针。十一数学依赖保持SHA且unique basename平铺归档；driver和纯plot另归档。原依赖会导入JAX/注册包装，不等于执行AD/JIT或生产力学。

全部通过后同一helper一次调用原pure误差plot，读本次accepted_005/summary.json，输出一张10项error/原limit的PNG及JSON，log10只作显示、原零误差保持零，无新floor/门。之后允许一次新PNG像素检查/展示，不重绘、不重读旧媒体；结构对照链接原S2实际图。

一次helper900秒/outer960秒（最多16分钟）、采样8GiB，含批准/来源核对、import、读数组、归档、2HP、全部比较、plot、完整输出seal及回执。launcher最早clock覆盖其preflight和最终输入身份SHA，helper独立900秒；合作stop/采样RSS不是OS硬上限，原HP内部无checkpoint时须等实际退出，迟到PASS不得通过。首错停止，无修复重跑、重试、延期、force或其它新科学；失败保真实partial与实际HP/plot计数，原窗口内可部分封存。

只授这一个保存圆形模型的数值参考/PORT方向，不授全部两态或完整路径参考、全列切线、连续压力、有效夹持、卸载/自由释放、稳定性、制造或HF5。legacy normal字段仅解释为全局Fy投影，不能当圆周局部法向压力或整圆总法向夹持力。原S2 response/results/flags不改。

包括实际结果、误差PNG、来源/资源回执、next决策记录和普通main提交推送及异目录恢复核对。若通过，再按实际误差/压缩/几何/成本提出下一加载目标；若失败，先解释实际错误，不静默重跑。具体protocol/授权/source静审同目录归档。
'''
    write_new('L-CREF1_CARD.md',card)
    write_new('preparation_receipt.json',dict(card='L-CREF1',status='prepared_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),bindings=len(bindings),reference_sources=len(refs),
        old_payloads_opened=0,old_inputs=inherited,HP_calls=0,production_calls=0,default_source_changes=0,
        external_files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in ('execute_circle_reference.py','launch_reference.py','protocol.proposed.json','L-CREF1_CARD.md','authorization.json')},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',bindings=len(bindings),reference_sources=len(refs),protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
