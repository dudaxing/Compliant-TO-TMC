"""Record a genuinely closed L-FWD1 success or partial using ordinary evidence only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

BASE = 'e23a34b6fac803bab4be6bd35e980807291326c3'
REL = 'lf_data_preparation/native_interface_001/lf_forward_001'
LABEL = 'lf_fine_forward'
ORDINARY = {'.json', '.jsonl', '.md', '.py', '.toml', '.txt', '.log'}
SCIENTIFIC = {'.npz', '.npy', '.gz', '.csv', '.png', '.gif'}
FRONTS = ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md')


def raw(path):
    assert path.suffix.lower() in ORDINARY, str(path)
    return path.read_bytes()


def read(path):
    return json.loads(raw(path))


def pin(path):
    return sha256(raw(path)).hexdigest()


def write_new(path, content):
    with path.open('xb') as stream:
        stream.write(content)


def child(directory, name):
    path = (directory / name).resolve()
    assert path.is_relative_to(directory.resolve())
    return path


def text(value):
    if value is None:
        return '未保存／未观察'
    return str(value).replace('|', '\\|').replace('\n', ' ')


def markdown_table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    return '\n'.join(lines + ['| ' + ' | '.join(text(value) for value in row) + ' |' for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--terminal-review', type=Path, required=True)
    parser.add_argument('--terminal-review-md', type=Path, required=True)
    parser.add_argument('--root-terminal-confirmation', type=Path, required=True)
    parser.add_argument('--pixel-qa', type=Path)
    parser.add_argument('--publication-tool-review', type=Path, required=True)
    parser.add_argument('--archive', type=Path, action='append', default=[])
    args = parser.parse_args()
    root = args.repo.resolve()
    stage, author = root / REL, root / REL / 'author'
    run = stage / 'run_001'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() == BASE
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip() == 'main'
    protocol_file, outer_file = stage / 'protocol.json', stage / 'production_launch.json'
    protocol, outer = read(protocol_file), read(outer_file)
    review = read(args.terminal_review)
    actual = read(args.root_terminal_confirmation)
    tool_review = read(args.publication_tool_review)
    assert protocol['card'] == outer['card'] == 'L-FWD1'
    assert outer['status'] in ('pass', 'not_pass') and outer['completed_utc'] and outer['invocations'] == 1
    assert review['status'].startswith('pass') and not review['blocking_findings']
    assert review['execution_closed'] is True and review['execution_status'] == outer['status']
    assert review['protocol_SHA256'] == pin(protocol_file) and review['outer_sha256'] == pin(outer_file)
    assert actual['actual_terminal_exit_code'] == outer['exit_code']
    assert actual.get('launch_sha256', actual.get('outer_sha256')) == pin(outer_file)
    assert tool_review['status'].startswith('pass') and not tool_review['blocking_findings']
    assert 'install_sources' not in protocol and protocol['expected_default_changes'] == 0
    assert protocol['zero_start'] is True and protocol['saved_parent_or_state_used'] is protocol['extend_path'] is False
    assert len(protocol['targets_mm']) == 25

    # The terminal reviewer binds the actual ordinary files. Scientific files are never opened here.
    identities = {}
    malformed_ordinary = []
    def observed_json(path, required=True):
        if not path.is_file():
            assert not required, str(path)
            return None
        name = path.relative_to(root).as_posix()
        assert review['reviewed_repository_SHA256'][name] == pin(path), name
        identities[name] = pin(path)
        try:
            return read(path)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            if required or outer['status'] == 'pass':
                raise
            malformed_ordinary.append(dict(path=name, sha256=pin(path), error=type(error).__name__, reason=str(error)))
            return None

    helper_file = run / 'execution_receipt.json'
    helper = observed_json(helper_file, required=False)
    if helper_file.is_file():
        assert actual.get('execution_receipt_sha256', actual.get('helper_receipt_sha256')) == pin(helper_file)
    if helper is not None:
        assert helper['status'] in ('running', 'pass', 'not_pass')
        assert helper['protocol_sha256'] == pin(protocol_file) and helper['authorized_execution_source_commit'] == BASE
    if outer['status'] == 'pass':
        assert helper is not None and helper['status'] == 'pass' and helper['last_phase'] == 'closure'
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True

    production = root / protocol['candidate_directory']
    view = root / protocol['view_directory']
    assert production == run / LABEL and view == run / 'view'
    result = observed_json(production / 'result.json', required=False)
    response = observed_json(production / 'response.json', required=False)
    model = None
    if result is not None:
        model_file = child(production, result['model']['descriptor_path'])
        model = observed_json(model_file, required=outer['status'] == 'pass')
        if model is not None:
            assert pin(model_file) == result['model']['descriptor_file_sha256']
        assert result['accepted_states'] == len(result['states'])
        assert result['targets_mm'] == protocol['targets_mm'] and 'continuation' not in result
    views = observed_json(view / 'view.json', required=False)
    summary = observed_json(view / LABEL / 'summary.json', required=False)
    if summary is not None:
        assert summary['accepted_states'] == len(summary['rows'])
    if outer['status'] == 'pass':
        assert result is not None and response is not None and views is not None and summary is not None
        assert result['status'] == response['status'] == 'success' and views['status'] == 'pass'
        assert result['path_completed'] and result['loading_peak_reached'] and result['unload_endpoint_reached']
        assert result['accepted_states'] >= 25 and helper['cached_production_gates']['passed'] is True
        assert summary['accepted_states'] == result['accepted_states']
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == 'not_provided'

    scientific = {}
    if helper is not None and helper['status'] in ('pass', 'not_pass') and helper.get('last_phase') == 'closure':
        for name, entry in helper.get('outputs', {}).items():
            if Path(name).suffix.lower() in SCIENTIFIC:
                path = child(root, name)
                assert path.is_file() and path.stat().st_size == entry['bytes']
                scientific[name] = dict(path=name, sha256=entry['sha256'], bytes=entry['bytes'])
    qa = read(args.pixel_qa) if args.pixel_qa is not None else None
    pngs = [name for name in scientific if Path(name).suffix.lower() == '.png']
    if outer['status'] == 'pass':
        assert len(pngs) == 3 and qa is not None
        assert qa['status'].startswith('pass') and qa['actual_invocations'] == 3
    # A failed producer may retain partial scientific files not sealed; record honestly, never late hash.
    unsealed = []
    for path in run.rglob('*'):
        if path.is_file() and path.suffix.lower() in SCIENTIFIC:
            name = path.relative_to(root).as_posix()
            if name not in scientific:
                unsealed.append(dict(path=name, bytes=path.stat().st_size, identity='not sealed; no post-window read/hash; publication must resolve or stop'))

    archive = {
        'independent_terminal_review.json': args.terminal_review,
        'independent_terminal_review.md': args.terminal_review_md,
        'root_terminal_confirmation.json': args.root_terminal_confirmation,
        args.publication_tool_review.name: args.publication_tool_review,
        'write_execution_records.py': Path(__file__),
    }
    if args.pixel_qa is not None:
        archive['pixel_QA.json'] = args.pixel_qa
    for path in args.archive:
        assert path.name not in archive or path.resolve() == archive[path.name].resolve()
        archive[path.name] = path
    assert not (stage / 'RESULTS.md').exists() and not (author / 'execution_documentation_receipt.json').exists()
    for name, path in archive.items():
        assert path.suffix.lower() in ORDINARY and not (author / name).exists(), name
        raw(path)

    rows = result['states'] if result is not None else []
    saved_row_count = len(rows) if result is not None else None
    forces = []
    for index, row in enumerate(rows):
        body = row.get('workpiece', {}).get('force_on_lower_body_N', {})
        forces.append([index, row.get('original_target_index'), row.get('leg'), row['d'], row['R_input'], row['q_out'],
            *[body.get(part, [None, None])[1] for part in ('total', 'material', 'regularization')],
            row['minimum_J'], row['relative_residual']])
    table = markdown_table(['接受序号', '原目标', 'leg', 'd mm', 'R N', 'q_out mm', 'total Fy N', '材料 Fy N', 'Hu Fy N', '全域 min J', '残差'], forces) if forces else '没有可复制的result接受态表；表缺失不证明实际接受态为零，不虚构反力、位移、工件力或场值。'
    distance_table = '没有完成保存态 viewer；有限表面距离和自由介质场尚未观察。'
    if summary is not None:
        distance_table = markdown_table(['序号', 'd mm', 'tip→bottom mm', 'tip→left mm', 'tip→right mm', 'bottom ray mm', 'left ray mm', 'free-medium min J', 'free-medium max |Hu| 1/mm'],
            [[row['index'], row['d_mm'], row['tip_to_bottom_mm'], row['tip_to_left_mm'], row['tip_to_right_mm'],
              row['bottom_first_ray_mm'], row['left_first_ray_mm'], row['medium_min_J'], row['medium_max_abs_Hu_per_mm']] for row in summary['rows']])
    pictures = '\n\n'.join('![' + title + '](run_001/view/' + name + ')' for name, title in (
        ('comparison.png', '真实变形、输入反力与下半体弱式作用'),
        ('distances_forces.png', '有限几何距离与有符号Fx'),
        ('peak_fields.png', '峰值保存场：实体Green应变、自由介质J及Hu'))) if outer['status'] == 'pass' else '本卡没有完整通过后的图件资格；已产生的部分显示仅按原产物记录保存，不假称完整可视化通过。'
    gif_name = REL + '/run_001/view/' + LABEL + '/actual_states.gif'
    if gif_name in scientific:
        pictures += '\n\n[真实接受态N帧GIF](run_001/view/' + LABEL + '/actual_states.gif)；仅链接已封存产物，未再次解码。'
    failure = (response or {}).get('failure') or (helper or {}).get('exception') or (result or {}).get('failure')
    status = outer['status']
    saved_flags = {key: (result or {}).get(key) for key in ('path_completed', 'loading_peak_reached', 'unload_endpoint_reached', 'task_target_executed')}
    counts = (helper or {}).get('counts', {})
    records = f'''# L-FWD1 实际结果：{status.upper()}

真实执行源 main `{BASE}`；原 source 卡与协议不改。本页只在唯一进程真正结束后，复制普通保存记录生成。当前结果不是已提交／已推送声明。

## 整体目标、已做工作与原因

整体目标是独立HF接收普通LF几何，分析有限变形／第三介质接触并返回位移、执行器反力、固定工件作用和可恢复状态供外部研究层消费。L-PREP1已完成输入准备；本步直接使用新gripper_native_fine派生几何，一次调用已安装evaluate_native，构模原门通过才从零完成原25目标。成功后原纯viewer独立进程显示，没有重写力核、求解器、默认源码或改变任务来取得通过。

E=1 MPa、nu=.3、厚20 mm、gamma=1e-6、alpha=5e-7、Lr80 mm，h=.5 mm、84×40 mm域及固定方体中心(71,40)/边18 mm保持。原task标签是模板历史，新LF拓扑不是旧几何的alpha单因素比较。显式mechanical/chunk256/port_projection及原settings，只新controller clock18000秒；所有25目标保持，N可含原内部二分接受态。

## 实际终态与可恢复响应

outer={text(status)}／exit={text(outer['exit_code'])}／invocations={text(outer['invocations'])}／stop={text(outer['stop_reason'])}。helper保存状态={text((helper or {}).get('status'))}；若为running，它只是已结束进程留下的最后快照，不是live证据或终态计数。result保存接受态={text(saved_row_count)}；原API response={text((response or {}).get('status'))}。原任务路径标志：`{json.dumps(saved_flags, ensure_ascii=False)}`。实际model counts：`{json.dumps((model or {}).get('region_metadata', {}).get('counts'), ensure_ascii=False)}`。原failure：`{json.dumps(failure, ensure_ascii=False)}`。

[保存响应](run_001/{LABEL}/response.json)和[result](run_001/{LABEL}/result.json)只在实际存在时为恢复入口；失败若尚未构模或保存result，以上引用不表示文件必定存在。真实[启动记录](production_launch.json)、[helper收据](run_001/execution_receipt.json)和[独立终态审阅](author/independent_terminal_review.md)保留原状态。

{table}

R是输入执行器ON-model的下半模型作用，q_out是加权输出端口位移。total/material/Hu Fy均为固定下半体ON-body有符号弱式合力；保持反力与之相反，镜像完整装配净力和2|Fy|幅值都不能替代局部总压力或合格夹持力。本表只复制已保存值，没有重新求力／积分／差值／比例。

## 实际显示与几何观察

{pictures}

{distance_table}

纯viewer只从新model/state/forces观察，未提供reference。距离是参考(80,30)节点到有限表面的无符号距离；射线null表示无交点，不能当零间隙。绿色射线和距离虚线为几何见证，不是力。镜像只用于显示；全域minJ与自由介质minJ、全域max分量Hu与图示Hu Frobenius范围不同。加载与卸载采样不完全相同，连线分离不能单独证明滞回。新GIF只记录原viewer全N帧，闭窗不再次解码；root原PNG一次QA记录见[像素记录](author/pixel_QA.json)，不存在时不宣称检查完成。

## 原门、计数、资源与身份封存

原cached gates：`{json.dumps((helper or {}).get('cached_production_gates'), ensure_ascii=False)}`。计数原值：`{json.dumps(counts, ensure_ascii=False)}`。F/T开始与完成分开，原invalid_J／回溯／二分属于内部试探，不能当外部重跑；监测只限NativeMean既有别名。

controller18000／helper19000／outer19060秒、viewer最多600共享helper剩余、采样8GiB。outer实际{outer['elapsed_seconds']}秒／childwall{outer['helper_wall_seconds']}秒／treeRSS{outer['peak_sampled_tree_RSS_bytes']}B；helper实际{text((helper or {}).get('elapsed_seconds'))}秒／RSS{text((helper or {}).get('peak_sampled_RSS_bytes'))}B。合作stop和真实child wait，非OS硬cap，无force或延期；旧UTC解析的负耗时不作运行计时证据。

all66bindings unchanged原记录={text(outer.get('all_bindings_unchanged'))}；seal={text((helper or {}).get('output_identity_seal'))}。科学产物身份只继承本次闭helper outputs+stat，闭窗不补数组、CSV、PNG或GIF hash/header/decode。unsealed partial路径：`{json.dumps(unsealed, ensure_ascii=False)}`；若有身份缺口，出版工具必须停止，文档不会虚构完整封存。损坏普通JSON原字节仍保留，解析问题：`{json.dumps(malformed_ordinary, ensure_ascii=False)}`；不将其当成已观察结果。

没有新HP、测试、默认安装、LF重转换或优化。独立参考／局部总压力／有效夹持／释放／稳定性／HF5均不升级，MPM未实现。完整输入回零只说明真实输入端点达到；构模或路径失败不被partial cached门掩盖。旧失败／旧HP／source era历史保持。

## 下一步

{'完整新LF前向生产和实际显示已通过；下一步依据本次真实峰值／关键卸载保存态准备独立HP80/120范围与新资源卡，不能搬移旧几何HP，也不重做已完成接口或完整路径。' if status == 'pass' else '先按真实typed failure、保存partial和资源记录定位最近一个实际原因，不自动修复重跑，不缩短任务或改变工件／材料来取得通过。任何新修订及科学窗口另行明确。'}
'''
    # Do not create dangling links to absent partial artifacts or absent QA.
    for label, relative in [('保存响应', f'run_001/{LABEL}/response.json'), ('result', f'run_001/{LABEL}/result.json'), ('helper收据', 'run_001/execution_receipt.json'), ('像素记录', 'author/pixel_QA.json')]:
        if relative == 'author/pixel_QA.json':
            exists = args.pixel_qa is not None
        else:
            exists = (stage / relative).is_file()
        if not exists:
            records = records.replace(f'[{label}]({relative})', label + '（未产生）')
    prefix = f'''# 2026-10-14：L-FWD1 已实际终态 {status.upper()}

新LF fine完整25目标的唯一零起点API已关闭；source `{BASE}`。实际outer{outer['elapsed_seconds']}秒／treeRSS{outer['peak_sampled_tree_RSS_bytes']}B，result保存接受态{text(saved_row_count)}，真实response={text((response or {}).get('status'))}。{('成功且一次原纯viewer已完成3PNG／真实N帧GIF。' if status == 'pass' else '本卡not_pass，保留实际原因及partial，不自动重跑或虚称完整显示。')}

原固定工件、全部物理／目标／生产门保持，默认文件未改；无新HP/tests/优化/安装。下半体弱式力、几何距离与真实变形用于人工观察，不授压力／有效夹持／释放／稳定性／HF5。旧source卡／失败／参考历史保留。[目标、实际结果和下一步](../{REL}/RESULTS.md)。继续main及固定origin。

---
'''.encode('utf-8')
    histories = []
    for name in FRONTS:
        original = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=root)
        assert raw(root / name) == original
        histories.append((name, original))
    for name, path in archive.items():
        write_new(author / name, raw(path))
    write_new(stage / 'RESULTS.md', records.encode('utf-8'))
    fronts = []
    for name, original in histories:
        current = prefix + original
        assert current.count(original) == 1
        (root / name).write_bytes(current)
        fronts.append(dict(path=name, old_sha256=sha256(original).hexdigest(), new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    record = dict(card='L-FWD1', status='actual_execution_records_written_pass', source_baseline_commit=BASE,
        actual_source_commit=BASE, actual_execution_closed=True, actual_execution_status=status,
        helper_receipt_sha256=pin(helper_file) if helper_file.is_file() else None, launch_sha256=pin(outer_file),
        results_sha256=pin(stage / 'RESULTS.md'), front_history=fronts,
        archived_author_ordinary_files={name: pin(author / name) for name in archive},
        read_actual_ordinary_identities=identities, malformed_ordinary_records=malformed_ordinary,
        declared_binary_identities=scientific, unsealed_partial_stat_only=unsealed,
        scientific_or_media_bytes_headers_hashes_decode=0, scientific_execution_or_replot=False, original_window_closed=True)
    write_new(author / 'execution_documentation_receipt.json', (json.dumps(record, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    write_new(Path(__file__).resolve().parent / 'execution_record_write_receipt.json', (json.dumps(record, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=record['status'], actual_execution_status=status, archived_ordinary_files=len(archive), scientific_bytes_read=False)))


if __name__ == '__main__':
    main()
