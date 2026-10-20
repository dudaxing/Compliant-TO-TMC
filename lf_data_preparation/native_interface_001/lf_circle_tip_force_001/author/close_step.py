"""Close L-CTIPFORCE1 from ordinary records and original helper seals/stat only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_001'
BASE = '58dd121f5026ecc2b8f0d8375479155dcb8f671c'
CARD = 'L-CTIPFORCE1'
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
MEDIA = ('force_vectors.png', 'force_components.png')
GIT = ['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']


def read(name, optional=False):
    path = ROOT/STAGE/name
    return None if optional and not path.is_file() else json.loads(path.read_bytes())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def shown(value):
    return '未提供' if value is None else str(value)


def table(headers, rows):
    return '\n'.join(['|'+'|'.join(headers)+'|', '|'+'|'.join('---' for _ in headers)+'|']+
        ['|'+'|'.join(shown(value) for value in row)+'|' for row in rows])


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'This closure already exists'
    protocol, launch = read('protocol.json'), read('step_launch.json')
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    response = read('run_001/force_response.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD
    assert protocol['source_baseline_commit'] == BASE
    assert launch['invocations'] == 1 and launch['status'] in ('pass', 'not_pass')
    assert not helper or (helper['card'] == CARD and helper['protocol_sha256'] == launch['protocol_sha256'])
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert decision['execution_status'] == outcome and review['execution_status'] == outcome
    assert isinstance(decision['next_step'], str) and decision['next_step'].strip()
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    media = {name: outputs[STAGE+'/run_001/'+name] for name in MEDIA if STAGE+'/run_001/'+name in outputs}
    state = response.get('state') if response is not None else None
    summary = response.get('original_summary') if response is not None else None
    counts = response.get('counts') if response is not None else None
    descriptive = response.get('descriptive') if response is not None else None
    groups = response.get('groups') if response is not None else {}
    if outcome == 'pass':
        assert response is not None and response['status'] == 'pass'
        assert counts['node_count'] == len(response['node_rows']) == 565
        assert set(groups) == {'physical_only','cut_only','physical_and_cut','interior'}
        assert sum(group['node_count'] for group in groups.values()) == 565
        assert launch['cleanup_verified'] is True
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert pixel is not None and pixel['card'] == CARD and pixel['inspections'] == 2
        assert {row['path'] for row in pixel['media']} == {STAGE+'/run_001/'+name for name in MEDIA}
        assert len(pixel['media']) == 2 and all(row['inspections'] == 1 for row in pixel['media'])
        assert len(media) == 2
    visual_status = pixel.get('status') if pixel is not None else 'not_provided'
    stage_complete = outcome == 'pass' and visual_status.startswith('pass')
    moment_origin = response.get('nodal',{}).get('moment_origin_mm') if response is not None else None
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        visual_QA_status=visual_status, stage_complete=stage_complete,
        created_utc=datetime.now(timezone.utc).isoformat(), report_client_local_date='2026-10-20',
        report_timezone='Asia/Seoul', source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        terminal=review.get('terminal'), helper_phase=helper.get('phase'), helper_error=helper.get('error'),
        outer_error=launch.get('error'), outer_stop_reason=launch.get('stop_reason'),
        state=state, original_summary=summary, moment_origin_mm=moment_origin, counts=counts,
        groups=groups, descriptive=descriptive,
        provenance=response.get('provenance') if response is not None else None,
        selected_state=response.get('selected_state') if response is not None else None,
        existing_GIF=response.get('existing_GIF') if response is not None else None,
        source_scope=response.get('scope') if response is not None else None,
        original_qualification=response.get('qualification') if response is not None else None,
        new_equilibrium_solves=0, new_production_force_calls=0, new_production_tangent_calls=0,
        new_HP_calls=helper.get('HP_calls_by_wrapper'), new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'), available_sealed_visualizations=media,
        pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        actual_review_status=review['status'], helper_elapsed_seconds=helper.get('elapsed_seconds'),
        outer_elapsed_seconds=launch.get('elapsed_seconds'), peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch.get('cleanup_verified'), sealed_output_files=len(outputs),
        sealed_output_bytes=sum(row['bytes'] for row in outputs.values()), output_identity_seal=helper.get('output_identity_seal'),
        next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Saved 1.06 mm fixed lower workpiece nodal weak-force contributions only; holding vectors are their opposite; no new mechanics or HP; no pressure, surface-traction, effective-grip, release, stability, full-path-reference, mesh/domain-convergence or HF5 upgrade',
        closure_read_scope='New ordinary JSON/source/docs and original helper producer seals/stat only; no old scientific arrays, CSV or media payload reads, hashing, decoding, rendering, tests or mechanics; Git object I/O separate')
    force_rows, group_rows = [], []
    if summary is not None:
        for name in ('total','material','regularization'):
            vec = summary['force_on_lower_body_N'][name]
            force_rows.append([name,vec[0],vec[1],summary['moment_about_origin_Nmm'][name]])
        holding = summary['holding_reaction_on_model_N']
        force_rows.append(['holding原保存值',holding[0],holding[1],'原summary未提供该项'])
    for name, group in groups.items():
        forces = group['force_on_body_N']
        group_rows.append([name,group['node_count'],forces['total'][0],forces['total'][1],
            forces['material'][1],forces['regularization'][1],group['moment_about_origin_Nmm']['total']])
    available = lambda label,name: f'[{label}](<{name}>)' if (stage/name).is_file() else label+'（未生成）'
    old_links = []
    if response is not None:
        old_GIF = response['existing_GIF']
        target = ROOT/old_GIF['path']
        assert target.stat().st_size == old_GIF['bytes']
        link = os.path.relpath(target,stage).replace('\\','/')
        old_links += [f'[原1.06 mm峰值变形动画](<{link}>)（仅核原大小，未解码）']
        original_manual = response.get('existing_manual')
        if original_manual:
            manual_path = original_manual['path'] if isinstance(original_manual,dict) else original_manual
            target = ROOT/manual_path
            assert target.is_file()
            link = os.path.relpath(target,stage).replace('\\','/')
            old_links += [f'[原人工页](<{link}>)']
    lines = [f'# {CARD}：保存峰值态的工件节点力贡献', '',
        f'2026-10-20（Asia/Seoul）；执行 **{outcome.upper()}**；图像QA `{visual_status}`；本阶段完成 `{stage_complete}`。原UTC运行时间与历史结果保持。', '',
        '整体目标是把LF夹持器几何接入独立、可恢复的大变形/TMC评估，形成可审查的实际结构、工件作用力及加载卸载响应。本轮在已有14段路径汇总之后，进一步解释1.06 mm加载峰值下半固定工件的力来自哪些节点、哪些掩码类别，以及material和Hu弱式贡献如何相加。', '',
        '本轮做什么及原因：仅读取授权的三个已有保存JSON，保留565个节点的原坐标、四类掩码、原total/material/regularization向量及原分组结果，提供节点作用力与反号holding向量，并将重新求和与原摘要的差作为描述性观察。没有新增构模、生产F/T、HP、平衡求解、测试、API关联或默认源码安装。', '',
        '物理条件保持：固定圆形工件r9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm、alpha=5e-7、gamma=1e-6、E=1 MPa、nu=0.3、plane strain、厚度20 mm、原网格、端口、支撑与对称条件。本卡仅观察已有accepted1/global12、loading、1.06 mm峰值态，不改变原验收门、状态SHA或其他保存态的资格。', '',
        f'原状态身份：`{shown(state)}`。计数与掩码观察：`{shown(counts)}`。', '',
        table(['原分量','下半工件Fx N','下半工件Fy N',f'关于{shown(moment_origin)}的原矩 N·mm'],force_rows), '',
        table(['原分组','节点数','total Fx N','total Fy N','material Fy N','regularization Fy N','total原矩 N·mm'],group_rows), '',
        '四个保存类别physical_only、cut_only、physical_and_cut、interior按原掩码显示；观察到的节点数分别为71、35、2、457，合计565。四类标签的互斥/完整观察，与物理边界节点集和对称切面节点集的关系不同：后两集合在physical_and_cut的两个节点重叠，不能把物理边界和切面当作天然互斥。', '',
        '表中均为原保存摘要值。各节点on_body_N是有限元弱式的有符号工件节点力贡献；holding_N逐节点反号，原holding总值独立保留。它们不是表面压力、法向牵引或有效夹持力。Hu是正则化弱式贡献，不能按连续表面应力解释；interior标签也不能自行排除或裁掉其贡献。力矩使用原保存参考点'+shown(moment_origin)+' mm，不转移参考点或据矩值授稳定性资格。', '',
        '描述性重新求和与差量（完整原值，不设相等、归零或新容差门）：', '',
        '```json',json.dumps(descriptive,ensure_ascii=False,indent=2,allow_nan=False),'```','',
        '新的fsum、掩码分组和节点分量重组差值只说明这次普通数据处理的观察；不把有限精度差量隐藏、裁零或当作新的物理验收门。原global/组摘要、原节点向量、原mask和原矩均保持，详见nodes/groups/force_response JSON。', '',
        '两张新图分别显示实际保存坐标上的节点向量与原分组分量/holding方向，保留有符号数值。箭头若为可视尺度，其图例注明缩放，不能当作结构位移；没有由力向量生成新变形。旧峰值GIF只核原字节大小并链接，不重新打开旧媒体。', '',
        decision.get('interpretation_md',''), '',
        f'执行记录：helper `{shown(helper.get("elapsed_seconds"))}` s，outer `{shown(launch.get("elapsed_seconds"))}` s；峰值采样RSS `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B；清理 `{shown(launch.get("cleanup_verified"))}`。原窗口封存 `{len(outputs)}` 个新输出、`{closure["sealed_output_bytes"]}` B，闭卡/发布仅继承原seal并核大小。新平衡/生产F/T/HP/测试/默认安装均为0；原三份JSON的读取范围与原GIF的stat范围单独保留在执行凭证。', '',
        '资格保持：所选加载峰值原有独立参考只保留其原范围。本卡没有完整路径新参考、压力、表面牵引、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格；固定工件节点反力的存在不能替代夹持功能判定。', '',
        f'实际错误原值：helper `{shown(helper.get("error"))}`，outer `{shown(launch.get("error"))}`。执行、像素QA与阶段完成分别记录，无外部重试、修复重跑、延期、force、回滚或删除。', '',
        ' · '.join(old_links),'']
    for name in media:
        lines += [f'![{name}](<run_001/{name}>)','']
    lines += ['后续决策：'+decision['next_step'],'',
        '跨机器继续：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。clone后先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md及本目录RESULTS/NEXT_STEPS，再按protocol和来源绑定开始新的工作。不要重跑已关闭launcher，不从本显示JSON替代真实保存态。恢复核对使用同机异目录local Git objects fetch/ff-only，远程main另行核验，不称为异机科学重算。','',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工页','run_001/REVIEW.md'),('节点力响应','run_001/force_response.json'),
            ('节点表','run_001/nodes.json'),('原分组及差量','run_001/groups.json'),
            ('outer','step_launch.json'),('helper','run_001/execution_receipt.json'),
            ('实际审查','author/ACTUAL_REVIEW.md'),('像素记录','author/pixel_QA.json')))+
            ' · [闭卡JSON](<author/closure.json>) · [后续](<NEXT_STEPS.md>)','']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n这里只记录建议，不启动新目标或新窗口；先明确范围、物理定义和资源，原门保持。\n')
    generated = {'RESULTS.md':('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md':(next_text.rstrip()+'\n').encode('utf-8'),'author/closure.json':encoded(closure)}
    old_fronts = {name:subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    front_history = dict(source_baseline_commit=BASE,files=[])
    prefixed = {}
    for name,old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old,'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix = (f'> 2026-10-20 {CARD} **执行{outcome.upper()}**／图像QA {visual_status}／阶段完成{stage_complete}：解释已有1.06 mm加载峰值的下半固定工件565节点弱式力、四类掩码及material/Hu分量，'
            f'保留原值并记录描述性重组差，生成两张新图；不新增力学计算或升级资格。见[实际记录](<{link}>)。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        front_history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(front_history)
    for name,raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()),name
        assert not (stage/name).exists(),'Preserve existing closure document: '+name
    for name,raw in generated.items():
        (stage/name).write_bytes(raw)
    for name,raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,counts=counts,fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
