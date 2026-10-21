"""Close the ordinary saved-alpha comparison using producer seals and stat."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_comparison_001'
BASE = '08d07caf6cbb1e6ebe1af6f35c8dc1b8c9d0d669'
CARD = 'L-CTIPACOMP1'
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


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'Preserve existing closure'
    closed_at = datetime.now(timezone.utc)
    local_date = closed_at.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    protocol, launch = read('protocol.json'), read('step_launch.json')
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    comparison = read('run_001/comparison.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD and protocol['source_baseline_commit'] == BASE
    assert launch['invocations'] == 1 and launch['status'] in ('pass', 'not_pass')
    assert not helper or (helper['card'] == CARD and helper['protocol_sha256'] == launch['protocol_sha256'])
    assert review['status'].startswith('pass') and not review.get('blockers', review.get('blocking_findings', []))
    outcome = 'pass' if launch['status'] == helper.get('status') == 'pass' else 'not_pass'
    assert review['execution_status'] == decision['execution_status'] == outcome
    assert isinstance(decision['next_step'], str) and decision['next_step'].strip()
    outputs = helper.get('outputs') or {}
    for name, seal in outputs.items():
        assert (ROOT/name).stat().st_size == seal['bytes'], name
    media = {name: outputs[STAGE+'/run_001/'+name] for name in MEDIA if STAGE+'/run_001/'+name in outputs}
    counts = comparison.get('counts') if comparison is not None else None
    sources = comparison.get('sources', {}) if comparison is not None else {}
    pairs = comparison.get('pairs', []) if comparison is not None else []
    if outcome == 'pass':
        assert comparison is not None and comparison['card'] == CARD and comparison['status'] == 'pass'
        assert set(sources) == {'baseline', 'new'}
        assert counts['matched_pairs'] == len(pairs) == 20
        assert counts['raw_values'] == len(comparison['raw_values']) == 40
        assert counts['metric_fields'] == len(comparison['metric_fields']) == 13
        assert counts['descriptive_differences'] == 260
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert launch['cleanup_verified'] is True and len(media) == 2
    visual_status = pixel.get('status') if pixel is not None else 'not_provided'
    qa_complete = False
    if pixel is not None:
        assert pixel['card'] == CARD
        inspections = pixel['media']
        assert len(inspections) <= 2 and len({row['path'] for row in inspections}) == len(inspections)
        assert {row['path'] for row in inspections} <= {STAGE+'/run_001/'+name for name in MEDIA}
        assert all(row['inspections'] == 1 for row in inspections)
        assert pixel['inspections'] == len(inspections)
        qa_complete = len(inspections) == 2 and visual_status.startswith('pass')
    stage_complete = outcome == 'pass' and qa_complete
    limits = {key: protocol[key] for key in (
        'helper_seconds', 'outer_seconds', 'sampled_RSS_bytes', 'cpu_thread_limit', 'cpu_thread_environment')}
    source_summaries = {key: {
        'path': item['path'], 'manual_path': item['manual_path'], 'manual_bytes': item['manual_bytes'],
        'alpha': item['alpha'], 'counts': item['original']['counts'],
        'convergence_totals': item['original']['convergence_totals'],
        'original_qualification': item['original'].get('qualification')}
        for key, item in sources.items()}
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        created_utc=closed_at.isoformat(), report_client_local_date=local_date, report_timezone='Asia/Seoul',
        source_baseline_commit=BASE, science_version='0.5.0',
        science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        comparison_status=comparison.get('status') if comparison is not None else None,
        comparison_counts=counts, comparison_record='run_001/comparison.json',
        compatibility=comparison.get('compatibility') if comparison is not None else None,
        source_summaries=source_summaries, visual_QA_status=visual_status, visual_QA_complete=qa_complete,
        stage_complete=stage_complete, pixel_QA_observations=pixel.get('observations') if pixel is not None else None,
        available_sealed_visualizations=media, actual_review_status=review['status'],
        helper_phase=helper.get('phase'), helper_error=helper.get('error'), outer_error=launch.get('error'),
        outer_stop_reason=launch.get('stop_reason'), resource_limits=limits,
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'), cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs), sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'),
        new_equilibrium_solves=0, new_production_force_calls=0, new_production_tangent_calls=0,
        new_HP_calls=helper.get('HP_calls_by_wrapper'), new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'), next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Descriptive saved-alpha scalar comparison only; no new solve/HP/reference inheritance, alpha-independence, pressure, effective grip, free release, stability, mesh/domain convergence, full-path reference or HF5 upgrade',
        closure_read_scope='Current ordinary JSON/source/docs and original helper producer seals/stat only; no old science/CSV/media payload reads/hash/decode or scientific reexecution; Git object I/O is separate')
    old_links = []
    for key, item in sources.items():
        link = os.path.relpath(ROOT/item['manual_path'], stage).replace('\\','/')
        old_links.append(f'|{key}|{item["alpha"]}|[原人工页与既有变形入口]({link})|{item["manual_bytes"]}|`{shown(item["original"]["counts"])}`|')
    available = lambda label, name: f'[{label}]({name})' if (stage/name).is_file() else label+'（未生成）'
    lines = [f'# {CARD}：两种alpha的已有圆形工件响应对照', '',
        f'{local_date}（Asia/Seoul，由实际UTC+09派生）；执行 **{outcome.upper()}**；图像QA `{visual_status}`／完整 `{qa_complete}`；阶段完成 `{stage_complete}`。原来源日期与资格保持。', '',
        '整体目标：将LF夹持器几何接入独立、可恢复的大变形/TMC评估，明确结构变形、工件作用力与加载卸载响应。本轮补齐已有两种正则化参数的同定义比较功能，帮助决定后续物理或数值改进。', '',
        '本轮仅读取旧PATH1与新APATH1两份普通统一JSON，按原global target index、display branch和d配对；不另开旧task/summary/convergence或科学/媒体内容。原37观察、raw锚/二分诊断、计数、异常、原leg/SHA和来源完整保留在comparison.json的sources.original，40条原值与260差量可逐项审查。', '',
        f'实际输出计数 `{shown(counts)}`。两种alpha为5e-7和2.5e-7；r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm和原物理门保持。可比性和元数据差异原记录：`{shown(closure["compatibility"])}`。不静默归一化不兼容项。', '',
        '响应图分开R、q_out、material/Hu/total工件Fy和unsigned tip/Q1距离，避免多分量图例堆叠。质量图原介质/右域J和Hu用原目标序号；旧来源33 raw与新来源23 raw诊断分开面板，原残差/constraint及bound完整保持。显式科学刻度不用offset；极小量和非单调量不裁零。', '',
        '旧alpha结果来自14段原求解，新alpha来自4段；不同来源时钟、计数和锚复核不能作为纯alpha性能。相同d的加载/卸载不混配，origin保原leg；即使零态SHA相同也不跨alpha去重或转移HP。图中重合不等于绝对相等，不增归零、可逆、恢复率、耗散或alpha独立性验收门。', '',
        '工件Fx/Fy仍为固定下半模型有符号弱式合力，不镜像加倍，不包装成压力、面牵引或有效夹持力。q_out不是间隙，unsigned Q1距离不是解析圆间隙或接触/释放证明；AREF1只保新alpha原加载1.06/global12单态及原PORT方向，不授卸载或完整路径参考。', '',
        decision.get('interpretation_md',''), '',
        f'资源配置 `{shown(limits)}`；helper实际 `{shown(helper.get("elapsed_seconds"))}` s，outer `{shown(launch.get("elapsed_seconds"))}` s；峰值采样RSS `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B；清理 `{shown(launch.get("cleanup_verified"))}`。四库16线程为上限配置，不是实测核利用率。本卡新增构模/F/T/HP/平衡求解/测试/默认安装和API关联均为0。', '',
        f'本轮封存 `{len(outputs)}` 份输出／`{closure["sealed_output_bytes"]}` B，闭卡继承helper seal并核stat大小，不重开科学/媒体载荷。helper错误 `{shown(helper.get("error"))}`；outer错误 `{shown(launch.get("error"))}`。执行、图像QA与阶段完成分开；真实partial保留，无外部重试、修复重跑、延期、force、回滚或删除。', '',
        '|来源|alpha|原人工页|原页stat bytes|原计数|', '|---|---|---|---:|---|', *old_links, '',
        '以上只stat链接两份原人工页，其已有14段/4段变形入口保持；没有打开、复制、解码、抽帧、重哈希或拼接旧图/动画，不生成新结构图。', '']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += ['后续：'+decision['next_step'], '',
        '原参考和结果资格不升级：无压力、有效夹持、自由释放、稳定性、alpha独立性、网格/域收敛、完整路径独立参考或HF5资格。到零只代表原输入回程完成。', '',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工页与260差量','run_001/REVIEW.md'), ('原值/比较JSON','run_001/comparison.json'),
            ('outer','step_launch.json'), ('helper','run_001/execution_receipt.json'),
            ('实际审查','author/ACTUAL_REVIEW.md'), ('两图QA','author/pixel_QA.json')))+
            ' · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)', '',
        '交接：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，main继续开发。异目录恢复采用同机local-Git fetch/ff-only，远程main单独核对，不称异机科学复算；不要重跑已关闭launcher。', '']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n这里只建议下一步，不授权或启动新范围；原物理和验收门保持。\n')
    generated = {'RESULTS.md': ('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md': (next_text.rstrip()+'\n').encode('utf-8'), 'author/closure.json': encoded(closure)}
    front_history = dict(source_baseline_commit=BASE, files=[])
    prefixed = {}
    for name in FRONTS:
        old = subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes() == old, 'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\','/')
        prefix = (f'> {local_date} {CARD} **执行{outcome.upper()}**／图像QA {visual_status}／阶段完成{stage_complete}：'
            f'完成两种alpha已有普通结果对照，实际计数 {shown(counts)}；两张新标量图和原值/差量可审查。'
            f'无新科学求解或资格升级；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        front_history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(front_history)
    for name, raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), name
        assert not (stage/name).exists(), 'Preserve existing document: '+name
    for name, raw in generated.items():
        (stage/name).write_bytes(raw)
    for name, raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,counts=counts,fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
