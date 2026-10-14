"""Write L-LINK1 ordinary closure documents after the real terminal; no mechanics/media reads."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXTERNAL = Path(__file__).resolve().parent
BASE = '4fd70556402347c73029cf7070217efaf7a4ea13'
REL = 'lf_data_preparation/native_interface_001/lf_link_001'
STAGE = ROOT / REL
ALLOWED = {'.json', '.md', '.py', '.txt', '.log'}

def raw(path):
    assert path.suffix.lower() in ALLOWED
    return path.read_bytes()

def sha(path):
    return sha256(raw(path)).hexdigest()

def read(path):
    return json.loads(raw(path))

def new(path, content):
    with path.open('xb') as stream:
        stream.write(content)

def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    launch, helper = read(STAGE/'link_launch.json'), read(STAGE/'run_001/execution_receipt.json')
    assert launch['status'] == helper['status'] == 'pass' and launch['invocations'] == 1 and launch['exit_code'] == 0
    assert helper['installation_complete'] is True and helper['unit_tests_run'] == 16 and helper['unit_reference_calls'] == 23
    assert len(helper['outputs']) == 67 and helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    assert sha(ROOT/'hf_repo/src/hf_eval/native_response.py') == helper['actual_default_SHA256'] == helper['candidate_SHA256']
    review = read(EXTERNAL/'actual_execution_review.json')
    assert review['status'].startswith('pass') and not review['blocking_findings']
    archive = {
        'root_terminal_confirmation.json': 'root_terminal_confirmation.json',
        'root_terminal_confirmation_initial_count_serialization.json': 'root_terminal_confirmation_initial_count_serialization.json',
        'actual_execution_review.json': 'independent_terminal_review.json',
        'actual_execution_review.md': 'independent_terminal_review.md',
        'publisher_execution.py': 'publisher_execution.py',
        'CLOSURE_TOOLS_SOURCE_NOTES.md': 'CLOSURE_TOOLS_SOURCE_NOTES.md',
        'closure_tools_author_receipt.json': 'closure_tools_author_receipt.json',
        'closure_tools_source_review.json': 'closure_tools_source_review.json',
        'closure_tools_source_review.md': 'closure_tools_source_review.md',
        'write_execution_records.py': 'write_execution_records.py',
        'RESULTS.template.md': 'RESULTS.template.md',
    }
    assert all((EXTERNAL/name).is_file() and not (STAGE/'author'/target).exists() for name,target in archive.items())
    results = raw(EXTERNAL/'RESULTS.template.md').rstrip()+b'\n'
    new(STAGE/'RESULTS.md', results)
    pins = {}
    for name, target in archive.items():
        new(STAGE/'author'/target, raw(EXTERNAL/name))
        pins[target] = sha(STAGE/'author'/target)
    prefix = '''# 2026-10-15：L-LINK1 实际 PASS，公共摘要已接入2／25参考

直接人工批准后唯一执行已闭卡：16个元数据测试方法／23次私有匹配调用通过，真实公共摘要一次、response／轻索引各一次，单文件native_response.py已安装。新响应明确matched_partial、indices13／16、selected_reference_pass=true，accepted/full_path参考通过仍false；原25目标0→1.20→0 mm完成及原物理、结果与五媒体保持。本次无新求解、F／T、HP或绘图。

[目标、实现、实际效果和限制](../lf_data_preparation/native_interface_001/lf_link_001/RESULTS.md) · [关联响应](../lf_data_preparation/native_interface_001/lf_link_001/run_001/linked_response.json) · [五媒体轻索引](../lf_data_preparation/native_interface_001/lf_link_001/run_001/light_index.json)。峰值原输入反力0.2436576873 N，下半工件弱式Fy=0.0585119885 N；它不是连续压力或已认证有效夹持力。outer1.9211秒／tree RSS35,913,728 B，实际封存67份普通输出，原额度内PASS。

下一步优先由外部研究层消费紧凑响应和明确覆盖，再根据结果安排必要参考或跨几何比较；完整25态独参、压力／有效夹持／释放／稳定性、所有列、一般LF／HF5与MPM仍未完成。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。推送与恢复另核真实交付回执。

下方完整保留4fd7055的原raw历史连续一次；旧“待批准／未执行”和旧API未关联说明仅表示历史阶段。

---
'''.encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        prior = subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        assert raw(ROOT/name) == prior
        current = prefix+prior
        assert current.count(prior) == 1
        (ROOT/name).write_bytes(current)
        history.append(dict(path=name,old_sha256=sha256(prior).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(current),old_raw_contiguous_once=True))
    source = {f'{REL}/{name}':sha(STAGE/name) for name in ('protocol.json','link_launch.json','link_stdout.log',
        'run_001/execution_receipt.json','run_001/linked_response.json','run_001/light_index.json','run_001/tests_summary.json','run_001/tests_stdout.txt')}
    receipt = dict(schema_version='LLINK1-execution-documentation-receipt-1.0',card='L-LINK1',
        status='ordinary_documentation_written_after_real_terminal',source_baseline_commit=BASE,
        actual_execution_closed=True,actual_execution_status=helper['status'],actual_counts=helper['calls'],
        actual_unit_tests=16,actual_private_reference_calls=23,actual_helper_sealed_outputs=67,
        root_confirmation_sha256=pins['root_terminal_confirmation.json'],terminal_review_sha256=pins['independent_terminal_review.json'],
        source_record_SHA256=source,front_history=history,archived_ordinary_SHA256=pins,results_SHA256=sha(STAGE/'RESULTS.md'),
        scientific_postrun_reads_hashes_decodes_imports_tests_solver_plot_pixels=0,
        publication_confirmed_by_writer=False,created_utc=datetime.now(timezone.utc).isoformat())
    new(STAGE/'author/execution_documentation_receipt.json',(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=receipt['status'],fronts_updated=2,archive_files=len(pins),results_SHA256=receipt['results_SHA256'])))

if __name__ == '__main__':
    main()
