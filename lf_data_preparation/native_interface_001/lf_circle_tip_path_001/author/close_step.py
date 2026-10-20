"""Close L-CTIPPATH1 from ordinary records and original helper seals/stat only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_path_001'
BASE = '0afa58b4e263bbad8ec5912b6bafb13a500e782a'
CARD = 'L-CTIPPATH1'
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
MEDIA = ('response.png', 'quality.png')
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
    protocol = read('protocol.json')
    launch = read('step_launch.json')
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    response = read('run_001/unified_response.json', optional=True)
    history = read('run_001/source_history.json', optional=True)
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
    counts = response.get('counts') if response is not None else None
    rows = response['timeline_rows'] if response is not None else []
    pairs = response['same_input_pairs'] if response is not None else []
    segments = response['segments'] if response is not None else []
    if outcome == 'pass':
        assert response is not None and response['status'] == 'pass' and history is not None
        assert len(segments) == 14
        assert counts['timeline_rows'] == len(rows) and counts['same_input_pairs'] == len(pairs)
        assert rows[0]['d_mm'] == rows[-1]['d_mm'] == 0. and max(row['d_mm'] for row in rows) == 1.06
        assert launch['cleanup_verified'] is True
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert pixel is not None and pixel['card'] == CARD and pixel['inspections'] == 2
        assert {row['path'] for row in pixel['media']} == {STAGE+'/run_001/'+name for name in MEDIA}
        assert len(pixel['media']) == 2 and all(row['inspections'] == 1 for row in pixel['media'])
        assert len(media) == 2
    visual_status = pixel.get('status') if pixel is not None else 'not_provided'
    stage_complete = outcome == 'pass' and visual_status.startswith('pass')
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome,
        execution_closed=True, visual_QA_status=visual_status, stage_complete=stage_complete,
        created_utc=datetime.now(timezone.utc).isoformat(), report_client_local_date='2026-10-20',
        report_timezone='Asia/Seoul', source_baseline_commit=BASE,
        science_version='0.5.0', science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        terminal=review.get('terminal'), helper_phase=helper.get('phase'), helper_error=helper.get('error'),
        outer_error=launch.get('error'), outer_stop_reason=launch.get('stop_reason'),
        counts=counts, timeline_rows=rows, same_input_pairs=pairs, segments=segments,
        convergence_totals=response.get('convergence_totals') if response is not None else None,
        original_exceptions=response.get('exceptions') if response is not None else None,
        original_task=response.get('original_task') if response is not None else None,
        source_scope=response.get('scope') if response is not None else None,
        new_equilibrium_solves=0, new_production_force_calls=0, new_production_tangent_calls=0,
        new_HP_calls=helper.get('HP_calls_by_wrapper'), new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'),
        available_sealed_visualizations=media, pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        actual_review_status=review['status'], helper_elapsed_seconds=helper.get('elapsed_seconds'),
        outer_elapsed_seconds=launch.get('elapsed_seconds'), peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),
        cleanup_verified=launch.get('cleanup_verified'), sealed_output_files=len(outputs),
        sealed_output_bytes=sum(row['bytes'] for row in outputs.values()), output_identity_seal=helper.get('output_identity_seal'),
        next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Metadata association and visualization of fourteen existing successful segments only; no new equilibrium, force, tangent or HP; source result flags and selected-reference scope remain unchanged; no pressure, effective grip, free release, stability, full-path reference, mesh/domain convergence or HF5 upgrade',
        closure_read_scope='Ordinary JSON/source/docs and original helper producer seals/stat only; no old scientific/media/CSV payload reads, hashing, decoding, rendering, tests or mechanics; Git object I/O separate')
    metric_rows = []
    for pair in pairs:
        for metric, values in pair['metrics'].items():
            metric_rows.append([pair['d_mm'], pair['reference_role'], pair['loading_raw_leg'],
                metric, values['loading_value'], values['unloading_value'], values['unloading_minus_loading']])
    state_table = table(['显示行','原leg','d mm','输入R N','q_out mm','下半工件总Fy N','尖端距离 mm','介质minJ','介质maxabsHu 1/mm'],
        ([row['display_index'], row['raw_leg'], row['d_mm'], row['R_input_N'], row['q_out_mm'],
          row['total_body_Fy_N'], row['tip_to_raster_boundary_mm'], row['medium_min_J'], row['medium_max_abs_Hu_per_mm']] for row in rows))
    pair_table = table(['d mm','参考角色','参考原leg','原metric','loading/origin参考原值','卸载原值','卸载减参考'], metric_rows)
    old_links = []
    for segment in segments:
        paths = segment['paths']
        links = []
        for label, key in (('原实际变形动画','GIF'), ('原人工页','manual')):
            target = ROOT/paths[key]
            assert target.is_file(), str(target)
            link = os.path.relpath(target, stage).replace('\\','/')
            links.append(f'[{label}]({link})')
        old_links.append('|'+segment['segment']+'|'+' · '.join(links)+'|')
    available = lambda label, name: f'[{label}]({name})' if (stage/name).is_file() else label+'（未生成）'
    lines = [f'# {CARD}：14段已有加载与卸载结果的统一对照', '',
        f'2026-10-20（Asia/Seoul）；执行 **{outcome.upper()}**；图像QA `{visual_status}`；本阶段完成 `{stage_complete}`。原运行UTC时间保留，不改历史日期或原结果。', '',
        '整体目标是把LF夹持器几何接入独立、可恢复的大变形/TMC有限元评估，逐步形成可审查的结构变形、工件作用力及加载卸载响应。本轮实现的是跨保存段的统一读取、精确来源追溯和同输入对照，补齐分段计算后的使用功能。', '',
        '本轮做什么及原因：汇总pilot、STEP1–10及UNLOAD1–3共14段已有成功结果；读取授权普通摘要与收敛记录，保留每段原记录和嵌套历史，仅在统一显示时间线上合并相邻重复锚。原始leg、原状态SHA、各来源索引与原资格标志保持。合并锚不等于重算平衡，也不把原child中的完整路径未执行标志改成完成。', '',
        '物理条件保持：固定圆形工件r9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm、alpha=5e-7、gamma=1e-6、E=1 MPa、nu=0.3、plane strain、厚度20 mm、原网格与支撑/加权平均端口/对称条件。原目标路径覆盖0→1.06→0 mm；本卡不新增位移目标、构模、F/T、HP或平衡求解，不修改默认HF源码或原验收门。', '',
        f'实际效果：统一计数 `{shown(counts)}`。原收敛计数按来源完整累计 `{shown(closure["convergence_totals"])}`，不因显示锚合并而扣减重核验、Newton或试探记录。原拒绝/失败试探全部按来源保留，不能把通过的回溯说成外部重试，也不能隐藏它们。', '',
        state_table, '',
        '上表所有值均来自已有普通摘要。q_out是端口加权位移而非表面间隙；输入反力和工件Fx/Fy均为有符号下半模型原值，未镜像加倍。工件总力含material和Hu弱式贡献，不解释为连续表面压力或有效夹持力。距离为unsigned Q1栅格边界距离；正距离、非零弱力与外观接近均不能单独认定有效接触。', '',
        pair_table, '',
        '同位移对照按原d数值精确配对，不插值、不裁零、不吸附零值、不增归零/相等/可逆性或耗散验收门。零输入参考是pilot原始origin，表中保留其raw leg=origin；loading_value只是共同JSON列名，不能据此说存在loading零态。每项原值、差量、状态SHA和合并后的全部来源见统一JSON与同位移JSON。', '',
        '两张新图展示标量响应及原收敛/介质质量记录；没有重开旧媒体或旧科学数组。既有14份GIF只核原字节数并提供链接，本卡未解码、拼帧或生成新变形动画。field图的旧定义和原计算结果不变；右条带最大节点位移不等同尖端间隙，极值见证可随状态变化。', '',
        decision.get('interpretation_md',''), '',
        f'执行与记录：helper `{shown(helper.get("elapsed_seconds"))}` s，outer `{shown(launch.get("elapsed_seconds"))}` s；峰值采样RSS `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B；清理 `{shown(launch.get("cleanup_verified"))}`。实际封存 `{len(outputs)}` 份新输出、`{closure["sealed_output_bytes"]}` B。闭卡与发布只继承原helper seal并核大小；旧科学/媒体/CSV读取为0，新力学求解/生产F/T/HP/测试/默认安装为0。', '',
        '资格保持：当前统一曲线说明既有分段前向响应已可连贯查看，不替代一次从零完成全路径的生产资格。已通过的选定1.06 mm加载态独立参考仍仅覆盖其原范围；本卡不新增完整路径独立参考、压力、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格。输入回零只代表已有请求输入回程完成。', '',
        f'实际错误原值：helper `{shown(helper.get("error"))}`，outer `{shown(launch.get("error"))}`。执行结果、图像QA与阶段完成分开记录；无外部重试、修复重跑、延期、force、回滚或删除。', '',
        '|原段|已有变形与人工检查入口|', '|---|---|', *old_links, '']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += ['后续决策：'+decision['next_step'], '',
        '跨机器继续：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，后续开发在main。另一计算机clone后先读README、docs/CURRENT_STATUS.md、docs/RESUME_DEVELOPMENT.md和本目录RESULTS/NEXT_STEPS，再按protocol、source_history和原阶段授权确定新工作。不要重跑已关闭launcher，也不要从显示汇总反推或替换真实保存态。该次恢复核对采用同机异目录local Git objects fetch/ff-only，远程main另行核验，不称为异机科学重算。', '',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工页','run_001/REVIEW.md'), ('统一响应','run_001/unified_response.json'),
            ('同位移对照','run_001/same_input_comparison.json'), ('完整来源历史','run_001/source_history.json'),
            ('outer','step_launch.json'), ('helper','run_001/execution_receipt.json'),
            ('实际审查','author/ACTUAL_REVIEW.md'), ('像素记录','author/pixel_QA.json')))+
            ' · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)', '']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n本页只记录下一步建议，不启动新目标或授权新窗口；先明确新范围及资源，原物理与验收门保持。\n')
    generated = {'RESULTS.md': ('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md': (next_text.rstrip()+'\n').encode('utf-8'), 'author/closure.json': encoded(closure)}
    old_fronts = {name: subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    history_rows = dict(source_baseline_commit=BASE, files=[])
    prefixed = {}
    for name, old in old_fronts.items():
        assert (ROOT/name).read_bytes() == old, 'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\','/')
        prefix = (f'> 2026-10-20 {CARD} **执行{outcome.upper()}**／图像QA {visual_status}／阶段完成{stage_complete}：汇总已有14段0→1.06→0 mm加载卸载结果；'
            f'统一计数 {shown(counts)}，保留原始来源与历史，完成同位移原值/差量和两张新图。'
            f'不新增力学计算或修改原资格；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        history_rows['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(history_rows)
    for name, raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), name
        assert not (stage/name).exists(), 'Preserve existing closure document: '+name
    for name, raw in generated.items():
        (stage/name).write_bytes(raw)
    for name, raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,counts=counts,fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
