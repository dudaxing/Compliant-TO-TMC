"""Close the stdlib saved-study reader from new ordinary records and seals/stat."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001'
BASE = '035eaef93324d2bdb4767e5b6c0b5850e51cd766'
CARD = 'L-CTIPAREPORT1'
FRONTS = ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
    'docs/PHYSICAL_FUNCTION_PROGRESS.md', 'docs/RESUME_DEVELOPMENT.md',
    'docs/L_USE1_NEXT_STEP_PLAN.md', 'docs/L_BFWD1_NEXT_STEP_PLAN.md')
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
    report = read('run_001/report.json', optional=True)
    review, decision = read('author/ACTUAL_REVIEW.json'), read('author/NEXT_DECISION.json')
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
    if outcome == 'pass':
        assert report is not None and report['card'] == CARD
        assert report['schema_version'] == 'lf-saved-study-report-1.0'
        assert report['status'] == 'linked_existing_saved_reports'
        assert set(report['inputs']) == {'scalar_comparison', 'peak_node_comparison'}
        assert set(report['cycles']) == set(report['peak_links']) == {'baseline', 'new'}
        assert len(report['artifacts']) == helper['asset_stat_count'] == 12
        assert helper['function_calls'] == 1 and helper['ordinary_JSON_reads'] == 2
        assert helper['old_manual_stat_count'] == 4 and helper['old_PNG_stat_count'] == 8
        assert helper['old_media_content_reads'] == helper['old_GIF_stat_count'] == 0
        assert helper['new_PNGs'] == helper['new_media_QA'] == 0
        assert helper['default_installations'] == helper['new_tests'] == helper['HP_calls_by_wrapper'] == 0
        assert set(helper['returned_keys']) == {'cycles','scalar_comparison','peak_node_comparison','report'}
        assert helper['returned_object_aliases']['cycles_baseline_is_original'] is True
        assert helper['returned_object_aliases']['cycles_new_is_original'] is True
        assert launch['cleanup_verified'] is True
        assert all(STAGE+'/run_001/'+name in outputs for name in ('report.json','REVIEW.md'))
    stage_complete = outcome == 'pass'
    limits = {key: protocol[key] for key in (
        'helper_seconds','outer_seconds','sampled_RSS_bytes','cpu_thread_limit','cpu_thread_environment')}
    cycles = report.get('cycles', {}) if report is not None else {}
    scalar = report.get('scalar_comparison', {}) if report is not None else {}
    nodes = report.get('peak_node_comparison', {}) if report is not None else {}
    peaks = report.get('peak_links', {}) if report is not None else {}
    artifacts = report.get('artifacts', []) if report is not None else []
    closure = dict(card=CARD, status=outcome+'_closed', execution_status=outcome, execution_closed=True,
        created_utc=closed_at.isoformat(), report_client_local_date=local_date, report_timezone='Asia/Seoul',
        source_baseline_commit=BASE, science_version='0.5.0',
        science_baseline_commit='b1334bb6a83ba9a0efab7bdba7bd39722146f024',
        protocol_sha256=launch['protocol_sha256'], outer_status=launch['status'], helper_status=helper.get('status'),
        authorization_record='author/authorization.json', preparation_pending_flags_are_historical=True,
        stage_complete=stage_complete, report_record='run_001/report.json',
        report_status=report.get('status') if report is not None else None,
        input_identity=report.get('inputs') if report is not None else None,
        cycles=cycles, scalar_comparison=scalar, peak_node_comparison=nodes, peak_links=peaks,
        original_qualification=report.get('qualification') if report is not None else None,
        existing_artifacts=artifacts, business_io=report.get('business_io') if report is not None else None,
        returned_keys=helper.get('returned_keys'), returned_object_aliases=helper.get('returned_object_aliases'),
        new_PNGs=0, new_media_QA=0, visual_QA_status='not_applicable_no_new_images',
        actual_review_status=review['status'], helper_phase=helper.get('phase'), helper_error=helper.get('error'),
        outer_error=launch.get('error'), outer_stop_reason=launch.get('stop_reason'), resource_limits=limits,
        helper_elapsed_seconds=helper.get('elapsed_seconds'), outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'), cleanup_verified=launch.get('cleanup_verified'),
        sealed_output_files=len(outputs), sealed_output_bytes=sum(row['bytes'] for row in outputs.values()),
        output_identity_seal=helper.get('output_identity_seal'),
        new_equilibrium_solves=0, new_production_force_calls=0, new_production_tangent_calls=0,
        new_HP_calls=helper.get('HP_calls_by_wrapper'), new_tests=helper.get('new_tests'),
        default_installations=helper.get('default_installations'), next_decision=decision, next_step=decision['next_step'],
        qualification_scope='Saved research-report association only, not scientific acceptance or labels; all original qualification remains separate; no new pressure/effective grip/release/stability/alpha-independence, mesh/domain convergence, full-path reference or HF5 upgrade',
        closure_read_scope='Current new ordinary report/control/source/docs and original helper seals/stat only; no original comparison re-read/API invocation or science/media/full-history reads; Git object I/O is separate')
    artifact_lines = []
    for artifact in artifacts:
        link = os.path.relpath(ROOT/artifact['path'], stage).replace('\\','/')
        artifact_lines.append('|'+artifact['role']+'|'+artifact['kind']+'|[已有入口]('+link+')|'
            +str(artifact['bytes'])+'|'+artifact['identity_scope']+'|')
    peak_lines = []
    for key, peak in peaks.items():
        peak_lines.append('|'+key+'|'+shown(peak['alpha'])+'|'+shown(peak['accepted_index'])+'|'
            +shown(peak['original_target_index'])+'|'+shown(peak['raw_leg'])+'|'+shown(peak['d_mm'])+'|`'
            +peak['state_sha256']+'`|')
    available = lambda label, name: f'[{label}]({name})' if (stage/name).is_file() else label+'（未生成）'
    lines = [f'# {CARD}：保存研究报告读取入口与轻索引', '',
        f'{local_date}（Asia/Seoul，由实际UTC+09派生）；执行 **{outcome.upper()}**；阶段完成 `{stage_complete}`。新PNG=0，媒体像素QA不适用，未读取pixel_QA或重开旧图。', '',
        '准备期PLAN、preapproval卡和proposed_plan的pending/false按原字节保留，属于原历史；当前整卡已由用户明确批准，以[当前授权](author/authorization.json)、[批准卡](L-CTIPAREPORT1_CARD.md)和[SOURCE审查](author/SOURCE_REVIEW.md)为准。', '',
        '整体目标：将LF独立几何与HF非线性/TMC评估结果提供给外部研究层使用。本轮把现成全周期、参数比较与峰节点数据集中到一个可导入函数/CLI，补齐结果使用功能，不重建力学摘要或比较算法。', '',
        '实现入口为研究层saved_study_report.py的load_saved_study_report(cycle_report_file, peak_node_report_file, *, repo_root, bindings, assets)，同文件提供CLI。返回四键cycles/scalar_comparison/peak_node_comparison/report；前三者保持同次解析原对象/引用，CLI只写轻report和人工总览，不重复260/3390大表。默认native_response既有单result功能保持，不导入HF、NumPy、Matplotlib或力学实现。', '',
        f'实际读取/使用记录：function_calls `{shown(helper.get("function_calls"))}`，普通业务JSON `{shown(helper.get("ordinary_JSON_reads"))}`，固定旧图页stat `{shown(helper.get("asset_stat_count"))}`；返回键 `{shown(helper.get("returned_keys"))}`，原cycle引用 `{shown(helper.get("returned_object_aliases"))}`。两输入总计3219013 B；控制/源码读取另列，不再开原cycle/node/task/convergence/HP/history文件。', '',
        f'原标量报告计数 `{shown(scalar.get("counts"))}`；原节点报告计数 `{shown(nodes.get("counts"))}`。原20目标/两alpha40原值、260标量差与565对/3390节点差以及原4组/24差、整体6差仍由API原对象访问；本轮不重算差、fsum、极值或力矩，不筛节点、重排或归一化。', '',
        '两alpha原峰关联如下；同source的37项原观察对应仅为已有报告身份核对，不新增科学/HP验收。旧accepted1、新accepted12与global12分别保留：', '',
        '|source|alpha|原accepted|原global|原leg|d mm|原SHA|', '|---|---|---:|---:|---|---:|---|', *peak_lines, '',
        '不只按d或SHA合并角色：同d的加载/卸载不混配，origin不伪称loading，初始同SHA不跨alpha去重或迁移参考。嵌入cycle路径/SHA只是原来源声明，本轮未重读原cycle；旧14段/33raw与新4段/23raw历史分别保存，不当作纯alpha性能。', '',
        '轻report保输入identity、原counts/任务/资格、峰关联、对象访问位置与12固定入口。缺资格字段保持缺失，不自动补值或把选定态参考升为全路径验证。原节点弱力不是面牵引、压力或有效夹持；到零仅为已有输入回程完成。', '',
        decision.get('interpretation_md',''), '',
        '|原结果角色|类型|原页/图|stat bytes|身份范围|', '|---|---|---|---:|---|', *artifact_lines, '',
        '上述只链接4原人工页/8PNG，未读正文、PNG/GIF字节或内容SHA，不复制、解码、拼图或新渲染。原人工页已有变形/力图入口；密集小箭头、约8–10微米距离、全量程重合线等原可见性限制保持，不另作旧图QA。', '',
        f'资源配置 `{shown(limits)}`；helper实际 `{shown(helper.get("elapsed_seconds"))}` s，outer `{shown(launch.get("elapsed_seconds"))}` s；峰值采样RSS `{shown(launch.get("peak_sampled_tree_RSS_bytes"))}` B，清理 `{shown(launch.get("cleanup_verified"))}`。四库16线程仅为配置；本轮纯标准库，无GPU/机械计算或新测试/默认安装。', '',
        f'新封存 `{len(outputs)}` 份普通输出／`{closure["sealed_output_bytes"]}` B。闭卡继承helper seals并核新输出stat，不再调用读取API或重读两原comparison。helper错误 `{shown(helper.get("error"))}`，outer错误 `{shown(launch.get("error"))}`；真实partial与实际状态保持，首错停，无外部重试、修复重跑、延期、force、回滚或删除。', '',
        '入口：'+' · '.join(available(label,name) for label,name in (
            ('人工总览与实际使用说明','run_001/REVIEW.md'), ('轻report','run_001/report.json'),
            ('可导入模块/CLI','saved_study_report.py'), ('outer','step_launch.json'),
            ('helper','run_001/execution_receipt.json'), ('当前授权','author/authorization.json'),
            ('SOURCE审查','author/SOURCE_REVIEW.md'), ('实际审查','author/ACTUAL_REVIEW.md')))+
            ' · [闭卡JSON](author/closure.json) · [后续](NEXT_STEPS.md)', '',
        '后续：'+decision['next_step'], '',
        '交接：origin保持https://github.com/dudaxing/Compliant-TO-TMC.git，main继续开发。函数用显式repo_root解析相对路径；异目录恢复采用同机local-Git fetch/ff-only并单独核远端main，不称异机科学复算。不要重跑已关闭launcher。', '']
    next_text = decision.get('next_steps_md') or ('# '+CARD+' 后续\n\n'+decision['next_step']+
        '\n\n这里只建议下一步，不授权/启动新范围；原物理和资格保持。\n')
    generated = {'RESULTS.md': ('\n'.join(lines).rstrip()+'\n').encode('utf-8'),
        'NEXT_STEPS.md': (next_text.rstrip()+'\n').encode('utf-8'), 'author/closure.json': encoded(closure)}
    history = dict(source_baseline_commit=BASE, files=[])
    prefixed = {}
    for name in FRONTS:
        old = subprocess.check_output(GIT+['show',BASE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes() == old, 'Front differs from baseline: '+name
        link = os.path.relpath(stage/'RESULTS.md', (ROOT/name).parent).replace('\\','/')
        prefix = (f'> {local_date} {CARD} **执行{outcome.upper()}**／阶段完成{stage_complete}：'
            f'新增研究层保存报告函数/CLI和轻索引，关联现成两alpha周期、260标量差、565对3390节点差及12既有图页；'
            f'无新PNG或科学验收，原对象/资格保持；见[实际记录]({link})。原历史说明保留如下。\n\n').encode('utf-8')
        prefixed[name] = prefix+old
        assert prefixed[name].endswith(old) and prefixed[name].count(old) == 1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
            prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    generated['author/front_history.json'] = encoded(history)
    for name, raw in generated.items():
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), name
        assert not (stage/name).exists(), 'Preserve existing document: '+name
    for name, raw in generated.items():
        (stage/name).write_bytes(raw)
    for name, raw in prefixed.items():
        (ROOT/name).write_bytes(raw)
    (stage/'author/close_step.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,stage_complete=stage_complete,fronts=len(FRONTS)),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
