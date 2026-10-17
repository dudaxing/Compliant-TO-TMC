"""Close localization from ordinary records and producer seals, no array/media reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import os
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_local_001'
BASE='e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6'
FRONTS=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
    'docs/RESUME_DEVELOPMENT.md','docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name):
    file=STAGE/name
    return json.loads(file.read_bytes()) if file.is_file() else None


def write(name,value):
    (STAGE/name).write_text(value,encoding='utf-8',newline='\n')


def main():
    protocol,launch,helper,summary,review,pixel=[read(name) for name in
        ('protocol.json','local_launch.json','run_001/execution_receipt.json','run_001/summary.json',
         'author/ACTUAL_REVIEW.json','author/pixel_QA.json')]
    assert review['status'].startswith('pass') and not review.get('blockers',review.get('blocking_findings',[]))
    helper=helper or {}
    assert launch['card']==protocol['card']=='L-CLOCAL1'
    assert launch['invocations']==1 and launch['status'] in ('pass','not_pass')
    assert launch['cleanup_verified'] is True
    outcome='pass' if launch['status']==helper.get('status')=='pass' else 'not_pass'
    assert review.get('execution_status',outcome)==outcome
    assert not subprocess.check_output(['git','diff',BASE,'--name-only','--','hf_repo/src'],cwd=ROOT)
    if outcome=='pass':
        assert helper['archives_decoded']==3 and helper['fields_decoded']==8
        assert helper['call_counts']['plots_completed']==2
        assert all(summary['source_scalar_exact_matches'].values())
        assert pixel and pixel['status'].startswith('pass')
    seals=helper.get('outputs') or {}
    for name,row in seals.items():
        assert (ROOT/name).stat().st_size==row['bytes'],name
    next_step=('根据本次实际极值位置、原见证和连接关系解释局部压缩；原值/分区/位置解释相容后才考虑另段1.35→1.40 mm。'
        '本次不执行新加载，不把正常收敛、几何邻接或含Hu的弱式合力认定为压力/有效夹持。')
    closure=dict(card='L-CLOCAL1',status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        source_baseline_commit=BASE,science_version='0.5.0',science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'],terminal=review.get('terminal'),
        helper_status=helper.get('status'),outer_status=launch['status'],helper_error=helper.get('error'),
        output_identity_seal=helper.get('output_identity_seal'),sealed_files=len(seals),
        sealed_bytes=sum(row['bytes'] for row in seals.values()),
        archives_decoded=helper.get('archives_decoded'),fields_decoded=helper.get('fields_decoded'),
        call_counts=helper.get('call_counts'),helper_elapsed_seconds=helper.get('elapsed_seconds'),
        outer_elapsed_seconds=launch.get('elapsed_seconds'),peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch['cleanup_verified'],observed_saved_fields=summary,
        original_gates=protocol['original_gates'],original_production_settings=protocol['original_production_settings'],
        selected_state_sha256=protocol['selected_state_sha256'],original_results_changed=False,default_HF_sources_changed=False,
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status') if pixel else None,
        qualification_scope=protocol['qualification_scope'],semantic_correction='J: nine-point Simpson. Hu: cellwise constant reference Hessian, no sample axis; center representative only.',
        closure_read_scope='Ordinary records and original producer seals/stat only; no NPZ/media hash, decode or new FE evaluation.',
        next_step=next_step,created_utc=datetime.now(timezone.utc).isoformat())
    lines=['# L-CLOCAL1：圆形工件1.35 mm保存场空间定位','',
        f'执行 **{outcome.upper()}**；helper `{helper.get("status")}`／outer `{launch["status"]}`。原S4生产成功记录保持。','',
        '整体目标为普通LF几何进入独立HF/TMC前向分析，逐步实现可检查的加载、传力、夹持相关响应和卸载。本次只定位已保存的J/Hu极值和最近边界关系，用于判断更强介质压缩发生在哪里；不重算平衡路径。','',
        '保持圆形半径9 mm、圆心(71,40) mm、原材料/网格/边界/端口/alpha/gamma及所有原数值门。唯一来源accepted1/global7/loading1.35 mm，state SHA `'+protocol['selected_state_sha256']+'`。','',
        '执行前源核查纠正了上一计划的术语：J是九点Simpson（xi慢eta快），非Gauss；Hu没有采样点轴，是Q1单元常值参考位移Hessian。Hu中心只是单元代表标记，最大绝对分量与Frobenius范数分开。原保存值、物理任务、3NPZ/8字段及资源范围保持。','']
    if summary:
        lines += [f'自由第三介质 `{summary["free_medium_cells"]}` 单元／`{summary["free_medium_Simpson_samples"]}` 原Simpson样本；最小J `{summary["J_minimum"]!r}`，最大Hu绝对分量 `{summary["Hu_max_abs_component_per_mm"]!r}` /mm。', '',
            '最低十个J element/point条目及截断并列、最高十个Hu单元及截断/分量并列均保留；实际行数见JSON/CSV。原四项标量精确对账：`'+str(summary['source_scalar_exact_matches'])+'`。', '',
            '|极值|单元（从0计）|原Simpson点/分量|实际位置 mm|', '|---|---:|---|---|']
        for row in summary['J_minimum_ties']:
            lines.append(f'|最小J|{row["element_id"]}|q={row["simpson_point_index"]}, (xi,eta)=({row["xi"]},{row["eta"]})|{row["actual_position_mm"]}|')
        for row in summary['Hu_maximum_ties']:
            lines.append(f'|最大absHu|{row["element_id"]}|{row["component_ties"]}|单元代表中心{row["actual_center_marker_mm"]}|')
        lines += ['', '最近边界信息直接复用原普通JSON，未新增搜索：`'+str(summary['nearest_saved_observation']['closest_pair'])+'`。', '',
            '完整定位、参考/实际坐标和逐行连接关系见[原值摘要](run_001/summary.json)、[J位置表](run_001/j_locations.csv)、[Hu单元/分量表](run_001/hu_locations.csv)。跨单元重合点保留各自单元/采样身份；同单元/共享节点只描述几何关系，不证明因果或接触。','']
    for name,label in [('overview.png','整体实际位置'),('local.png','工件下方梁段局部')]:
        if (STAGE/'run_001'/name).is_file():lines += [f'![{label}](run_001/{name})','']
    lines += [f'helper `{helper.get("elapsed_seconds")}` s／180 s，outer `{launch.get("elapsed_seconds")}` s／240 s，SUP2采样峰值 `{launch.get("peak_sampled_tree_RSS_bytes")}` B／8589934592 B，清理 `{launch["cleanup_verified"]}`。', '',
        f'实际归档/字段解码 `{helper.get("archives_decoded")}`／`{helper.get("fields_decoded")}`；调用计数 `{helper.get("call_counts")}`。无HF力核/API/solver导入；计数不是通用机械hook。', '',
        f'helper真实错误 `{helper.get("error")}`；封存 `{len(seals)}` 份／`{closure["sealed_bytes"]}` B，状态 `{helper.get("output_identity_seal")}`。像素检查 `{closure["pixel_QA_status"]}`。', '',
        '原J/Hu数组、平衡态、原验收门、父任务历史和资格不改。CREF1仍仅祖先1.15 mm参考；本步骤不取得1.35态独立HP、圆周压力、有效夹持、卸载/释放、稳定性、完整路径、制造或HF5资格。','',
        '下一步：'+next_step,'',
        '[人工页](run_001/REVIEW.md) · [实际审阅](author/ACTUAL_REVIEW.md) · [helper](run_001/execution_receipt.json) · [outer](local_launch.json) · [闭卡JSON](author/closure.json)','']
    old_fronts={name:subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    for name,raw in old_fronts.items():assert (ROOT/name).read_bytes()==raw,name
    write('RESULTS.md','\n'.join(lines))
    write('NEXT_STEPS.md','# L-CLOCAL1后续（尚未执行）\n\n'+next_step+'\n\n具体结论由本次实际定位审阅后补入；本页不授权新运行。原门、物理条件及原失败/成功历史保持。\n')
    write('author/closure.json',json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    history=dict(source_baseline_commit=BASE,files=[])
    for name,raw in old_fronts.items():
        link=os.path.relpath(STAGE/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix=(f'> 2026-10-17 L-CLOCAL1 **{outcome.upper()}**：圆形1.35 mm保存J/Hu空间定位；3NPZ/8字段，无新平衡或默认HF修改。'
            f'原S4结果/资格保持；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+raw)
        history['files'].append(dict(path=name,old_bytes=len(raw),old_sha256=sha256(raw).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    write('author/front_history.json',json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='closed',execution_status=outcome,fronts=7,FE_evaluations=0)))


if __name__=='__main__':main()
