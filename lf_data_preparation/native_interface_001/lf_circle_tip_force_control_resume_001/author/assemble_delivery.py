"""Deliver closed FRESUME1 bytes and ordinary records; never run mechanics."""
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfrs1_001')
RUN = BASE/'run_001'
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_resume_001'
PREP = '../lf_circle_tip_force_control_resume_preparation_001/'
DEST = ROOT/REL


def read(path):
    return json.loads(Path(path).read_bytes())


def identity(path):
    raw = Path(path).read_bytes()
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


def copy(source, relative):
    """Only copy existing opaque bytes; no archive or media decoder is used."""
    target = DEST/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert identity(source) == identity(target), 'Delivery bytes differ: '+str(relative)


def write(relative, text):
    target = DEST/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.encode('utf-8').rstrip(b'\n')+b'\n')


def cell(value):
    return '<td>'+escape('未记录' if value is None else str(value))+'</td>'


def table(headers, rows):
    return ('<div class="scroll"><table><thead><tr>'
        +''.join('<th>'+escape(value)+'</th>' for value in headers)
        +'</tr></thead><tbody>'+''.join('<tr>'+''.join(cell(v) for v in row)+'</tr>' for row in rows)
        +'</tbody></table></div>')


def main():
    # Every prerequisite precedes directory creation, copying or repository edits.
    summary = read(AUTHOR/'EXECUTION_RESULT.json')
    assert summary['stage'] == 'L-CTIPFRESUME1' and summary['status'] == 'PASS'
    assert summary['scientific_window_closed'] is True, 'Scientific execution must already be closed'
    assert not DEST.exists(), 'Preserve any existing delivery; no directory replacement'
    for name in ('RESULTS.md', 'USAGE.md', 'NEXT_STEPS.md', 'RECOVERY.md'):
        assert (AUTHOR/name).is_file(), 'Root must finish actual outcome document: '+name
    protocol = read(BASE/'protocol.json')
    installation = read(BASE/'installation_receipt.json')
    seal = read(BASE/'seal_receipt.json')
    qa = read(BASE/'root_qa.json')
    validation = read(RUN/'artifacts/validation_summary.json')
    renderer = read(RUN/'view/renderer_receipt.json')
    assert installation['status'] == 'pass' and len(installation['installed']) == 3
    assert installation['original_source_files_unchanged'] == 55
    assert seal['status'] == 'pass' and seal['attempts'] == 1
    assert identity(BASE/'execution_evidence.zip') == seal['archive']
    assert qa['status'] == 'pass' and qa['pixel_inspections'] == 1 and qa['rerenders'] == 0
    assert qa['image_identity'] == identity(RUN/'view/force_resume.png')
    assert renderer['new_png_count'] == 1 and renderer['scientific_calls'] == 0
    assert validation['all_twelve_methods_passed'] is True
    assert validation['counts'] == dict(real_16cell_paths=7,
        finite_oracle_injection_rejection_calls=37, controlled_partial_counted_on_both_axes=1)
    assert identity(RUN/'artifacts/validation_summary.json') == {
        key:summary['helper']['validation_summary'][key] for key in ('bytes', 'sha256')}
    assert subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == protocol['baseline']
    package = ROOT/'hf_repo/src/hf_eval'
    original = {str(Path(row['path']).resolve()):row for row in protocol['original_production']}
    assert len(original) == 57
    installed = {str(Path(row['path']).resolve()):row for row in installation['installed']}
    expected_names = {'split_guided_force.py', 'native_guided_force.py', 'native_guided_force_resume.py'}
    assert {Path(path).name for path in installed} == expected_names
    assert len(set(original)&set(installed)) == 2
    for path, row in installed.items():
        assert Path(path).parent == package.resolve()
        assert identity(path) == {key:row[key] for key in ('bytes', 'sha256')}
    for path, row in original.items():
        if path not in installed:
            assert identity(path) == {key:row[key] for key in ('bytes', 'sha256')}
    assert {str(path.resolve()) for path in package.rglob('*.py')} == set(original)|set(installed)

    copies = []
    for name in ('RESULTS.md', 'USAGE.md', 'NEXT_STEPS.md', 'RECOVERY.md'):
        copies.append((AUTHOR/name, name))
    for name in ('approved_card.md', 'authorization.json', 'protocol.json'):
        copies.append((BASE/name, name))
    copies.append((RUN/'artifacts/validation_summary.json', 'validation_summary.json'))
    # The original ZIP is the sole scientific payload dependency.  These are
    # ordinary receipts/identity journals, copied separately for immediate review.
    for name in ('execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json',
                 'top_supervision.json', 'outer_supervision.json', 'execution_receipt.json',
                 'installation_receipt.json', 'root_qa.json', 'outer.instances.ndjson'):
        copies.append((BASE/name, 'execution/'+name))
    for name in ('helper_receipt.json', 'tests_supervision.json', 'viewer_supervision.json',
                 'pytest.log', 'pytest.xml', 'helper.instances.ndjson',
                 'tests.instances.ndjson', 'viewer.instances.ndjson'):
        copies.append((RUN/name, 'execution/run_001/'+name))
    for name in ('force_resume.png', 'renderer_receipt.json'):
        copies.append((RUN/'view'/name, 'view/'+name))
    for name in ('test_force_resume.py', 'launch_resume1.py', 'outer_resume1.py',
                 'run_resume1.py', 'render_resume1.py', 'windows_owned_process_sup2.py'):
        copies.append((BASE/name, 'wrapper/'+name))
    for name in ('API_IMPLEMENTATION.json', 'CONTROLLER_IMPLEMENTATION.json',
                 'TEST_IMPLEMENTATION.json', 'WRAPPER_IMPLEMENTATION.json',
                 'API_STATIC_REVIEW.json', 'CONTROLLER_STATIC_REVIEW.json',
                 'TEST_STATIC_REVIEW.json', 'WRAPPER_VIEWER_STATIC_REVIEW.json',
                 'PROTOCOL_ACK.json', 'EXECUTION_ELIGIBILITY.json', 'CANDIDATE_FREEZE.json',
                 'RESULTS_PHYSICS_REVIEW.md', 'RESULTS_PHYSICS_REVIEW.json',
                 'freeze_resume1.py', 'check_eligibility.py', 'review_api.py',
                 'monitor_resume1.py', 'assemble_delivery.py'):
        copies.append((AUTHOR/name, 'author/'+name))
    assert len(copies) == 51 and len({relative for _, relative in copies}) == 51
    for source, _ in copies:
        assert source.is_file(), 'Missing existing deliverable: '+str(source)
    front_pages = [('README.md', REL+'/'), ('docs/CURRENT_STATUS.md', '../'+REL+'/'),
                   ('hf_repo/README.md', '../'+REL+'/')]
    old_front = {}
    for relative, _ in front_pages:
        raw = (ROOT/relative).read_bytes()
        assert b'L-CTIPFRESUME1 **' not in raw[:1500], 'Current banner already exists'
        old_front[relative] = raw

    DEST.mkdir(parents=True)
    for source, relative in copies:
        copy(source, relative)
    # Avoid a second full validation copy inside the closure record.  Its raw
    # identity is retained; the one complete ordinary summary is adjacent.
    thin = {key:value for key, value in summary.items() if key != 'validation'}
    thin.update(schema='L-CTIPFRESUME1-closed-delivery-summary-1.0',
        original_execution_summary=dict(path=(AUTHOR/'EXECUTION_RESULT.json').as_posix(),
            **identity(AUTHOR/'EXECUTION_RESULT.json')),
        validation=dict(path='validation_summary.json', **identity(RUN/'artifacts/validation_summary.json')),
        qualified_scope=validation['qualification'],
        scientific_payload_dependency='execution/execution_evidence.zip; existing raw bytes, never unpacked or resealed by delivery')
    write('result_summary.json', json.dumps(thin, ensure_ascii=False, indent=2, allow_nan=False))

    accepted = []
    for branch in ('direct', 'prefix', 'child', 'grandchild', 'partial'):
        for row in validation['rows'][branch]:
            components = row['force_on_body_N']
            accepted.append([branch, row['original_target_index'], row['fresh_anchor'],
                row['P_target_half_N'], row['body_q_mm'], row['R_input_N'],
                row['load_increment_from_anchor_half_N'], row.get('load_increment_from_root_half_N'),
                row['generalized_force_scale_half_N'], components['total'][0],
                components['material'][0], components['regularization'][0],
                row['minimum_J'], row['max_abs_Hu_per_mm'], row['newton_checks']])
    comparison_rows = [[row['branch'], row['reference_branch'], row['original_target_index'],
        row['P_target_half_N'], row['q_abs_error_mm'], row['physical_displacement_max_error_mm'],
        row['q_and_state_bound_mm'], row['R_abs_error_N'], row['R_bound_N']]
        for row in validation['comparisons']]
    outcomes = [[name, value['status'], value['accepted_count'], json.dumps(value['failure'], ensure_ascii=False)]
                for name, value in validation['paths'].items()]
    links = [('RESULTS.md', '实际目标／过程／结果'), ('USAGE.md', '已安装接口与用法'),
             ('NEXT_STEPS.md', '下一步准备'), ('RECOVERY.md', '恢复说明'),
             ('result_summary.json', '闭卡轻摘要'), ('validation_summary.json', '完整普通验证摘要'),
             ('execution/execution_evidence.zip', '原窗口科学证据ZIP'),
             ('execution/EVIDENCE_MANIFEST.json', '原ZIP成员身份'),
             ('execution/installation_receipt.json', '实际安装字节'),
             ('execution/root_qa.json', '一次实际图像QA'),
             (PREP+'L-CTIPFRESUME1_CARD.md', '原卡／原链接上下文')]
    nav = ' · '.join('<a href="'+escape(href, quote=True)+'">'+escape(label)+'</a>' for href,label in links)
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>L-CTIPFRESUME1 · 力控保存态续载</title>
<style>body{font:16px/1.7 system-ui,sans-serif;max-width:1480px;margin:30px auto;padding:0 22px;color:#182b3b;background:#f5f7fa}header,section{background:white;border:1px solid #d5dee8;border-radius:10px;padding:24px;margin:20px 0}h1{line-height:1.3}a{color:#075d94}img{display:block;width:100%;height:auto}.scroll{overflow-x:auto}table{border-collapse:collapse;white-space:nowrap;min-width:100%}td,th{border-bottom:1px solid #d5dee8;padding:8px;text-align:left}.note{color:#475e71}code{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>
<header><p>2026-10-23 · 已批准唯一执行 · PASS／科学窗口已关闭</p><h1>保留非零绝对q、预载P及原split的力控保存态续载</h1><p>已安装2份修改和1份新源码；其余55份保持原字节。12项有限验证通过，7条16单元／50DOF真实小模型路径、37次有限代数／注入／拒绝调用。正式r9物理条件与原结果保持，本卡没有执行正式r9续载或HP。</p><nav>'''+nav+'''</nav><p class="note">旧fixed父力控入口继续支持q=0起点；新extend_native_guided_force只追加严格增加的绝对有符号半模型载荷。非零q不归零，原lift/w/R原样继承，lift只覆盖不再叠加。段起点P与最初root P0分开：SP仍=max(abs(P),abs(root P0),Ffloor)。完整前缀是谱系，本child只实际执行其fresh段起点和新增后缀。</p></header>
<section><h2>实际分支状态</h2>'''+table(['分支','实际状态','接受态数','failure原值'],outcomes)+'''<p class="note">partial是预先规定的第二次T constraint_failure持久化检查；它保持非零fresh锚点及原父树，不代表物理失稳载荷，不作为成功数值路径。固定父是第7条真实路径，另保普通摘要中的fixed_parent_summary。</p></section>
<section><h2>实际小模型图</h2><a href="view/force_resume.png"><img src="view/force_resume.png" alt="实际小模型变形、P-q、反力、分段误差、收敛及root尺度"></a><p class="note">仅链接本窗口已经生成并检查一次的原PNG。真实结构变形×1，箭头×'''+escape(str(renderer['displacement_arrow_scale']))+'''；网格重合及接近零误差的显示限制见原QA。全部17次force base check及6条trial merit依原renderer记录；没有新绘图、科学数组读取或再次像素检查。</p></section>
<section><h2>原值接受态与力口径</h2>'''+table(['分支','global index','fresh','P_half / N','绝对q / mm','R_input / N','段增量P / N','根增量P / N','SP / N','ON-body total Fx / N','material Fx / N','Hu Fx / N','min J','max |Hu| / mm⁻¹','checks'],accepted)+'''<p class="note">表格直接显示已保存普通JSON原值，不插值、不补未生成状态。1.0根入口没有根增量字段时显示未记录；不伪补新字段。P已含原厚度，是半模型有符号外载；ON-body total Fx与施加P反号，total含material/Hu；R为保持机构平均输入的独立反力。没有把这些弱力认作压力或纯接触承载能力。</p></section>
<section><h2>同原目标的预定功能比较</h2>'''+table(['实际分支','参考分支','global index','P_half / N','|Δq| / mm','全50DOF max |Δu| / mm','q/u界 / mm','|ΔR| / N','R界 / N'],comparison_rows)+'''<p class="note">16组比较均来自原验证摘要；direct/分段同P比较及给q参考分开，完整物理位移差使用四split项math.fsum。fresh状态硬身份与这些预先工程界是两个独立检查，不以误差小替代原始身份和原生产门。</p></section>
<section><h2>恢复和下一步</h2><p>原窗口ZIP为唯一科学payload依赖，含本轮自建夹具、接受缓存、候选58源及完整原字节日志；交付未解包、重封或复制整个candidate树。四份SUP2监督及四本同实例身份日志单独可查；其他start/普通stdout日志留在原ZIP。当前可用能力是经小模型验证的单调力控保存态续载，正式r9下一小增量需另核父态、任务和独立窗口。</p><p>批准卡为历史原字节副本，原pending标题与相对接口／验证链接应按相邻preparation目录上下文阅读；当前状态以本页、RESULTS和USAGE为准。原核、门、正式任务、HP和压力／有效夹持／释放／稳定性资格没有升级。</p></section></html>'''
    write('inspection.html', page)

    banner = ('> 2026-10-23 L-CTIPFRESUME1 **实际状态：PASS**：已安装力控保存态单调续载，保留非零绝对q/P/R/split及root P0尺度。'
        '12项有限验证／7条16单元50DOF路径通过；2旧改+1新增，其余55源原字节保持。'
        '[实际结果／图]({p}RESULTS.md) · [已安装用法]({p}USAGE.md) · [下一步]({p}NEXT_STEPS.md)。'
        '本卡未执行正式r9续载或HP，不授压力、承载极限、释放或稳定性资格。下方为历史状态。\r\n\r\n')
    for relative, prefix in front_pages:
        (ROOT/relative).write_bytes(banner.format(p=prefix).encode('utf-8')+old_front[relative])
    attributes = ROOT/'.gitattributes'
    old_attributes = attributes.read_bytes()
    entry = REL+'/wrapper/windows_owned_process_sup2.py whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof\n'
    if entry.encode() not in old_attributes:
        separator = b'' if not old_attributes or old_attributes.endswith(b'\n') else b'\n'
        attributes.write_bytes(old_attributes+separator+
            ('# Preserve unchanged byte-bound SUP2 for L-CTIPFRESUME1.\n'+entry).encode('utf-8'))
    print(json.dumps(dict(stage='L-CTIPFRESUME1',status='PASS',delivery=DEST.as_posix(),
        base_delivery_files=len(copies)+2, scientific_window_closed=True,
        opaque_archive_copied=True, new_scientific_calls=0, new_media_generation=0,
        repeated_pixel_checks=0, delivery_manifest_owner='root publication stage'),ensure_ascii=False))


if __name__ == '__main__':
    main()
