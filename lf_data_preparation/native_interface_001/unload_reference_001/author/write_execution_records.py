"""Write ordinary M-PREF1 closure records after real terminal, root QA and peer review.

This candidate imports stdlib only; it never opens scientific or media files.
It must not run before the actual terminal confirmation and review SHA arguments exist.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import json
import subprocess

BASE = 'ea5b55cc4f2ace87a78ed512d6bb14382e826a5d'
PROTOCOL_SHA = '651ef450c19d499486b0478d386e4b545a0e1bad99f478faafcebec1eb29ee7d'
REL = 'lf_data_preparation/native_interface_001/unload_reference_001'
FRONTS = ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md')


def ordinary(path):
    path = Path(path)
    assert path.suffix.lower() in ('.json', '.py', '.md', '.log')
    raw = path.read_bytes()
    return raw, sha256(raw).hexdigest()


def read(path):
    assert Path(path).suffix.lower() == '.json'
    raw, pin = ordinary(path)
    value = json.loads(raw)
    assert isinstance(value, dict)
    return value, pin


def display(value):
    if value is None:
        return '未记录'
    if isinstance(value, float):
        return format(value, '.12g')
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).replace('|', '\\|').replace('\n', ' ')


def error_display(value):
    # Formatting the original decimal string only; no new normalization or gate.
    return format(Decimal(value), '.6E')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        + ['| ' + ' | '.join(display(value) for value in row) + ' |' for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--terminal-review', type=Path, required=True)
    parser.add_argument('--terminal-review-md', type=Path, required=True)
    parser.add_argument('--terminal-review-sha256', required=True)
    parser.add_argument('--terminal-review-md-sha256', required=True)
    parser.add_argument('--pixel-qa', type=Path)
    parser.add_argument('--human-context', type=Path, required=True)
    parser.add_argument('--publication-tool-directory', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve(); stage = root / REL; author = stage / 'author'
    protocol, protocol_pin = read(stage / 'protocol.json')
    auth, auth_pin = read(author / 'authorization.json')
    proof, proof_pin = read(author / 'source_publication_receipt.json')
    human, human_pin = read(args.human_context)
    reply, reply_pin = read(author / 'direct_human_reply.json')
    assert protocol_pin == PROTOCOL_SHA and protocol['card'] == 'M-PREF1'
    assert protocol['selected_child_accepted_indices'] == [2, 3] and protocol['original_target_indices'] == [18, 19]
    assert protocol['targets_mm'] == [.9, .8] and protocol['expected_new_HP_calls'] == 4
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == proof['published_commit'] == reply['authorized_execution_source_commit'] == BASE
    assert auth['protocol_sha256'] == proof['protocol_sha256'] == PROTOCOL_SHA
    assert auth['source_publication_receipt_sha256'] == proof_pin and auth['human_evidence_sha256'] == reply_pin
    assert human['authorization_from_direct_human_reply'] is True
    assert human['direct_human_answer'] == auth['direct_human_answer'] and human['reply_context'] == reply['reply_context']
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == BASE
    confirmation, confirmation_pin = read(args.confirmation)
    assert confirmation['card'] == 'M-PREF1' and confirmation['unified_exec_session_id'] == 90472
    assert confirmation['root_observed_same_session_terminal'] is confirmation['execution_closed'] is True
    assert confirmation['source_baseline_commit'] == BASE and confirmation['recorded_utc']
    assert type(confirmation['tool_terminal_exit_code']) is int
    assert confirmation['execution_status'] in ('pass', 'not_pass')
    assert confirmation['observation_new_science_HP_solver_or_plot_calls'] == 0
    outer, outer_pin = read(stage / 'reference_launch.json')
    execution, execution_pin = read(root / protocol['reference_output'] / 'execution_receipt.json')
    assert confirmation['outer_sha256'] == outer_pin and confirmation['execution_receipt_sha256'] == execution_pin
    assert outer['status'] == confirmation['execution_status'] and outer['exit_code'] == confirmation['tool_terminal_exit_code']
    assert outer['invocations'] == 1 and outer['status'] in ('pass', 'not_pass')
    assert execution['status'] in ('pass', 'not_pass')
    assert outer['authorized_execution_source_commit'] == execution['authorized_execution_source_commit'] == BASE
    assert outer['protocol_sha256'] == execution['protocol_sha256'] == PROTOCOL_SHA
    review, review_pin = read(args.terminal_review)
    review_md, review_md_pin = ordinary(args.terminal_review_md)
    assert review_pin == args.terminal_review_sha256 and review_md_pin == args.terminal_review_md_sha256
    assert review['authorized_execution_source_commit'] == BASE and review['protocol_SHA256'] == PROTOCOL_SHA
    assert review['outer_sha256'] == outer_pin and review['execution_closed'] is True
    assert review['authorized'] is review['executed'] is True and review['execution_status'] == outer['status']
    assert str(review['status']).startswith('pass') and review.get('blocking_findings', []) == []
    pins = {REL + '/protocol.json': protocol_pin, REL + '/author/authorization.json': auth_pin,
        REL + '/author/source_publication_receipt.json': proof_pin, REL + '/author/direct_human_reply.json': reply_pin,
        REL + '/reference_launch.json': outer_pin, protocol['reference_output'] + '/execution_receipt.json': execution_pin}
    def reviewed(path, required=True):
        if not path.exists() and not required:
            return None
        value, pin = read(path); name = path.relative_to(root).as_posix()
        assert review['reviewed_repository_SHA256'][name] == pin
        pins[name] = pin
        return value
    output = root / protocol['reference_output']
    summary = reviewed(output / 'summary.json')
    lifecycle = reviewed(output / 'lifecycle.json')
    raw_rows = {index: reviewed(output / f'accepted_{index:03d}/summary.json', False) for index in (18, 19)}
    observation = reviewed(output / 'reference_observations.json', False)
    producer = root / protocol['production_stage'] / protocol['production_result_dir']
    result = reviewed(producer / 'result.json')
    response = reviewed(producer / 'response.json')
    model = reviewed(producer / 'model/model.json')
    viewer_file = root / protocol['production_stage'] / 'view' / protocol['production_result_dir'] / 'summary.json'
    viewer = reviewed(viewer_file)
    assert result['status'] == 'success' and result['accepted_states'] == 9
    assert result['mechanics_source_sha256'] == protocol['producer_mechanics_source_sha256']
    assert result['continuation'] == protocol['production_continuation']
    assert response['independent_reference']['status'] == 'not_provided'
    assert result['full_original_path_completed'] is result['full_extended_path_completed'] is False
    assert all(result[key] is False for key in ('independent_HP_qualified', 'equilibrium_qualified', 'HF_qualified'))
    ancestor = result['continuation']
    while 'parent_continuation' in ancestor:
        ancestor = ancestor['parent_continuation']
    assert ancestor['parent_status'] == 'failed' and ancestor['parent_failure']['code'] == 'time_limit'
    passed = outer['status'] == 'pass'
    if passed:
        assert execution['status'] == summary['status'] == lifecycle['status'] == 'pass' and outer['exit_code'] == 0
        assert outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
        assert execution['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert summary['HP_calls_started'] == summary['HP_calls_completed'] == lifecycle['HP_calls_started'] == lifecycle['HP_calls_completed'] == 4
        assert summary['accepted_states'] == lifecycle['accepted_mechanical_states_completed'] == lifecycle['workpiece_states_completed'] == 2
        assert summary['plot_started'] == summary['plot_completed'] == lifecycle['plot_started'] == lifecycle['plot_completed'] == 1
        assert summary['gates'] == protocol['gates'] and summary['result_sha256'] == pins[(producer / 'result.json').relative_to(root).as_posix()]
        assert all(summary[key] is False for key in ('full_production_segment_reference_pass', 'full_composed_path_reference_pass',
            'full_child_path_reference_pass', 'full_original_path_reference_pass', 'full_extended_path_reference_pass',
            'contact_qualified', 'clamp_qualified', 'pressure_qualified', 'HF5_qualified', 'public_API_association_performed'))
        assert observation['status'] == 'rendered_observation_only' and len(observation['states']) == 2
        assert observation['original_gates_unchanged'] is True and observation['new_mechanics_calls'] == 0
    selected = []
    for offset, (child, global_index) in enumerate(((2, 18), (3, 19))):
        row = result['states'][child]
        assert row['original_target_index'] == global_index and row['state_sha256'] == protocol['selected_state_sha256'][offset]
        assert row['d'] == protocol['targets_mm'][offset] and row['leg'] == 'unloading' and row['continuation_anchor'] is False
        raw = raw_rows[global_index]
        if raw is not None:
            assert raw['index'] == global_index and raw['state_sha256'] == row['state_sha256'] and raw['target_mm'] == row['d']
        if passed:
            top = summary['states'][offset]; observed = observation['states'][offset]
            assert raw['status'] == 'pass' and top['index'] == top['child_accepted_index'] == child
            assert top['reference_execution_index'] == top['original_target_index'] == global_index
            assert top['state_sha256'] == observed['state_sha256'] == row['state_sha256']
            assert observed['accepted_child_index'] == child and observed['original_target_index'] == global_index
            assert len(observed['entries']) == 10
            for entry in observed['entries']:
                member = entry['source_member']
                if member.startswith('checks:'):
                    check = next(item for item in raw['checks'] if item['name'] == member.split(':', 1)[1])
                    error, limit = check['normalized_error'], check['limit']
                elif member.endswith('.hp80_hp120_error'):
                    check = raw['force_checks']['total']; error, limit = check['hp80_hp120_error'], check['reference_limit']
                else:
                    check = raw
                    for key in member.split('.'):
                        check = check[key]
                    error, limit = check['normalized_error'], check['limit']
                assert entry['error'] == error and entry['limit'] == limit and entry['pass_gate'] is check['pass_gate'] is True
        selected.append((child, global_index, row, raw))
    qa = None; qa_pin = None
    if args.pixel_qa is not None:
        qa, qa_pin = read(args.pixel_qa)
        assert qa['card'] == 'M-PREF1' and qa['inspected_by_root'] is True
        assert 0 <= qa['actual_view_image_calls'] <= 1
        assert qa['render_retry_or_replot'] == qa['scientific_post_read'] == qa['scientific_NPZ_gzip_CSV_byte_reads_or_hashes'] == 0
        assert qa['new_PNG_postrun_hashes'] == qa['old_media_reads_or_decodes'] == qa['new_science_HP_solver_or_plot_calls'] == 0
        assert all(item['view_calls'] == 1 and item['detail'] == 'original' for item in qa.get('images', []))
        assert all(item['path'] == protocol['reference_output'] + '/reference_observations.png' for item in qa.get('images', []))
    if passed:
        assert qa is not None and qa['actual_view_image_calls'] == 1 and len(qa['images']) == 1
    values = []
    for child, index, row, raw in selected:
        body = row['workpiece']['force_on_lower_body_N']
        view_row = viewer['rows'][child]
        assert view_row['index'] == child and view_row['original_target_index'] == index
        assert view_row['state_sha256'] == row['state_sha256'] and view_row['d_mm'] == row['d']
        assert view_row['R_input_N'] == row['R_input'] and view_row['q_out_mm'] == row['q_out']
        for name, part in (('total', 'total'), ('material', 'material'), ('regularization', 'regularization')):
            assert [view_row[name + '_body_Fx_N'], view_row[name + '_body_Fy_N']] == body[part]
        values.append([str(child) + '/' + str(index), row['d'], row['R_input'], row['q_in'], row['q_out'],
            *body['total'], *body['material'], *body['regularization'], view_row['tip_to_bottom_mm']])
    physical = table(['child/global', 'd mm', 'R N', 'qin mm', 'qout mm', 'total Fx N', 'total Fy N',
        'material Fx N', 'material Fy N', 'Hu Fx N', 'Hu Fy N', '原tip-to-bottom mm'], values)
    metrics = []
    if observation is not None:
        for state in observation['states']:
            for entry in state['entries']:
                metrics.append([str(state['accepted_child_index']) + '/' + str(state['original_target_index']), entry['label'],
                    error_display(entry['error']), error_display(entry['limit']), entry['pass_gate']])
    metric_table = table(['child/global', '原显示项', '原normalized error', '原limit', '原pass gate'], metrics) if metrics else '未完成参考误差显示；不补造两态通过。'
    status = 'PASS' if passed else 'NOT_PASS'
    counts = {key: lifecycle.get(key) for key in ('HP_calls_started', 'HP_calls_completed', 'accepted_mechanical_states_completed',
        'workpiece_states_completed', 'checks_completed', 'plot_started', 'plot_completed', 'JAX_module_loaded', 'AD_or_JIT_calls_by_wrapper')}
    errors = dict(outer_stop_reason=outer.get('stop_reason'), outer_failure=outer.get('failure'),
        helper_error=execution.get('error'), final_write_stop=execution.get('final_write_stop'), lifecycle_error=lifecycle.get('error'),
        output_identity_seal=execution.get('output_identity_seal'), actual_reference_states=[
            {key:row[key] for key in ('index', 'child_accepted_index', 'reference_execution_index', 'original_target_index', 'status', 'target_mm', 'state_sha256', 'leg') if key in row}
            for row in summary.get('states', [])])
    visual = '![本次两卸载态原参考误差](run_001/reference/reference_observations.png)' if passed else '本卡NOT_PASS；保留实际partial和原错误，不声称完整两态／四HP／PNG已完成。'
    qa_text = '未产生可供完整QA的实际图。' if qa is None else 'root实际一次original像素QA记录；状态字段：' + display(qa.get('status')) + '\n\n' + '\n'.join('- ' + str(note) for item in qa.get('images', []) for note in item.get('observations', []))
    note = f'''# M-PREF1实际闭卡：{status}

2026-10-13（Asia/Seoul）。用户直接批准后，root观察唯一session90472真实终态exit{outer['exit_code']}；源`{BASE}`、协议`{PROTOCOL_SHA}`，outer={outer['status']}、helper={execution['status']}。本记录来自真实普通摘要与独立终态审阅；本writer没有读科学或媒体字节，出版核对另由真实receipt确认。

整体目标仍为独立HF读取普通LF几何，给出有限变形／TMC前向反力、位移、固定工件作用、可恢复保存态及可检查变形，供外部研究层使用；HF不优化、不调用dmftd。已保存加载／卸载至零和25点统一显示，本步补两个变化显著的卸载点：原child2/global18/0.90与child3/global19/0.80，原工件Fy衰减且有限底边距离增大，因此先核保存力、材料／Hu分量及同一PORT方向切线，避免重复平衡或变形绘图。

本步实际{status}。B850与aa86原方法、11数学源、全部物理参数／生产settings和十五门保持；raw accepted_018/019，顶层child2/3与reference_execution_index18/19保留。实际完成计数如下（开始／完成原值分别保留）：

```json
{json.dumps(counts, ensure_ascii=False, indent=2)}
```

通过时只取得这两个source result/state的四次HP80／120与原方向参考，不关联公开API。工件检查完成数来自原不可变aa86返回及实际生命周期；其科学gz不在闭卡后读取或重算body误差。

{physical}

这些signed Fx/Fy与R/qout原值复制自成功UNLOAD2普通result并与原pure viewer同SHA/child/global普通行对账；最后列取该既有viewer原tip-to-bottom有限距离，不是新HP距离、连续表面间隙或压力。本次没有创建新变形或GIF。工件力是固定下半工件weak-form节点合力，含material/Hu；原材料Fy随这两点下降，Hu Fy两值接近且在后一态略高。这是保存标量观察，未计算新差值、比例或工件相对误差。作用衰减和距离增大支持保存态的卸载观察，不能据此认定自由工件有效夹持或完全释放。

{metric_table}

误差显示只格式化原字符串，完整精度、原分母／floor／limits和全部原检查仍在新raw普通摘要与已封存科学产物中。十项显示不替代十五门，工件误差不是Fy相对百分比。原十五阈值如下，未放宽或新算gate：

```json
{json.dumps(protocol['gates'], ensure_ascii=False, indent=2)}
```

{visual}

{qa_text}

新资源合同helper900／outer960秒、采样8GiB。实际helper回执{display(execution.get('elapsed_seconds'))}秒、helper终端墙钟{display(outer.get('child_terminal_wall_seconds'))}秒、outer{display(outer.get('elapsed_seconds'))}秒；helper采样峰{display(lifecycle.get('sampled_peak_RSS_bytes'))}B、树采样峰{display(outer.get('peak_sampled_tree_RSS_bytes'))}B。最早clock包含imports、身份／归档、四HP、比较、一次plot和封存；采样／合作stop不宣称OS硬限制。Inherited dependencies实际可能加载／注册JAX；AD/JIT wrapper调用按原记录，不伪称未import。新生产F/T、solver、API、tests、安装、重试／修复／延期／force均0，闭窗不补科学hash或图。

原UNLOAD2九态及成功父链保持，深层ALPHA failed/time_limit与M-EXTEND1 NOT_PASS历史保留；source era保持实际producer mechanics map，本参考只归原child2/3 state。旧1.20／1.15／1.10三点仍各归原result/state，不搬移。本卡不能匹配公共reader所需全九态／18HP；完整9态、组合25点路径、全部切线列、压力、有效夹持／完全释放、稳定性、一般LF／HF5资格均不升级。

当前效果是所选两态的实际参考结论及一次原误差显示；若NOT_PASS，仅保已完成部分和原错误。下一步基于真实结果选择必要的功能／验证缺口，任何新科学范围须另拟具体卡并取得直接批准，闭卡余时不是许可。

实际停止／部分记录：

```json
{json.dumps(errors, ensure_ascii=False, indent=2)}
```

[原raw18摘要](run_001/reference/accepted_018/summary.json) · [原raw19摘要](run_001/reference/accepted_019/summary.json) · [顶层摘要](run_001/reference/summary.json) · [误差原记录](run_001/reference/reference_observations.json) · [执行回执](run_001/reference/execution_receipt.json) · [外层回执](reference_launch.json) · [独立实际审阅](author/independent_terminal_review.md) · [root终态](author/root_terminal_confirmation.json) · [实际QA](author/pixel_QA.json) · [直接批准](author/actual_human_context.json) · [具体卡](M-PREF1_CARD.md) · [原卸载结果](../saved_extension_004/RESULTS.md) · [25点保存显示](../../../functional_views/native_alpha_composed_20261013/complete_001/RESULTS.md)。
'''
    prefix = f'''# 最新实际闭卡：M-PREF1 {status}，两卸载保存态参考

2026-10-13（Asia/Seoul）。用户直接批准后的唯一session90472已真实终止exit{outer['exit_code']}；实际outer={outer['status']}、helper={execution['status']}，HP开始／完成{display(counts['HP_calls_started'])}／{display(counts['HP_calls_completed'])}、数学态{display(counts['accepted_mechanical_states_completed'])}、工件态{display(counts['workpiece_states_completed'])}、plot开始／完成{display(counts['plot_started'])}／{display(counts['plot_completed'])}。只核原UNLOAD2 child2/3、global18/19、0.90/0.80；物理／源版本／十五门保持。原signed工件分量、反力、位移、有限距离、误差显示和真实QA见[M-PREF1结果](../{REL}/RESULTS.md)。

旧参考仍归原result/state；成功父链和failed/time_limit祖先保持，完整9态／25点路径、压力、有效夹持／完全释放、稳定性、全列与HF5不升级。本writer科学／媒体postread为0；出版另核真实推送／恢复receipt。下方保留源提交ea5b55c的完整原raw历史连续一次，历史未执行文字不取代顶部实际状态。

---

'''.encode('utf-8')
    prior = {}
    for name in FRONTS:
        previous = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=root)
        assert (root / name).read_bytes() == previous and (prefix + previous).count(previous) == 1
        prior[name] = previous
    assert not (stage / 'RESULTS.md').exists() and not (author / 'execution_documentation_receipt.json').exists()
    archives = {'root_terminal_confirmation.json': ordinary(args.confirmation)[0], 'actual_human_context.json': ordinary(args.human_context)[0],
        'independent_terminal_review.json': ordinary(args.terminal_review)[0], 'independent_terminal_review.md': review_md,
        'write_execution_records.py': ordinary(Path(__file__))[0],
        'writer_source_notes.md': ordinary(Path(__file__).with_name('writer_source_notes.md'))[0],
        'writer_source_author_receipt.json': ordinary(Path(__file__).with_name('writer_source_author_receipt.json'))[0]}
    if args.pixel_qa is not None:
        archives['pixel_QA.json'] = ordinary(args.pixel_qa)[0]
    publication_receipt, publication_pin = read(args.publication_tool_directory / 'execution_publisher_author_receipt.json')
    assert publication_receipt['source_baseline_commit'] == BASE
    for name in ('publisher_execution.py', 'EXECUTION_PUBLICATION_TOOL_NOTES.md'):
        raw, pin = ordinary(args.publication_tool_directory / name)
        assert publication_receipt['current_source_SHA256'][name] == pin
        archives[name] = raw
    archives['execution_publisher_author_receipt.json'] = ordinary(args.publication_tool_directory / 'execution_publisher_author_receipt.json')[0]
    for name, raw in archives.items():
        target = author / name
        assert not target.exists() or target.read_bytes() == raw
    for name, raw in archives.items():
        target = author / name
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(raw)
    with (stage / 'RESULTS.md').open('xb') as stream:
        stream.write(note.encode('utf-8'))
    histories = []
    for name, previous in prior.items():
        current = prefix + previous; (root / name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(previous).hexdigest(), new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    documented = dict(schema_version='MPREF1-execution-documentation-receipt-1.0', status='ordinary_documentation_written_after_real_terminal',
        card='M-PREF1', source_baseline_commit=BASE, authorized_execution_source_commit=BASE, protocol_sha256=PROTOCOL_SHA,
        actual_execution_closed=True, actual_execution_status=outer['status'], execution_status=outer['status'], execution_closed=True,
        real_terminal_exit_code=outer['exit_code'], unified_exec_session_id=90472, root_confirmation_sha256=confirmation_pin,
        source_record_SHA256=pins, archived_ordinary_SHA256={name:sha256(raw).hexdigest() for name,raw in archives.items()},
        front_history=histories, results_SHA256=sha256(note.encode('utf-8')).hexdigest(), actual_counts=counts,
        selected_child_accepted_indices=[2,3], original_target_indices=[18,19],
        scientific_postrun_reads_hashes_decodes_imports_tests_solver_plot_pixels=0,
        closed_scientific_identity_source='Only helper sealed execution_receipt.outputs; publisher maystat original files without rawread/hash.',
        publication_confirmed_by_writer=False, created_utc=datetime.now(timezone.utc).isoformat())
    with (author / 'execution_documentation_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(documented, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=documented['status'], actual_execution_status=outer['status'], science_media_postread=0, publication_confirmed=False)))


if __name__ == '__main__':
    main()
