"""Close LOCAL2 with actual visual QA, ordinary records and producer seals/stat."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_002'
OLD = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_001'
BASE = '261bc7be72211b428a6d1eaa6aa2b733f894b837'
FRONTS = ('README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
    'docs/RESUME_DEVELOPMENT.md','docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md')
GIT = ['git','-c','gc.auto=0','-c','maintenance.auto=false']


def main():
    stage = ROOT/STAGE
    def read(name):
        return json.loads((stage/name).read_bytes())
    def write(name,value):
        (stage/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    assert not (stage/'author/closure.json').exists()
    protocol, launch = read('protocol.json'), read('local_launch.json')
    helper = read('run_001/execution_receipt.json')
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json') if (stage/'author/pixel_QA.json').exists() else None
    assert launch['invocations']==1 and launch['status'] in ('pass','not_pass') and launch['cleanup_verified']
    outcome = 'pass' if launch['status']==helper['status']=='pass' else 'not_pass'
    assert review['status'].startswith('pass') and not review.get('blockers',[])
    assert review['execution_status']==decision['execution_status']==outcome
    outputs = helper['outputs']
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size==seal['bytes'],name
    if outcome=='pass':
        assert helper['output_identity_seal']=='complete_inside_original_helper_window'
        assert pixel is not None and pixel['inspections']==1
    visual_status = pixel['status'] if pixel else 'not_provided'
    complete = outcome=='pass' and visual_status.startswith('pass')
    qa_label = '图像QA通过' if complete else '图像QA未通过'
    old_closure = json.loads((ROOT/OLD/'author/closure.json').read_bytes())
    assert old_closure['execution_status']=='pass' and old_closure['visual_QA_status']=='not_pass_layout_overlap'
    assert old_closure['stage_complete'] is False
    closure = dict(card='L-CTIPLOCAL2',status='closed',execution_status=outcome,execution_closed=True,
        visual_QA_status=visual_status,stage_complete=complete,visual_gap_resolved_by_new_output=complete,
        original_LOCAL1_history_preserved=True,original_LOCAL1_stage_complete=False,
        source_baseline_commit=BASE,protocol_sha256=sha256((stage/'protocol.json').read_bytes()).hexdigest(),
        created_utc=datetime.now(timezone.utc).isoformat(),outer_status=launch['status'],helper_status=helper['status'],
        outputs=outputs,observation=helper.get('observation'),mechanics_calls=helper['mechanics_calls'],
        default_installations=helper['default_installations'],new_tests=helper['new_tests'],HP_calls_by_wrapper=helper['HP_calls_by_wrapper'],
        elapsed_seconds=helper['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
        peak_sampled_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],cleanup_verified=launch['cleanup_verified'],
        actual_review_status=review['status'],pixel_QA=pixel,next_decision=decision,
        qualifications='Saved-map layout only; original physics, gates, results, qualifications and failures preserved',
        read_scope='Ordinary records/source and original output seal/stat; no payload/media hash or decode by closure')
    write('author/closure.json',closure)
    tip_link=os.path.relpath(ROOT/OLD/'run_001/tip_closeup.png',stage).replace('\\','/')
    lines = ['# L-CTIPLOCAL2：补齐介质定位图排版','',
        f'2026-10-19；唯一执行 **{outcome.upper()}**；**{qa_label}**，本阶段完成 `{complete}`。','',
        '整体目标是把LF夹持器几何接入独立可恢复的TMC大变形分析，逐步观察接近工件、变形、作用力与卸载。当前r9/(80,40)、right92/Lr80的真实前向路径已推进至1.04 mm。LOCAL1完成两态局部定位及尖端近景，但介质图标题重叠；本轮只补足该显示功能。','',
        '问题与实现：constrained-layout的rect实际为(left,bottom,width,height)，旧值(0,.075,1,.95)使上缘达到1.025。本候选将medium绘图区改为(0,.075,1,.85)、suptitle显式y=.985，保留原图大小、两态共同范围、色标、地图数据与Q1/Simpson/Hu定义。原LOCAL1失败图、执行PASS/图像NOT_PASS及stage_complete=false历史保持。','',
        '为何这样做：先让已有介质压缩位置及正则项场峰值能够完整阅读，再根据真实结果决定下一物理目标；没有为排版问题重做平衡或改变任何原物理验收门。','',
        decision.get('interpretation_md',''),'',
        '实际执行仅读取同5NPZ/12字段：model坐标、连接、solid、workpiece_cells，两态各lift/fluctuation/J/Hu。与原普通定位及producer色标记录精确核对，原图媒体仅链接，未重开或重绘尖端图；只输出1张新PNG、render.json及manual.html。无新构模、F/T/HP/Newton/平衡求解、测试、GIF或默认HF修改。','',
        f"资源：helper {helper['elapsed_seconds']} /180 s；outer {launch['elapsed_seconds']} /240 s；进程树采样峰值 {launch['peak_sampled_tree_RSS_bytes']} B /8 GiB，四库线程上限16。唯一启动、清理 {launch['cleanup_verified']}。原窗口封存 {len(outputs)} 份输出、{sum(v['bytes'] for v in outputs.values())} B；像素检查 {pixel['inspections'] if pixel else '未提供'} 次。",'',
        'minJ为原含角点九点Simpson样本最小值；Hu逐单元常值组件，中心只是代表标记。首个C-order见证与精确并列数量均保留，未宣称所有并列位置唯一。正unsigned Q1距离及工件包含Hu的弱式合力，不能直接当作连续压力或有效夹持力；不升级完整路径、独立参考、释放/稳定性、网格/域宽或HF5资格。','',
        *(['![新版介质定位图](run_001/medium_locations.png)',''] if (stage/'run_001/medium_locations.png').exists() else []),
        '入口：'+' · '.join(f'[{name}](run_001/{name})' for name in ('manual.html','render.json') if (stage/'run_001'/name).exists())+f' · [原通过尖端图]({tip_link}) · [实际审查](author/ACTUAL_REVIEW.md) · [闭卡](author/closure.json) · [后续计划](NEXT_STEPS.md)','',
        '下一步：'+decision['next_step'],'',
        '恢复开发：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，在main继续。新目录/计算机clone后先读README、docs/CURRENT_STATUS.md与docs/RESUME_DEVELOPMENT.md，再读本卡RESULTS/NEXT_STEPS、protocol和author/authorization。异路径恢复核对使用同机local Git对象fetch/ff-only，不能表述为独立机器或远端对象下载验证。不要重新运行已关闭launcher。','']
    (stage/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    (stage/'NEXT_STEPS.md').write_text(decision.get('next_steps_md',decision['next_step']).rstrip()+'\n',encoding='utf-8',newline='\n')
    history=dict(source_baseline_commit=BASE,files=[])
    for name in FRONTS:
        old=subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==old
        link=os.path.relpath(stage/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix=(f'> 2026-10-19 L-CTIPLOCAL2 **执行{outcome.upper()}／{qa_label}**：同1.03/1.04 mm两保存态，仅修介质定位图排版，原数据/范围/色标保持、无新力学求解。本阶段完成{complete}；LOCAL1原失败历史保留。见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        new=prefix+old
        assert new.endswith(old) and new.count(old)==1
        (ROOT/name).write_bytes(new)
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    write('author/front_history.json',history)
    for name in ('close_local.py','publish_local.py'):
        target=stage/'author'/name
        source=(AUTHOR/name).read_bytes()
        if target.exists():assert target.read_bytes()==source
        else:target.write_bytes(source)
    links=[]
    for name in ('RESULTS.md','NEXT_STEPS.md'):
        path=stage/name
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):continue
            target=(path.parent/link.split('#')[0]).resolve()
            target.relative_to(ROOT)
            assert target.exists(),(name,link)
            links.append(dict(document=name,link=link))
    manual=stage/'run_001/manual.html'
    if manual.exists():
        for link in re.findall(r'(?:href|src)="([^"]+)"',manual.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):continue
            target=(manual.parent/link.split('#')[0]).resolve()
            target.relative_to(ROOT)
            assert target.exists(),link
            links.append(dict(document='run_001/manual.html',link=link))
    write('author/FINAL_DOC_REVIEW.json',dict(status='pass_ordinary_documents',links=links,fronts=7,payload_reads=0))
    print(json.dumps(dict(status='closed',execution_status=outcome,visual_QA_status=visual_status,stage_complete=complete,fronts=7,links=len(links))))


if __name__=='__main__':
    main()
