"""Close an observed stage using ordinary records and original output seals."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_001'
BASE = 'f6e9e926614a234e15313e9b641f31054095e588'
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
    protocol, launch, helper = read('protocol.json'), read('local_launch.json'), read('run_001/execution_receipt.json')
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
        assert pixel is not None and pixel['inspections']==2
    visual_status=pixel['status'] if pixel else 'not_provided'
    stage_complete=outcome=='pass' and visual_status.startswith('pass')
    visual_label='图像QA通过' if stage_complete else '图像QA未通过'
    closure = dict(card='L-CTIPLOCAL1',status='closed',execution_status=outcome,execution_closed=True,
        visual_QA_status=visual_status,stage_complete=stage_complete,
        source_baseline_commit=BASE,protocol_sha256=sha256((stage/'protocol.json').read_bytes()).hexdigest(),
        created_utc=datetime.now(timezone.utc).isoformat(),outer_status=launch['status'],helper_status=helper['status'],
        outputs=outputs,observation=helper.get('observation'),mechanics_calls=helper['mechanics_calls'],
        default_installations=helper['default_installations'],new_tests=helper['new_tests'],HP_calls_by_wrapper=helper['HP_calls_by_wrapper'],
        elapsed_seconds=helper['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
        peak_sampled_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],cleanup_verified=launch['cleanup_verified'],
        actual_review_status=review['status'],pixel_QA=pixel,next_decision=decision,
        qualifications='Only saved geometry/field localization; original physics, gates, results, qualifications and history preserved',
        read_scope='Ordinary records/source and original output seal/stat; no payload/CSV/media hash or decode by closure')
    write('author/closure.json',closure)
    lines = ['# L-CTIPLOCAL1：尖端近景与介质极值定位','',f'2026-10-19；唯一执行及数值对账 **{outcome.upper()}**；**{visual_label}**，整阶段完成标志 `{stage_complete}`。','',
        '实际像素检查：尖端近景通过；medium_locations.png顶部总标题与上排子图标题重叠，保留原输出并记为排版未通过。原窗口已关闭，没有重绘、覆盖原图或重试。定位JSON和原数值对账通过；计算状态与显示缺口分别记录，原物理门保持。','',
        '整体目标是把LF夹持器几何接入独立、可恢复的TMC大变形分析，逐步观察机构接近工件、变形、作用力及卸载。本轮不改变模型或求解新的平衡态。','',
        '已完成的前序工作：当前r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm布置已由短行程逐步延伸到1.04 mm，STEP8保存1.03与1.04 mm两态，原生产门通过。宽幅图难以肉眼分辨约19微米的最近距离，原摘要也没有给出全非工件介质minJ/maxabsHu的位置。','',
        '本轮做什么及原因：只解码5个既存NPZ的12个批准字段，复用真实Q1边界与原split坐标顺序，生成等比例近景与全介质极值定位，让数值与空间位置可以对照。原J九点为含角点的Simpson；Hu逐单元常值组件，图中中心只是代表标记。保留精确并列数，首个C-order见证不代表唯一极值位置。','',
        decision.get('interpretation_md',''),'',
        '读取范围：model的coordinates/connectivity/solid/workpiece_cells；每态state的lift/fluctuation和forces中的J/Hu。其余普通JSON提供身份、原反力、边界与tip见证。没有读取旧媒体、应力、力数组、切线或矩阵；无新构模、F/T/HP/Newton/平衡求解、测试、GIF或默认HF修改。原物理条件、数值设置、验收门及历史保持。','',
        f"资源与效果记录：helper {helper['elapsed_seconds']} /180 s；outer {launch['elapsed_seconds']} /240 s；采样进程树峰值 {launch['peak_sampled_tree_RSS_bytes']} B /8 GiB；四库线程上限16。唯一启动，owned清理 {launch['cleanup_verified']}。原窗口输出封存 {len(outputs)} 份、{sum(x['bytes'] for x in outputs.values())} B。实际审查 {review['status']}；实际像素检查次数 {pixel['inspections'] if pixel else '未提供'}。",'',
        '正unsigned Q1距离、介质场或工件含Hu弱式合力，不能直接授予连续接触压力或有效夹持资格；本卡也不授独立高精度参考、自由释放、稳定性、网格/域宽收敛或HF5资格。','',
        *[f'![{name}](run_001/{name})\n' for name in ('tip_closeup.png','medium_locations.png') if (stage/'run_001'/name).exists()],
        '入口：'+' · '.join(f'[{name}](run_001/{name})' for name in ('manual.html','localization.json') if (stage/'run_001'/name).exists())+' · [实际审查](author/ACTUAL_REVIEW.md) · [原窗口回执](run_001/execution_receipt.json) · [闭卡记录](author/closure.json) · [后续计划](NEXT_STEPS.md)','',
        '下一步：'+decision['next_step'],'',
        '恢复开发：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续在main。另一目录或计算机clone后先读README、docs/CURRENT_STATUS.md与docs/RESUME_DEVELOPMENT.md，再读本卡RESULTS/NEXT_STEPS、protocol及author/authorization。不同路径恢复核对采用同机local Git对象fetch/ff-only，不能表述为独立机器或远端对象下载验证。不要重新运行本卡已关闭launcher。','']
    (stage/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    (stage/'NEXT_STEPS.md').write_text(decision.get('next_steps_md',decision['next_step']).rstrip()+'\n',encoding='utf-8',newline='\n')
    history = dict(source_baseline_commit=BASE,files=[])
    for name in FRONTS:
        old = subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==old
        link = os.path.relpath(stage/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix = (f'> 2026-10-19 L-CTIPLOCAL1 **执行{outcome.upper()}／{visual_label}**：r9/(80,40)、right92/Lr80，两态1.03/1.04 mm保存数组局部观察；数值精确对账通过，定位图顶部标题重叠，原图保留、整阶段尚未完成；无新平衡求解，原资格及历史保持。见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        current = prefix+old
        assert current.endswith(old) and current.count(old)==1
        (ROOT/name).write_bytes(current)
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
            assert (path.parent/link.split('#')[0]).resolve().exists(),(name,link)
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
    print(json.dumps(dict(status='closed',execution_status=outcome,fronts=7,links=len(links))))


if __name__=='__main__':
    main()
