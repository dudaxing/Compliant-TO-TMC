"""Freeze a future ordinary packet only after actual M-UNLOAD1 publication exists."""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import argparse
import json

from preparation_common import REL,CARD,PARENT,MANIFEST,APPENDED,TARGETS
from preparation_common import git,raw,read,sha,new,canonical_hash,prior_base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--publication-receipt',type=Path,required=True)
    args = parser.parse_args(); root = args.repo.resolve(); here = Path(__file__).resolve().parent
    base,proof = prior_base(args.publication_receipt.resolve())
    assert git(root,'rev-parse','HEAD').decode().strip() == base and not git(root,'status','--porcelain')
    assert not (root/REL).exists() and not (here/'frozen_packet').exists()
    manifest_raw = raw(root/MANIFEST); entries = {row['path']:row for row in json.loads(manifest_raw)['files']}
    assert proof['manifest_sha256'] == sha256(manifest_raw).hexdigest() and len(entries) == proof['ordinary_manifest_files']
    assert sum(row['bytes'] for row in entries.values()) == proof['ordinary_manifest_bytes']
    parent_file = root/PARENT/'run_001/unloaded_alpha_half/result.json'; parent = read(parent_file)
    model_file = parent_file.parent/parent['model']['descriptor_path']; model = read(model_file)
    selected = parent['states'][1]; source_task = model['task']; task = read(here/'proposed_task.json')
    assert parent['status'] == 'success' and parent['path_completed'] and len(parent['states']) == 2
    assert selected['original_target_index'] == 16 and selected['d'] == 1.05
    assert len(source_task['path']['targets_mm']) == 17 and source_task['path']['targets_mm'][-1] == 1.05
    restored = deepcopy(task); restored['path']['targets_mm'] = deepcopy(source_task['path']['targets_mm'])
    assert restored == source_task and task['path']['targets_mm'] == source_task['path']['targets_mm']+APPENDED
    assert canonical_hash(source_task) == parent['task_sha256']
    review = read(here/'source_candidate_review.json')
    assert review['authorized'] is review['executed'] is False and review['blocking_findings'] == []
    assert all(sha(here/name) == pin for name,pin in review['candidate_source_SHA256'].items())
    packet = here/'frozen_packet'
    for name in ('execute_unload.py','launch_unload.py','proposed_task.json'):
        new(packet/name,raw(here/name))
    for name in ('SOURCE_AUTHOR_NOTES.md','source_author_receipt.json','wrapper_input_contract.json','source_candidate_review.json','source_candidate_review.md'):
        new(packet/'author'/name,raw(here/name))
    new(packet/'author/previous_execution_publication_receipt.json',raw(args.publication_receipt.resolve()))
    new(packet/'author/TAIL_SCOPE_RECOMMENDATION.md',raw(here.parent/'MUNLOAD1_execution_review_001/TAIL_SCOPE_RECOMMENDATION.md'))
    paragraphs = raw(here/'M-UNLOAD2_DRAFT.md').decode('utf-8').split('\n\n')
    paragraphs[0] = paragraphs[0].replace('未冻结外部草稿','源码准备，尚未授权／执行')
    paragraphs[1] = '外部源码／协议准备已冻结，尚未授权／执行。前置M-UNLOAD1真实PASS已发布并恢复，实际基线`'+base+'`及其publication receipt已绑定；本卡新准备发布／恢复状态以随后实际收据为准，不继承旧授权。目录`'+REL+'`。'
    card = '\n\n'.join(paragraphs)
    new(packet/'M-UNLOAD2_CARD.md',card.encode('utf-8'))
    new(packet/'PREPARATION_RESULTS.md',('''# M-UNLOAD2源码准备结果

仅普通source/task/result/stat及AST；没有API、测试、模型、F/T、HP、NPZ/gzip/CSV/媒体解码或绘图，也没有默认安装。已成功1.05末态是唯一起点；保原17任务前缀只追加旧M-CYCLE1尾段八目标，形成新25目标task。当前接口支持批量严格append；只适配薄包装身份、索引和预算。

新controller9000／view600／helper10200／outer10260秒、采样8GiB，首错停止、真实partial、闭窗不补科学hash；N至少9且允许原bisection增加。到零仅输入endpoint，不認释放、完整从零路径或压力／有效夹持／HF5资格。原失败祖先完整保留，HP与测试／安装本阶段均零。见[具体卡](M-UNLOAD2_CARD.md)与[父实际结果](../saved_extension_003/RESULTS.md)。
''').encode('utf-8'))
    new(packet/'author/front_prefix.md',('''# 最新准备：M-UNLOAD2从成功1.05末态批量卸载至零

保17任务前缀只append `[1,.9,.8,.75,.65,.5,.25,0]`，25完整task目标；请求suffix9目标，global16..24，真实N含原bisection。默认API及原pure viewer复用，不改核心、不重做测试、安装或HP。

源码准备未授权／执行；新controller9000／view600／helper10200／outer10260秒、采样8GiB，首错停、无重试／修复重跑／延期／force。零仅输入endpoint，原失败和完整路径／压力／有效夹持／HF5缺口保留。见[M-UNLOAD2卡](../lf_data_preparation/native_interface_001/saved_extension_004/M-UNLOAD2_CARD.md)、[准备说明](../lf_data_preparation/native_interface_001/saved_extension_004/PREPARATION_RESULTS.md)。

---

''').encode('utf-8'))
    parent_protocol = read(root/PARENT/'protocol.json'); helper = read(root/PARENT/'run_001/execution_receipt.json')
    assert helper['status'] == 'pass' and helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    ordinary = {path.relative_to(root).as_posix() for path in (root/'hf_repo/src/hf_eval').glob('*.py')}
    ordinary.update(parent_protocol['pure_view_bindings'])
    ordinary.update({'hf_repo/pyproject.toml',PARENT+'/protocol.json',PARENT+'/production_launch.json',PARENT+'/run_001/execution_receipt.json',
        parent_file.relative_to(root).as_posix(),model_file.relative_to(root).as_posix(),
        (model_file.parent/model['source_geometry']['snapshot']['descriptor']).relative_to(root).as_posix(),
        (parent_file.parent/selected['descriptor_path']).relative_to(root).as_posix()})
    bindings = {}
    for name in sorted(ordinary):
        pin = sha(root/name); assert pin == entries[name]['sha256']; bindings[name] = pin
    inherited = {}
    npzs = [model_file.parent/model['arrays']['path'],model_file.parent/model['source_geometry']['snapshot']['arrays']]
    npzs += [parent_file.parent/selected[key]['path'] for key in ('state','forces','tangents','matrix')]
    for path in npzs:
        name = path.relative_to(root).as_posix(); row = entries[name]; produced = helper['outputs'][name]
        assert path.suffix == '.npz' and produced == dict(sha256=row['sha256'],bytes=row['bytes']) and path.stat().st_size == row['bytes']
        bindings[name] = row['sha256']; inherited[name] = dict(row,basis='Closed MUNLOAD1 true output seal + published manifest; preparation stat only')
    artifacts = {path.relative_to(packet).as_posix():sha(path) for path in packet.rglob('*') if path.is_file()}
    bindings.update({REL+'/'+name:pin for name,pin in artifacts.items()})
    settings = parent['settings'] | {'time_limit_seconds':9000.}
    protocol = dict(schema_version='saved-native-default-unload-card-1.0',card=CARD,source_baseline_commit=base,prepared=True,authorized=False,executed=False,
        bindings=bindings,inherited_NPZ_bindings=inherited,parent_result=parent_file.relative_to(root).as_posix(),parent_protocol=PARENT+'/protocol.json',
        task_file=REL+'/proposed_task.json',candidate_directory=REL+'/run_001/unloaded_alpha_half',view_directory=REL+'/run_001/view',
        selected_state_index=1,selected_state_sha256=selected['state_sha256'],targets_mm=TARGETS,original_target_indices=list(range(16,25)),
        original_full_task_targets_mm=source_task['path']['targets_mm'],extended_full_task_targets_mm=task['path']['targets_mm'],
        task_sha256=canonical_hash(task),source_task_sha256=parent['task_sha256'],gates=parent_protocol['gates'],settings=settings,
        options=parent_protocol['options'],pure_view_bindings=parent_protocol['pure_view_bindings'],viewer_source=parent_protocol['viewer_source'],
        controller_seconds=9000,view_seconds=600,sampled_RSS_bytes=8*1024**3,
        phases=dict(production=dict(helper_seconds=10200,outer_seconds=10260,argv=[REL+'/execute_unload.py','--repo','.', '--protocol',REL+'/protocol.json'])),
        expected_accepted_states_minimum=9,expected_original_targets_mm=TARGETS,expected_API_calls=1,expected_fresh_anchor=True,
        production_decoded_NPZ_files=2,production_descriptor_fields=6,initial_K=None,archive_count_measured_by_dynamic_hooks=False,
        new_tests_candidate_copies_default_installations_HP=0,postrun_new_PNG_pixel_QA_maximum=3,new_GIF_postrun_decode=0,
        input_reference_scope='No matched new suffix reference; old point references retain their original result identity',
        previous_execution_publication_proof_sha256=sha(args.publication_receipt.resolve()),
        full_original_path_completed=False,full_extended_path_completed=False,pressure_qualified=False,clamp_qualified=False,HF5_qualified=False)
    new(packet/'protocol.json',protocol); artifacts['protocol.json'] = sha(packet/'protocol.json')
    new(here/'frozen_preparation_receipt.json',dict(status='frozen_ordinary_preparation_not_authorized_not_executed',card=CARD,prepared=True,authorized=False,executed=False,
        source_baseline_commit=base,protocol_sha256=artifacts['protocol.json'],artifact_SHA256=artifacts,bindings=len(bindings),inherited_stat_only_NPZ=6,
        scientific_binary_byte_reads=0,HF_import_tests_science_or_plot=0,formal_writes=0))
    print(json.dumps(dict(status='ordinary_packet_frozen',protocol_sha256=artifacts['protocol.json'],source_baseline_commit=base,bindings=len(bindings),formal_writes=0)))


if __name__ == '__main__': main()
