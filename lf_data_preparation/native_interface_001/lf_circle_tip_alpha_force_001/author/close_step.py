"""Close the saved two-alpha peak node comparison using producer seals/stat."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_force_001'
BASE = '289450a8d27d915e1832beef9c75ca4fcc168232'
CARD = 'L-CTIPAFORCE1'
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


def main():
    stage = ROOT/STAGE
    assert not (stage/'author/closure.json').exists(), 'Preserve existing closure'
    closed_at = datetime.now(timezone.utc)
    local_date = closed_at.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    protocol, launch = read('protocol.json'), read('step_launch.json')
    authorization = read('author/authorization.json')
    helper = read('run_001/execution_receipt.json', optional=True) or {}
    comparison = read('run_001/comparison.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
    pixel = read('author/pixel_QA.json', optional=True)
    assert protocol['card'] == launch['card'] == CARD and protocol['source_baseline_commit'] == BASE
    assert authorization['card'] == CARD and authorization['authorized'] is True
    assert authorization['protocol_sha256'] == launch['protocol_sha256']
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
    pairs = comparison.get('node_pairs', []) if comparison is not None else []
    if outcome == 'pass':
        assert comparison is not None and comparison['card'] == CARD and comparison['status'] == 'pass'
        assert set(sources) == {'baseline', 'new'}
        assert counts['node_raw_rows'] == len(comparison['raw_values']) == 1130
        assert counts['matched_node_pairs'] == len(pairs) == 565
        assert counts['descriptive_node_differences'] == 3390
        assert counts['mask_group_original_rows'] == 8
        assert counts['mask_group_matched_pairs'] == len(comparison['group_pairs']) == 4
        assert counts['mask_group_component_differences'] == 24
        assert counts['whole_resultant_component_differences'] == 6
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
        'paths': item['paths'], 'manual_path': item['manual_path'], 'manual_bytes': item['manual_bytes'],
        'alpha': item['alpha'], 'selected_state': item['selected_state'],
        'state': item['state'], 'counts': item.get('counts'),
        'original_summary': item['original']['nodal']['summary'],
        'descriptive': item.get('descriptive')}
        for key, item in sources.items()}
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        created_utc=closed_at.isoformat(), report_client_local_date=local_date, report_timezone='Asia/Seoul',
        source_baseline_commit=BASE, science_version='0.5.0',
        science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        authorization_record='author/authorization.json', preparation_pending_flags_are_historical=True,
        comparison_status=comparison.get('status') if comparison is not None else None,
        comparison_counts=counts, comparison_record='run_001/comparison.json',
        display=comparison.get('display') if comparison is not None else None,
        whole_resultant_comparison=comparison.get('whole_resultant_comparison') if comparison is not None else None,
        original_group_comparison=comparison.get('group_pairs') if comparison is not None else None,
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
        qualification_scope='Saved fixed lower-body nodal weak-force explanation at two alpha loading peaks1.06 only; no new F/T/solve/HP, production-alpha change, pressure/face-traction/effective grip/release/stability/alpha-independence, mesh/domain convergence, full-path reference or HF5 upgrade',
        closure_read_scope='Current ordinary JSON/source/docs and original helper producer seals/stat only; no old science/CSV/media payload reads/hash/decode or scientific reexecution; Git object I/O is separate')
    old_links = []
    for key, item in sources.items():
        link = os.path.relpath(ROOT/item['manual_path'], stage).replace('\\','/')
        old_links.append(f'|{key}|{item["alpha"]}|[原人工页与既有变形入口]({link})|{item["manual_bytes"]}|`{shown(item.get("counts"))}`|')
    available = lambda label, name: f'[{label}]({name})' if (stage/name).is_file() else label+'（未生成）'
    lines = [f'# {CARD}：两种alpha同峰固定工件节点弱力空间对照', '',
        f'{local_date}（Asia/Seoul，由实际UTC+09派生）；执行 **{outcome.upper()}**；图像QA `{visual_status}`／完整 `{qa_complete}`；阶段完成 `{stage_complete}`。原来源日期与资格保持。', '',
        '准备期PLAN、preapproval卡及proposed_plan中的pending/false是原历史快照，原字节保留；当前整卡已由用户明确批准，以[当前授权](author/authorization.json)、[批准卡](L-CTIPAFORCE1_CARD.md)和[SOURCE审查](author/SOURCE_REVIEW.md)为准，不将旧pending误作当前授权状态。', '',
        '整体目标：将LF几何接入独立、可恢复的大变形/TMC评估，明确结构变形、工件作用力与加载卸载响应。本轮在既有标量比较之后解释material/Hu节点贡献的空间来源，帮助决定后续研究；不改生产alpha，不继续加载或例行新增HP。', '',
        '本轮只读两alpha各nodal/derived/geometry共6份已绑定普通JSON，共449948 B；按相同原global12、loading1.06及原SHA核身份，按原node ID配对。原两source全部节点坐标/mask/边、三种ON-body向量、原summary/holding/矩及37项row保持在comparison.json的sources.original；未另开科学数组、task、summary、convergence或旧媒体。', '',
        f'实际输出计数 `{shown(counts)}`。完整1130条原值、565组原节点配对与3390项三分量Fx/Fy描述差，4组/24分量差及整体6分量差可由比较JSON审查；人工页不重复3390行。alpha=5e-7与2.5e-7，r9/圆心(80,40)/right92/Lr80及原物理门保持。原兼容性记录：`{shown(closure["compatibility"])}`。', '',
        '图1为2alpha行×total/material/Hu三列，共6空间面板，每面板全部565点/向量。共同轴/aspect和跨两alpha三分量的maxnorm→2mm显示标尺；quiver minlength=0，零向量保节点点位，不筛小力。只画固定下半工件×1及原tip/距离见证，不伪造全机构变形；箭头mm/N不是位移放大。holding原total向量逐source列在图内，方向为−ON-body total，material/Hu反号只是代数分量，不是独立测量。', '',
        '图2保留全部节点Fx/Fy，旧/新同分量共用量程，Fx与Fy分别定范围；原组贡献直接使用summary.groups，分量三色/alpha柱纹。四mask为互斥完整分区71/35/2/457；physical/cut两个边节点集合另有2个共有节点，不能混为重复组。显式科学刻度无offset，原负号、零、极小量与抵消均保持。', '',
        '原fsum全体/原mask重组减summary、total−(material+Hu)尾差与原holding+ON-body total仅描述，不新增容差或吸零，不新增矩积分或移动原点。节点弱力不是局部面牵引，不做径向投影成压力，不镜像倍增，不授有效夹持。unsigned Q1距离不是解析圆间隙或接触/释放证明。', '',
        '本轮只解释1.06峰的material/Hu重分配，不冒充覆盖全程最大R/q/距离/总Fy差，1.02/1.03仍只是后续候选。两source原峰HP各保原态和原方向，不相互转移、不授全卸载/全路径或alpha独立性；也不比较不同来源的总CPU性能。', '',
        decision.get('interpretation_md',''), '',
        f'资源配置 `{shown(limits)}`；helper实际 `{shown(helper.get("elapsed_seconds"))}` s，outer `{shown(launch.get("elapsed_seconds"))}` s；峰值采样RSS `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B；清理 `{shown(launch.get("cleanup_verified"))}`。四库16线程为上限配置，不是实测核利用率。本卡新增构模/F/T/HP/平衡求解/测试/默认安装和API关联均为0。', '',
        f'本轮封存 `{len(outputs)}` 份输出／`{closure["sealed_output_bytes"]}` B，闭卡继承helper seal并核stat大小，不重开科学/媒体载荷。helper错误 `{shown(helper.get("error"))}`；outer错误 `{shown(launch.get("error"))}`。执行、图像QA与阶段完成分开；真实partial保留，无外部重试、修复重跑、延期、force、回滚或删除。', '',
        '|来源|alpha|原人工页|原页stat bytes|原节点计数|', '|---|---|---|---:|---|', *old_links, '',
        '以上只stat链接两份原人工页及其既有变形入口；没有打开、复制、解码、抽帧、重哈希或拼接旧图/动画，不生成全机构结构图。固定坐标=实际坐标沿producer的工件lift/fluctuation为零合同，本轮不另读数组重验。', '']
    for name in media:
        lines += [f'![{name}](run_001/{name})', '']
    lines += ['后续：'+decision['next_step'], '',
        '原参考和结果资格不升级：无压力、有效夹持、自由释放、稳定性、alpha独立性、网格/域收敛、完整路径独立参考或HF5资格。到零只代表原输入回程完成。', '',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工页与3390差量入口','run_001/REVIEW.md'), ('原值/比较JSON','run_001/comparison.json'),
            ('outer','step_launch.json'), ('helper','run_001/execution_receipt.json'),
            ('当前授权','author/authorization.json'), ('SOURCE审查','author/SOURCE_REVIEW.md'),
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
            f'完成两种alpha同1.06峰节点弱力空间对照，实际计数 {shown(counts)}；两张新力图和原值/差量可审查。'
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
