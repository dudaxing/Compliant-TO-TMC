"""Saved JSON/source-only diagnosis and current-state documentation."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import ast
import json

root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
stage=root/'lf_data_preparation/native_interface_001/batch_forward_001'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
worker=stage/'reference_author/audit_batch_case.py'
tree=ast.parse(worker.read_bytes())
used=sorted({n.slice.value for n in ast.walk(tree) if isinstance(n,ast.Subscript)
    and isinstance(n.value,ast.Name) and n.value.id=='model'
    and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str)})
cases={}
for label in ('canonical','native_fine'):
    result=read(stage/'run_001'/label/'result.json')
    metadata_file=stage/'run_001'/label/result['model']['descriptor_path']
    fields=read(metadata_file)['arrays']['fields']
    missing=sorted(set(used)-set(fields))
    assert missing==['coords'] and len(fields)==23 and 'coordinates' in fields
    cases[label]=dict(metadata_file=metadata_file.relative_to(root).as_posix(),metadata_sha256=sha(metadata_file),
        declared_fields=fields,wrapper_model_subscripts=used,missing_subscripts=missing,
        coordinates_shape=fields['coordinates']['shape'],actual_states=len(result['states']))
protocol=read(stage/'reference_protocol_canonical.json')
launch=read(stage/'reference_canonical_launch.json')
receipt=read(stage/'run_001/audit/canonical/execution_receipt.json')
lifecycle=read(stage/'run_001/audit/canonical/lifecycle.json')
assert launch['status']==receipt['status']==lifecycle['status']=='not_pass'
assert launch['exit_code']==1 and launch['invocations']==1 and launch['all_bindings_unchanged']
assert receipt['HP_calls_started']==receipt['HP_calls_completed']==receipt['accepted_states']==0
assert receipt['error']=="KeyError('coords')"
assert not (stage/'reference_protocol_native_fine.json').exists()
assert not (stage/'run_001/audit/native_fine').exists() and not (stage/'run_001/view').exists()
production=read(stage/'run_001/execution_receipt.json')
assert production['status']=='pass'
assert all(sha(root/name)==pin for name,pin in production['outputs'].items())
assert all(sha(root/name)==pin for name,pin in production['bindings'].items())
now=datetime.now(timezone.utc).isoformat()
diagnosis=dict(schema_version='native-batch-reference-failure-diagnosis-1.0',status='closed_not_pass',created_utc=now,
    error=receipt['error'],failure_location='reference_author/audit_batch_case.py:125, added node-count check',
    actual_new_HP_calls=0,accepted_states_audited=0,checks_completed=receipt['checks_completed'],
    helper_seconds=receipt['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],actual_exit_code=1,
    production_unchanged=True,worker_sha256=sha(worker),protocol_sha256=sha(stage/'reference_protocol_canonical.json'),
    cases=cases,root_cause='Wrapper introduced coords, while both declared models and native writer use coordinates.',
    review_gap='Source inheritance and dimensions were reviewed, but each added model subscript was not compared with the actual declared field names.',
    scope='JSON/AST/raw-file identity only, no array loading or mechanics evaluation.',
    later_stages=dict(native_fine_reference='not_frozen_not_executed',saved_views='not_frozen_not_executed'),
    next='Prepare minimal V2 wrapper and complete field/state/attribute source review, then seek a separately reviewed new card; no retry of this closed card.')
write(stage/'reference_failure_diagnosis.json',diagnosis)
progress=read(stage/'closure_progress.json')
progress.update(status='production_pass_reference_canonical_closed_not_pass',created_utc=now,
    reference_canonical=dict(status='closed_not_pass',actual_exit_code=1,error=receipt['error'],HP_started=0,HP_completed=0),
    reference_native_fine='not_executed',saved_views='not_executed',
    next='Review minimal V2 wrapper and new card; preserve all closed production and failed-reference evidence.')
write(stage/'current_progress_002.json',progress)
header=('## 当前：真实两例生产通过，新的参考包装读取失败\n\n'
    f'UTC {now}：canonical 新参考卡已一次终止，exit1，新增节点数检查读取不存在的 `coords` 字段；真实23字段中的名称是 `coordinates`。失败前新HP=0、参考接受态=0、检查11项，helper约1.498秒/outer约1.880秒。fine参考与新图未执行。两例0.025 mm生产、28核心源与原54份输出字节不变，原生产资格仍通过。\n\n'
    '本张参考卡已关闭，不修复后重试；准备独立V2最小包装、逐项字段/状态/属性核对和新卡，再单独确认执行。两设计不同，不作网格收敛或排名；HF5整体尚未完成。'
    '[当前诊断](../lf_data_preparation/native_interface_001/batch_forward_001/reference_failure_diagnosis.json)；'
    '[实际阶段报告](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md)。以下为历史记录，当前以上方及真实终态回执为准。\n\n---\n\n')
changes={}
for file,prefix in [
    (root/'docs/CURRENT_STATUS.md',header),
    (root/'docs/NATIVE_BATCH_INTERFACE.md',header),
    (stage/'RESULTS.md',header.replace('../lf_data_preparation/native_interface_001/batch_forward_001/',''))]:
    previous=file.read_bytes();before=sha(file)
    file.write_bytes(prefix.encode('utf-8')+previous)
    changes[file.relative_to(root).as_posix()]=dict(before=before,after=sha(file),operation='prepend current closed-failure state, retain history raw')
write(stage/'reference_failure_documentation_install.json',dict(status='recorded',created_utc=now,files=changes,science_calls=0))
(stage/'closure_author/record_reference_failure.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':'closed_not_pass_recorded','actualHP':0,'production_unchanged':True,'missing_model_field':missing}))
