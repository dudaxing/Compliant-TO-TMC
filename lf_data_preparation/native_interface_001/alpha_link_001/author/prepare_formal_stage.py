"""Save only the reviewed M-ALINK1 candidate and preserve both previous front texts."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
STAGE = ROOT / REL
BASE = '84c67e48ba61548a1c15d2c049870678ef58f573'
PROOF = Path('D:/hf-native-workpiece-api-author-20261012/MAREF1_execution_review_001/execution_publication_receipt.json')
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def new_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def main():
    git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == BASE and not git('status', '--porcelain')
    assert not STAGE.exists()
    for name in ('candidate_scope_resource_review.json', 'candidate_input_protocol_review.json'):
        review = read(HERE / name)
        assert review['status'] == 'pass_static_candidate_review_not_executed'
        assert review['candidate_SHA256'] == sha(HERE / 'execute_alpha_link.py')
        assert review['protocol_SHA256'] == sha(HERE / 'protocol.json')
        assert review['launcher_SHA256'] == sha(HERE / 'launch_link.py')
    STAGE.mkdir()
    (STAGE / 'author').mkdir()
    for name in ('execute_alpha_link.py', 'launch_link.py', 'protocol.json', 'M-ALINK1_CARD.md', 'PREPARATION_RESULTS.md'):
        new_bytes(STAGE / name, (HERE / name).read_bytes())
    author_files = ('INPUT_SCOPE_REVIEW.md', 'input_scope_review.json', 'input_contract_seed.json',
        'SOURCE_SCOPE_AND_FLAGS_REVIEW.md', 'source_scope_and_flags_review.json',
        'SOURCE_AUTHOR_NOTES.md', 'source_author_receipt.json',
        'CANDIDATE_SCOPE_RESOURCE_REVIEW.md', 'candidate_scope_resource_review.json',
        'CANDIDATE_INPUT_PROTOCOL_REVIEW.md', 'candidate_input_protocol_review.json',
        'freeze_protocol.py', 'prepare_formal_stage.py', 'deliver_preparation.py')
    for name in author_files:
        new_bytes(STAGE / 'author' / name, (HERE / name).read_bytes())
    assert read(PROOF)['published_commit'] == BASE
    new_bytes(STAGE / 'author/previous_publication_receipt.json', PROOF.read_bytes())
    head = '''# 当前接续：M-ALINK1两态API关联候选已准备，未执行

整体目标仍为独立HF有限变形／TMC前向评价，读取普通LF几何，在明确任务下给出实际变形、反力及可解释工件作用供外部研究层比较；HF不优化、不调用dmftd，MPM暂不实现，main、既定origin、science0.5.0保持。

M-AREF1已实际PASS闭卡并发布84c67e4、异地恢复验收：两个alpha5e−7接受态／4HP、原15门、193.3503027秒／树RSS采样1278435328B、161495检查。原M-RESUME1仅1.20→1.15 mm短段success，父M-ALPHA1 NOT_PASS／14加载态／time_limit保持，不拼原一次完整路径。原R0.37865427196005513→0.3470376815403639 N、下半工件total Fy0.12492121630032427→0.10671287553103108 N，原三PNG／两帧GIF保持。

最近准备M-ALINK1薄关联：默认summarize_saved_native_result和writer各复用一次，新增linked_response／light_index／receipt，同两态child0/1与原13/14明确对应。reader已有continuation支持，无需改默认源码。将来accepted_reference_pass/full_path_reference_pass为true只指child两态suffix；full_original两个flags仍false、target_response=null、父failure和producer flags保持。原response/view/图不回写，原view reference_available=false保绘制时事实，不授全列HP／压力／有效夹持／HF5。

拟绑定30普通JSON／来源／原媒体身份，一次helper180／outer240秒、采样8GiB，首错停止、无重试／修复重跑／延期／force。未来API读5JSON、核12源码和原三PNG／GIF字节，不读数组／科学gzip、无新F/T/HP/平衡/测试/图。本轮只源码／普通JSON／stat准备：未调用API或HF，未读取媒体字节、NPZ/gzip，尚无新增响应；需新直接批准，M-AREF1余时不能续用。

默认保存态续算有限25测试PASS保持。父子全路径参考覆盖、连续材料+Hu总压力／有效夹持、一般LF几何可靠性、移动／摩擦与其他形状完整验证、网格／域／参数稳定性、独立全部切线列及HF5仍未完成。

[具体卡](../lf_data_preparation/native_interface_001/alpha_link_001/M-ALINK1_CARD.md) · [准备结果与原图](../lf_data_preparation/native_interface_001/alpha_link_001/PREPARATION_RESULTS.md) · [已有实际参考](../lf_data_preparation/native_interface_001/alpha_reference_001/RESULTS.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.replace('\n', '\r\n').encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        path = ROOT / name
        prior = git('show', BASE + ':' + name)
        assert path.read_bytes() == prior
        raw = head + prior + b'\r\n</details>\r\n'
        assert raw.count(prior) == 1
        path.write_bytes(raw)
        history.append(dict(path=name, old_sha256=sha256(prior).hexdigest(), new_sha256=sha(path),
            history_start_byte=len(head), history_end_byte_exclusive=len(head)+len(prior)))
    artifact_pins = {path.relative_to(ROOT).as_posix(): sha(path) for path in STAGE.rglob('*') if path.is_file()}
    value = dict(status='prepared_static_review_only', card='M-ALINK1', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, artifact_SHA256=artifact_pins, front_history=history,
        default_runtime_changes=0, media_byte_reads_array_gzip_HF_API_tests_HP_plots=0)
    new_bytes(STAGE / 'author/preparation_receipt.json', (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=value['status'], stage_files=len(artifact_pins)+1,
        protocol_sha256=sha(STAGE / 'protocol.json'), fronts=2), ensure_ascii=False))


if __name__ == '__main__':
    main()
