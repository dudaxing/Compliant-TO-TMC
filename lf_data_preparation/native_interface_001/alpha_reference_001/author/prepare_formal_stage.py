"""Save the concrete reviewed preparation and preserve both previous front documents."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/alpha_reference_001'
STAGE = ROOT / REL
BASE = '6c17633c59315490b825fdcc289e49f58e27fcef'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def new_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def main():
    git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == BASE and not git('status', '--porcelain')
    assert not STAGE.exists()
    for name in ('candidate_math_resource_review.json', 'candidate_input_protocol_review.json'):
        review = read(HERE / name)
        assert review['status'] == 'pass_static_candidate_review_not_executed'
        assert review['candidate_SHA256'] == sha(HERE / 'execute_alpha_reference.py')
        assert review['protocol_SHA256'] == sha(HERE / 'protocol.json')
        assert review['launcher_SHA256'] == sha(HERE / 'launch_reference.py')
    STAGE.mkdir()
    (STAGE / 'author').mkdir()
    root_files = ('execute_alpha_reference.py', 'launch_reference.py', 'protocol.json', 'M-AREF1_CARD.md', 'PREPARATION_RESULTS.md')
    author_files = ('REFERENCE_REUSE_SOURCE_REVIEW.md', 'REFERENCE_REUSE_SOURCE_REVIEW.json',
        'INPUT_SCOPE_REVIEW.md', 'input_scope_review.json', 'input_contract_seed.json',
        'COST_AND_GATES_REVIEW.md', 'cost_and_gates_review.json',
        'CANDIDATE_MATH_RESOURCE_REVIEW.md', 'candidate_math_resource_review.json',
        'CANDIDATE_INPUT_PROTOCOL_REVIEW.md', 'candidate_input_protocol_review.json',
        'source_author_receipt.json', 'SOURCE_AUTHOR_NOTES.md',
        'freeze_protocol.py', 'prepare_formal_stage.py', 'deliver_preparation.py', 'write_cost_and_gates_review.py')
    for name in root_files:
        new_bytes(STAGE / name, (HERE / name).read_bytes())
    for name in author_files:
        new_bytes(STAGE / 'author' / name, (HERE / name).read_bytes())
    previous = Path('D:/hf-native-workpiece-api-author-20261012/MINTEGRATE1_execution_review_001/execution_publication_receipt.json')
    assert read(previous)['published_commit'] == BASE
    new_bytes(STAGE / 'author/previous_publication_receipt.json', previous.read_bytes())
    head = '''# 当前接续：M-AREF1两态独立参考已准备，未执行

整体目标仍为独立HF有限变形／TMC前向评价：读取普通LF几何，在明确任务下给出实际变形、反力和可解释工件作用，供外部研究层比较；HF不优化、不调用dmftd，MPM暂不实现，main、既定origin、science0.5.0保持。

默认保存态续算已由M-INTEGRATE1安装，25项有限兼容测试实际PASS闭卡并发布6c17633。新alpha5e−7仍是父M-ALPHA1 NOT_PASS／14加载态，加M-RESUME1原1.20→1.15 mm短段success；父子不拼为原一次完整路径通过。原两态R0.37865427196005513→0.3470376815403639 N，下半工件total Fy0.12492121630032427→0.10671287553103108 N；3PNG／2帧实际GIF保留，新alpha无HP。

本轮完成三份只读源／普通JSON审阅及具体M-AREF1候选：旧第0态零初态假设不适合非零续算峰值，按真实原索引13／14继承原B850／aa86数学，raw科学summary保持，顶层明确映射child0／1。原15门、分母、floor、PORT方向与11依赖原字节保持。仅两个接受态4次新HP；完整13440单元27378DOF，三力／声明方向切线／CSC组装身份／KKT与原工件投影；不是独立全部切线列或压力／有效夹持资格。

具体卡一次helper900／outer960秒、采样8GiB，首错停，无测试、重试、修复重跑、延期、force、新生产F／T、模型／平衡或图。旧参考只有24态总耗时，无逐态记录；窗口为保守规划。当前未获本卡直接批准，未importHF、未读取NPZ原字节／解码、未执行HP。10份NPZ的准备pin继承已发布清单／原实际回执，未来批准后核原字节。

连续总压力／有效夹持、父子全路径参考关联、一般LF输入可靠性、移动／摩擦与其他形状完整验证、网格／域／参数稳定性、全部切线列及HF5仍未完成。独立两态结果产生后再决定最小下一步，不自动扩展范围。

[具体卡](../lf_data_preparation/native_interface_001/alpha_reference_001/M-AREF1_CARD.md) · [准备结果与原实际变形](../lf_data_preparation/native_interface_001/alpha_reference_001/PREPARATION_RESULTS.md) · [默认入口用法](NATIVE_EVALUATION_INTERFACE.md)

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
    artifacts = {path.relative_to(ROOT).as_posix(): sha(path) for path in STAGE.rglob('*') if path.is_file()}
    receipt = dict(status='prepared_static_review_only', source_baseline_commit=BASE, authorized=False, executed=False,
        card='M-AREF1', artifact_SHA256=artifacts, front_history=history,
        source_or_default_runtime_changes=0, new_NPZ_byte_reads_HF_tests_HP_plots=0)
    new_bytes(STAGE / 'author/preparation_receipt.json', (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=receipt['status'], stage_files=len(artifacts)+1, fronts=2,
        protocol_sha256=sha(STAGE / 'protocol.json')), ensure_ascii=False))


if __name__ == '__main__':
    main()
