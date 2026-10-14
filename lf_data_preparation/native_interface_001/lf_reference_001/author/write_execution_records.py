"""Write ordinary L-REF1 closure records after the actual terminal and independent review."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import json
import subprocess

BASE = '799bdc9709fa2fc92f573f3801b243f24e370983'
PROTOCOL_SHA = 'd6512016bc169183e6f857d0bab18185aa66e1aec3847ccbdb30a9450b9a2125'
REL = 'lf_data_preparation/native_interface_001/lf_reference_001'
FRONTS = ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md')
ORDINARY = {'.json', '.md', '.py', '.log', '.txt', '.jsonl'}


def ordinary(path):
    path = Path(path)
    assert path.suffix.lower() in ORDINARY
    raw = path.read_bytes()
    return raw, sha256(raw).hexdigest()


def read(path):
    raw, pin = ordinary(path)
    value = json.loads(raw)
    assert isinstance(value, dict)
    return value, pin


def display(value):
    if value is None:
        return '未记录'
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
        + ['| ' + ' | '.join(display(value) for value in row) + ' |' for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--terminal-review', type=Path, required=True)
    parser.add_argument('--terminal-review-md', type=Path, required=True)
    parser.add_argument('--pixel-qa', type=Path)
    parser.add_argument('--archive', type=Path, action='append', default=[])
    args = parser.parse_args()
    root = args.repo.resolve(); stage = root / REL; author = stage / 'author'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == BASE
    protocol, pin = read(stage / 'protocol.json')
    assert pin == PROTOCOL_SHA and protocol['card'] == 'L-REF1'
    assert protocol['selected_accepted_indices'] == protocol['original_target_indices'] == [13, 16]
    assert protocol['targets_mm'] == [1.2, 1.05]
    auth, _ = read(author / 'authorization.json'); reply, reply_pin = read(author / 'direct_human_reply.json')
    proof, proof_pin = read(author / 'source_publication_receipt.json')
    assert auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == proof['published_commit'] == BASE
    assert auth['human_evidence_sha256'] == reply_pin and auth['source_publication_receipt_sha256'] == proof_pin
    assert auth['protocol_sha256'] == proof['protocol_sha256'] == PROTOCOL_SHA
    confirmation, confirmation_pin = read(args.confirmation)
    assert confirmation['card'] == 'L-REF1' and confirmation['actual_session_id'] == 53525
    assert confirmation['authorized_source_commit'] == BASE and type(confirmation['actual_terminal_exit_code']) is int
    assert confirmation['initial_tool_chunk_id'] and confirmation['actual_terminal_tool_chunk_id']
    assert confirmation['actual_direct_human_answer'] == auth['direct_human_answer']
    assert confirmation['scientific_content_read_or_hashed_after_window'] is False
    outer, outer_pin = read(stage / 'reference_launch.json')
    assert outer['completed_utc'] and outer['status'] in ('pass', 'not_pass')
    assert outer['status'] == confirmation['outer_stdout']['status'] and outer['invocations'] == 1
    assert outer['authorized_execution_source_commit'] == BASE and outer['protocol_sha256'] == PROTOCOL_SHA
    assert confirmation['ordinary_output_sha256']['reference_launch.json'] == outer_pin
    assert all(outer[key] == value for key, value in confirmation['outer_stdout'].items())
    review, review_pin = read(args.terminal_review)
    assert str(review['status']).startswith('pass') and review.get('blocking_findings', []) == []
    assert review['authorized'] is review['executed'] is review['execution_closed'] is True
    assert review['execution_status'] == outer['status'] and review['protocol_SHA256'] == PROTOCOL_SHA
    assert review['authorized_execution_source_commit'] == BASE and review['outer_sha256'] == outer_pin
    source_pins = {REL + '/reference_launch.json': outer_pin, REL + '/protocol.json': PROTOCOL_SHA}
    unavailable = {}

    def reviewed(path, optional=False):
        name = path.relative_to(root).as_posix()
        if not path.exists() and optional:
            unavailable[name] = 'missing'; return None
        raw, actual = ordinary(path)
        assert review['reviewed_repository_SHA256'][name] == actual
        relative = path.relative_to(stage).as_posix() if path.is_relative_to(stage) else None
        if relative in confirmation['ordinary_output_sha256']:
            assert confirmation['ordinary_output_sha256'][relative] == actual
        source_pins[name] = actual
        try:
            value = json.loads(raw)
            assert isinstance(value, dict)
            return value
        except (json.JSONDecodeError, UnicodeDecodeError, AssertionError) as error:
            if not optional:
                raise
            unavailable[name] = type(error).__name__; return None

    output = root / protocol['reference_output']
    passed = outer['status'] == 'pass'
    helper = reviewed(output / 'execution_receipt.json', not passed)
    lifecycle = reviewed(output / 'lifecycle.json', not passed)
    summary = reviewed(output / 'summary.json', not passed)
    observation = reviewed(output / 'reference_observations.json', not passed)
    raw_rows = {i: reviewed(output / f'accepted_{i:03d}/summary.json', not passed) for i in (13, 16)}
    producer = root / protocol['production_stage'] / protocol['production_result_dir']
    result = reviewed(producer / 'result.json'); response = reviewed(producer / 'response.json')
    viewer = reviewed(root / protocol['production_stage'] / 'view' / protocol['production_result_dir'] / 'summary.json')
    assert result['status'] == 'success' and result['accepted_states'] == 25
    assert result['path_completed'] is result['task_target_executed'] is True and 'continuation' not in result
    assert result['mechanics_source_sha256'] == protocol['producer_mechanics_source_sha256']
    assert response['independent_reference']['status'] == 'not_provided'
    assert all(result[key] is False for key in ('independent_HP_qualified', 'equilibrium_qualified', 'HF_qualified'))
    if passed:
        assert helper['status'] == lifecycle['status'] == summary['status'] == 'pass'
        assert outer['exit_code'] == confirmation['actual_terminal_exit_code'] == 0
        assert outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert helper['HP_calls_started'] == helper['HP_calls_completed'] == 4
        assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == 2
        assert helper['plot_started'] == helper['plot_completed'] == 1
        assert summary['gates'] == protocol['gates'] and summary['accepted_states'] == 2
        assert all(summary[key] is False for key in ('full_production_path_reference_pass', 'full_original_path_reference_pass',
            'public_API_association_performed', 'HP_matrix_columns_exhaustively_checked', 'contact_qualified', 'clamp_qualified', 'pressure_qualified', 'HF5_qualified'))
        assert observation['status'] == 'rendered_observation_only' and observation['new_mechanics_calls'] == 0
    values, metrics = [], []
    for offset, index in enumerate((13, 16)):
        row, view = result['states'][index], viewer['rows'][index]
        assert row['state_sha256'] == protocol['selected_state_sha256'][offset] == view['state_sha256']
        assert row['d'] == protocol['targets_mm'][offset] == view['d_mm']
        assert row['original_target_index'] == view['index'] == view['original_target_index'] == index
        assert row['R_input'] == view['R_input_N'] and row['q_out'] == view['q_out_mm']
        body = row['workpiece']['force_on_lower_body_N']
        assert all(body[part] == [view[part + '_body_Fx_N'], view[part + '_body_Fy_N']]
            for part in ('total', 'material', 'regularization'))
        values.append([index, row['leg'], row['d'], row['R_input'], row['q_in'], row['q_out'],
            *body['total'], *body['material'], *body['regularization'], view['tip_to_bottom_mm']])
        if passed:
            raw, top, shown = raw_rows[index], summary['states'][offset], observation['states'][offset]
            assert raw['status'] == 'pass' and raw['index'] == top['index'] == top['source_accepted_index'] == index
            assert top['reference_execution_index'] == top['original_target_index'] == shown['accepted_source_index'] == shown['original_target_index'] == index
            assert raw['state_sha256'] == top['state_sha256'] == shown['state_sha256'] == row['state_sha256']
        if observation is not None:
            for shown in observation.get('states', []):
                if shown['original_target_index'] == index:
                    for entry in shown['entries']:
                        metrics.append([index, entry['label'], format(Decimal(entry['error']), '.6E'),
                            format(Decimal(entry['limit']), '.6E'), entry['pass_gate']])
    qa = None
    if args.pixel_qa:
        qa, _ = read(args.pixel_qa)
        assert qa['card'] == 'L-REF1' and qa['status'] == 'pass_observation_only'
        assert qa['inspection_calls'] == 1 and qa['detail'] == 'original' and qa['tool'] == 'tools.view_image'
        assert qa['path'] == protocol['reference_output'] + '/reference_observations.png'
        assert qa['source_indices_displayed'] == [13, 16] and qa['targets_mm_displayed'] == [1.2, 1.05]
        assert all(qa[key] is False for key in ('scientific_acceptance_derived_from_pixels',
            'scientific_gzip_NPZ_CSV_read_or_hashed_after_window', 'post_window_PNG_hash_computed',
            'full_path_pressure_or_clamping_qualification_added'))
    if passed:
        assert qa is not None
    terminal_lifecycle = lifecycle if lifecycle and lifecycle.get('status') in ('pass', 'not_pass') else {}
    keys = ('HP_calls_started', 'HP_calls_completed', 'accepted_mechanical_states_completed', 'workpiece_states_completed',
        'checks_completed', 'plot_started', 'plot_completed', 'JAX_module_loaded', 'AD_or_JIT_calls_by_wrapper')
    counts = {key: terminal_lifecycle.get(key) for key in keys}
    error = dict(outer_stop_reason=outer.get('stop_reason'), outer_failure=outer.get('failure'),
        helper_error=(helper or {}).get('error'), final_write_stop=(helper or {}).get('final_write_stop'),
        output_identity_seal=(helper or {}).get('output_identity_seal'), unavailable_ordinary_records=unavailable)
    status = 'PASS' if passed else 'NOT_PASS'
    physical = table(['accepted/original', 'leg', 'd mm', 'R N', 'qin mm', 'qout mm', 'total Fx N', 'total Fy N',
        'material Fx N', 'material Fy N', 'Hu Fx N', 'Hu Fy N', '原tip-to-bottom mm'], values)
    errors = table(['accepted/original', '显示项', '原normalized error', '原limit', '原pass gate'], metrics) if metrics else '参考误差显示未完成；不补造通过。'
    image = '![两保存态参考误差](run_001/reference/reference_observations.png)' if passed else '本卡NOT_PASS；保留实际部分结果，不执行补图、重试或闭窗科学hash。'
    next_basis = '当前两态严格PASS支持进入这一步，无须重复旧数学审计。' if passed else '本卡NOT_PASS，先保实际partial与原错误，排查后再按实际证据确定后续。'
    qa_text = json.dumps(qa, ensure_ascii=False, indent=2) if qa is not None else 'null'
    note = f'''# L-REF1实际闭卡：{status}

2026-10-15记录；计算于2026-10-14 23:49–23:53（Asia/Seoul）完成。用户直接批准后，root观察唯一session53525实际终态；源`{BASE}`、协议`{PROTOCOL_SHA}`。outer={outer['status']}，helper={display((helper or {}).get('status'))}，实际tool exit={confirmation['actual_terminal_exit_code']}。本记录来自普通保存摘要和独立实际审阅；本writer未读取科学或媒体字节，发布另由真实commit/push/恢复回执确认。

整体目标是HF独立读取LF普通几何，在一致任务下提供非线性/TMC反力、位移、固定工件弱式合力和保存变形，供外部研究层比较；HF不优化、不调用dmftd。L-PREP1已准备真实LF输入；L-FWD1已完成25目标0→1.20→0 mm及变形显示。本步核最接近工件的峰值accepted13/loading1.20 mm，以及作用衰减段accepted16/unloading1.05 mm，避免重复平衡求解。

本步实际{status}。复用原B850/aa86数学方法、11依赖、同13440单元/27378DOF、三力和同一PORT方向切线、CSC/KKT与工件投影；物理参数、生产settings与十五门保持。实际完成记录如下；缺失记录为null，未从空行表发明0计数：

```json
{json.dumps(counts, ensure_ascii=False, indent=2)}
```

{physical}

以上R/q、signed下半工件Fx/Fy及有限尖端距离复制自L-FWD1普通result/view相同state SHA行。工件力是固定体弱式节点合力，包含材料与Hu，不是连续压力或有效夹持力；距离沿用原viewer几何诊断，本卡没有新变形图或GIF。

{errors}

显示项仅格式化原误差字符串，未重算数学门。十项显示不替代十五门；原分母/floor与完整精度在本次普通raw摘要，工件误差不解释为Fy百分比。原十五门如下：

```json
{json.dumps(protocol['gates'], ensure_ascii=False, indent=2)}
```

{image}

实际root像素QA（成功时恰一次original检查，不补画）：

```json
{qa_text}
```

原合同helper900/outer960秒、采样8GiB；实际helper回执{display((helper or {}).get('elapsed_seconds'))}秒，child终端墙钟{display(outer.get('child_terminal_wall_seconds'))}秒，outer{display(outer.get('elapsed_seconds'))}秒，树采样峰{display(outer.get('peak_sampled_tree_RSS_bytes'))}B。采样/合作stop不是OS硬上限。继承依赖可能导入注册JAX，wrapper AD/JIT调用按实际生命周期记录，不声称未导入。新生产F/T、solver、API、测试、安装、外部重试/修复/延期/force均未执行；闭窗不补科学hash或解码。

通过只取得这两态4次HP80/120与原方向参考。原L-FWD1结果/response及25目标完成状态保持；full25参考、全部切线列、压力、有效夹持、自由工件释放、稳定性、一般LF/HF5资格均不升级，public API reference仍not_provided。历史失败各归原source/result，不拼接资格。

下一步优先复用现有摘要API，关联同L-FWD1完整25生产态、这两态4HP和已有变形媒体，便于外部研究层调用；完整25态参考仍为false，不新增求解、HP或压力资格，并另拟具体执行卡。{next_basis}闭卡剩余墙钟不是许可。

```json
{json.dumps(error, ensure_ascii=False, indent=2)}
```

[原峰值摘要](run_001/reference/accepted_013/summary.json) · [原卸载摘要](run_001/reference/accepted_016/summary.json) · [顶层摘要](run_001/reference/summary.json) · [执行回执](run_001/reference/execution_receipt.json) · [独立审阅](author/independent_terminal_review.md) · [root终态](author/root_terminal_confirmation.json) · [具体卡](L-REF1_CARD.md) · [原LF前向结果](../lf_forward_001/RESULTS.md)。
'''
    prefix = f'''# 最新实际闭卡：L-REF1 {status}，两LF保存态独立参考

2026-10-15记录；计算于2026-10-14 23:49–23:53（Asia/Seoul）完成。用户直接批准后的唯一session53525已实际终止；outer={outer['status']}，tool exit={confirmation['actual_terminal_exit_code']}。只核L-FWD1 accepted13/loading1.20与16/unloading1.05，原十五门/物理条件保持。实际计数、反力、位移、工件三力、误差图及QA见[L-REF1结果](../{REL}/RESULTS.md)。全25目标已生产完成，但两态参考不升级完整25态参考、压力、有效夹持/释放、稳定性、全部列或HF5资格；公开API reference仍not_provided。

下一步优先复用现有摘要API，关联同25生产态、这两态4HP和已有变形媒体，供外部研究层调用；保持full25参考false、不新增求解/HP/压力资格，另拟具体卡。

下方完整保留源提交799bdc97的原raw历史连续一次；历史prepared/未执行文字不覆盖顶部真实闭卡状态。出版另核真实推送/恢复回执。

---

'''.encode('utf-8')
    prior = {name: subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=root) for name in FRONTS}
    assert all((root / name).read_bytes() == raw and (prefix + raw).count(raw) == 1 for name, raw in prior.items())
    assert not (stage / 'RESULTS.md').exists() and not (author / 'execution_documentation_receipt.json').exists()
    archives = {'root_terminal_confirmation.json': ordinary(args.confirmation)[0],
        'independent_terminal_review.json': ordinary(args.terminal_review)[0], 'independent_terminal_review.md': ordinary(args.terminal_review_md)[0],
        'write_execution_records.py': ordinary(Path(__file__))[0]}
    if args.pixel_qa:
        archives['pixel_QA.json'] = ordinary(args.pixel_qa)[0]
    for path in args.archive:
        assert path.name not in archives
        archives[path.name] = ordinary(path)[0]
    assert all(not (author / name).exists() or (author / name).read_bytes() == raw for name, raw in archives.items())
    for name, raw in archives.items():
        if not (author / name).exists():
            (author / name).write_bytes(raw)
    (stage / 'RESULTS.md').write_bytes(note.encode('utf-8'))
    histories = []
    for name, raw in prior.items():
        current = prefix + raw; (root / name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(raw).hexdigest(), new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    receipt = dict(schema_version='LREF1-execution-documentation-receipt-1.0', card='L-REF1',
        status='ordinary_documentation_written_after_real_terminal', source_baseline_commit=BASE,
        actual_execution_closed=True, actual_execution_status=outer['status'], root_confirmation_sha256=confirmation_pin,
        terminal_review_sha256=review_pin, source_record_SHA256=source_pins, front_history=histories, actual_counts=counts,
        archived_ordinary_SHA256={name: sha256(raw).hexdigest() for name, raw in archives.items()},
        results_SHA256=sha256(note.encode('utf-8')).hexdigest(),
        scientific_postrun_reads_hashes_decodes_imports_tests_solver_plot_pixels=0,
        publication_confirmed_by_writer=False, created_utc=datetime.now(timezone.utc).isoformat())
    with (author / 'execution_documentation_receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=receipt['status'], actual_execution_status=outer['status'], science_media_postread=0)))


if __name__ == '__main__':
    main()
