"""Read saved HF JSON for an external LF study; no HF imports or evaluation."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path


def consume(repo, index_path, output, checkpoint=lambda event: None):
    """Project three saved JSON files into a portable table and a Markdown page."""
    repo = Path(repo).resolve()
    output = (repo / output).resolve()
    output.mkdir(parents=True, exist_ok=False)

    def artifact_path(record):
        if record['path_scope'] != 'repo_relative':
            raise ValueError('This example expects repository-relative artifacts')
        path = (repo / record['path']).resolve()
        path.relative_to(repo)
        return path

    def read(path, expected=None):
        checkpoint('json_read_started')
        raw = path.read_bytes()
        value, pin = json.loads(raw), sha256(raw).hexdigest()
        if expected is not None and pin != expected:
            raise ValueError('Saved JSON identity differs: ' + str(path))
        checkpoint('json_read_completed')
        return value, dict(path=path.relative_to(repo).as_posix(), sha256=pin)

    index, index_id = read((repo / index_path).resolve())
    response, response_id = read(artifact_path(index['linked_response']), index['linked_response']['sha256'])
    source = index['saved_artifacts']['result_file']
    result, result_id = read(artifact_path(source), source['sha256'])
    if response['identity']['result']['sha256'] != result_id['sha256']:
        raise ValueError('Response and result identities differ')
    if len(result['states']) != response['path']['accepted_states']:
        raise ValueError('Response and result accepted-state counts differ')
    reference = response['independent_reference']
    selected = set(reference['matched_state_indices']) if reference['selected_reference_pass'] else set()
    rows = [dict(accepted_row_index=i, original_target_index=s['original_target_index'],
        is_original_target=s['is_original_target'], state_sha256=s['state_sha256'],
        leg=s['leg'], d_mm=s['d'], R_input_N=s['R_input'], q_in_mm=s['q_in'],
        q_out_mm=s['q_out'], minimum_J=s['minimum_J'],
        force_on_lower_body_N=s['workpiece']['force_on_lower_body_N'],
        has_matched_reference=i in selected) for i, s in enumerate(result['states'])]
    table = dict(schema_version='lf-saved-consumption-table-1.0',
        inputs=dict(index=index_id, response=response_id, result=result_id),
        identity=response['identity'], physics=response['physics'], options=response['options'],
        path=response['path'], independent_reference=reference, producer_flags=response['producer_flags'],
        force_semantics=response['force_semantics'], field_scope=response['field_scope'],
        existing_media=index['images'], rows=rows,
        scope='Saved JSON projection only; no new reference, mechanics, formal labels or ranking')
    checkpoint('before_table_write')
    with (output / 'states_table.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(table, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    checkpoint('table_written')
    lines = ['# LF外部研究层：保存结果检查页', '',
        f"生产路径完成：{table['path']['completed']}；接受态：{len(rows)}。", '',
        f"已有参考：{reference['status']}，匹配行 {sorted(selected)}，覆盖 {len(selected)}/{len(rows)}。",
        f"全路径参考通过：{reference['full_path_reference_pass']}。其余行未被本关联参考覆盖。", '',
        'R是半模型输入反力；工件值是下半固定体弱式合力，含材料与Hu，不能当作连续压力或正式有效夹持力。',
        'q_out是加权端口位移，不是表面间隙；minJ是原保存的全局最小值。JSON保留原浮点值，以下仅作显示舍入。', '',
        '| 接受行 | 原目标 | 路段 | d (mm) | R (N) | q_out (mm) | minJ | 材料Fy (N) | Hu Fy (N) | 总Fy (N) | 已匹配参考 |',
        '|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in rows:
        force = row['force_on_lower_body_N']
        values = [row[key] for key in ('d_mm', 'R_input_N', 'q_out_mm', 'minimum_J')]
        values += [force[key][1] for key in ('material', 'regularization', 'total')]
        numbers = ' | '.join(format(value, '.9g') for value in values)
        lines.append(f"| {row['accepted_row_index']} | {row['original_target_index']} | {row['leg']} | {numbers} | {'是' if row['has_matched_reference'] else '未覆盖'} |")
    lines += ['', '## 身份与数值含义', '',
        f"- 几何ID：`{table['identity']['geometry']['geometry_id']}`",
        f"- 任务SHA：`{table['identity']['task_sha256']}`",
        f"- 原result SHA：`{result_id['sha256']}`",
        '- 接受行来自enumerate(result.states)，与原目标序号分别保留。原反力字段为R_input。',
        '- 完整向量、state SHA、物理条件和全部原资格字段见 [states_table.json](states_table.json)。', '',
        '## 五份既有媒体', '', '以下只提供既有链接；本示例没有读取媒体内容、绘图或检查像素。', '']
    for record in table['existing_media']:
        relative = os.path.relpath(artifact_path(record), output).replace('\\', '/')
        lines.append(f"- [{Path(record['path']).name}](<{relative}>)")
    checkpoint('before_review_write')
    with (output / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(lines) + '\n')
    checkpoint('review_written')
    return table


def main(argv=None, checkpoint=lambda event: None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True, help='Explicit restored repository root')
    parser.add_argument('--index', type=Path, required=True, help='Saved light index, relative to --repo')
    parser.add_argument('--output', type=Path, required=True, help='New output directory, relative to --repo or absolute')
    args = parser.parse_args(argv)
    table = consume(args.repo, args.index, args.output, checkpoint)
    print(json.dumps(dict(rows=len(table['rows']), reference=table['independent_reference']['status'])))
    return table


if __name__ == '__main__':
    main()
