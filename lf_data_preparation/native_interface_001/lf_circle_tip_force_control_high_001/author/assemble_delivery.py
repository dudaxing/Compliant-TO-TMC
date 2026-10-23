"""Deliver closed HIGH1 ordinary records and existing raw evidence; no science."""
from html import escape
import json
from pathlib import Path
import shutil


ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = Path('D:/hfh1_001')
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_001'
PREP_REL = '../lf_circle_tip_force_control_high_preparation_001/'
DEST = ROOT / REL

# This must precede every directory creation, copy and repository edit.
summary = json.loads((AUTHOR / 'EXECUTION_RESULT.json').read_bytes())
assert summary['scientific_window_closed'] is True, 'Wait for the closed scientific window'
assert summary['production_sources_unchanged'] == 57
assert summary['stage'] == 'L-CTIPFHIGH1'
assert not DEST.exists(), 'Do not replace an existing delivery'
for name in ('RESULTS.md', 'NEXT_STEPS.md', 'RECOVERY.md', 'FUNCTION_STATUS_AND_USAGE.md'):
    assert (AUTHOR / name).is_file(), 'Root must finish the actual outcome documents first: ' + name


def copy(source, relative):
    """Copy existing bytes only; archives and media are never decoded."""
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert source.read_bytes() == target.read_bytes()


def copy_if_present(source, relative):
    if source.is_file():
        copy(source, relative)
        return True
    return False


def write(relative, text):
    target = DEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.strip().encode('utf-8') + b'\n')


def shown(value):
    return '未记录' if value is None else str(value)


def cell(value):
    return '<td>' + escape(shown(value)) + '</td>'


def body_x(row, name):
    vector = (row.get('force_on_body_N') or {}).get(name)
    return vector[0] if vector is not None else None


DEST.mkdir(parents=True)
for name in ('approved_card.md', 'authorization.json', 'protocol.json', 'source_binding.json', 'observer_binding.json'):
    copy(BASE / name, name)
copy(AUTHOR / 'EXECUTION_RESULT.json', 'result_summary.json')
copy(AUTHOR / 'FUNCTION_STATUS_AND_USAGE.md', 'USAGE.md')
for name in ('RESULTS.md', 'NEXT_STEPS.md', 'RECOVERY.md'):
    copy(AUTHOR / name, name)
has_comparison = copy_if_present(BASE / 'run_001/comparison.json', 'comparison.json')

for name in ('science_high1.py', 'compare_high1.py', 'view_high1.py', 'helper_high1.py',
             'launch_high1.py', 'windows_owned_process_sup2.py'):
    copy(BASE / name, 'wrapper/' + name)
for name in ('execution_evidence.zip', 'EVIDENCE_MANIFEST.json', 'seal_receipt.json',
             'top_start.json', 'top_supervision.json', 'helper_start.json', 'helper_receipt.json',
             'root_qa.json', 'helper.log', 'helper.instances.ndjson'):
    copy_if_present(BASE / name, 'execution/' + name)
run = BASE / 'run_001'
if run.is_dir():
    for source in sorted(run.iterdir()):
        if source.is_file() and source.name != 'comparison.json' and source.suffix in ('.json', '.log', '.ndjson'):
            copy(source, 'execution/run_001/' + source.name)

images = [
    ('01_actual_geometry.png', '实际×1全机构与工件几何',
     '机构平均输入保持1.06 mm；只给P，刚体q由力控独立求解，无变形倍率放大。'),
    ('02_P_q_cross_check.png', 'P–q与工程误差',
     '旧参考仅accepted[0,2]两个原请求配对；旧q=.0125只作HISTORY ONLY，不插值配对新N二分态。'),
    ('03_force_components_and_R.png', '有符号力分量、输入R与外载账本',
     'ON-body与施加P反号；total包含material和Hu，机构R与P分别报告，旧body-x处方反力不重复入账。'),
    ('04_tip_right_geometry_global_J_Hu.png', '尖端坐标近景、右介质与全域响应',
     '同图坐标放大inset仍为实际×1变形；距离到原工件栅格物理边段并排除对称切口；J/Hu仅已保存全域标量。'),
    ('05_convergence_and_gates.png', '全实际Newton、trial与数值门',
     '保留所有真实接受态和内部尝试；双残差、mean、global和rigid分别显示，旧invalid_J历史单独保留。'),
]
existing_images = []
for name, title, description in images:
    if copy_if_present(run / 'view' / name, 'view/' + name):
        existing_images.append((name, title, description))
has_gif = copy_if_present(run / 'view/actual_force_states.gif', 'view/actual_force_states.gif')
for name in ('geometry_metrics.json', 'renderer_receipt.json'):
    copy_if_present(run / 'view' / name, 'view/' + name)

# Preserve source-review/freeze/prelaunch records exactly as they stood, including
# historical pending/false values. Those do not replace the closed actual summary.
root_copies = {'RESULTS.md', 'NEXT_STEPS.md', 'RECOVERY.md', 'FUNCTION_STATUS_AND_USAGE.md',
               'EXECUTION_RESULT.json', 'protocol.json', 'authorization.json'}
for source in sorted(AUTHOR.iterdir()):
    if source.is_file() and source.suffix in ('.md', '.json', '.py') and source.name not in root_copies:
        copy(source, 'author/' + source.name)

force = summary.get('force_summary') or {}
comparison = summary.get('comparison') or {}
rows = force.get('scalar_rows') or []
status = str(summary['status'])
row_html = []
for index, row in enumerate(rows):
    role = '原请求' if row.get('is_original_target') is True else '内部接受态'
    values = [index, role, row.get('P_target_half_N'), row.get('body_q_mm'), row.get('R_input_N'),
              body_x(row, 'total'), body_x(row, 'material'), body_x(row, 'regularization'),
              row.get('minimum_J'), row.get('max_abs_Hu_per_mm'), row.get('newton_checks')]
    row_html.append('<tr>' + ''.join(cell(value) for value in values) + '</tr>')
if not row_html:
    row_html = ['<tr><td colspan="11">无已记录的接受态标量；不以零值补齐未生成结果。</td></tr>']

cards = []
present = {name for name, _, _ in existing_images}
for name, title, description in images:
    if name in present:
        content = ('<a href="view/' + name + '"><img loading="lazy" src="view/' + name
                   + '" alt="' + escape(title) + '"></a>')
    else:
        content = '<p class="missing">本次未生成此图，未另开窗口补绘。</p>'
    cards.append('<figure><h2>' + escape(title) + '</h2>' + content
                 + '<figcaption>' + escape(description) + '</figcaption></figure>')
if has_gif:
    animation = ('<img loading="lazy" src="view/actual_force_states.gif" alt="全部实际接受态的×1变形动画">'
                 '<p>帧数依原writer成功grab_frame记录；无插值、不代表物理时间。交付仅复制已有原字节，不解码GIF数帧。</p>')
else:
    animation = '<p class="missing">本次未生成动画，未伪造帧数或从旧动画替代。</p>'

links = [('RESULTS.md', '完整目标／过程／结果'), ('USAGE.md', '接口与能力边界'),
         ('result_summary.json', '闭卡轻摘要'), ('RECOVERY.md', '恢复'), ('NEXT_STEPS.md', '下一步'),
         (PREP_REL + 'PREPARATION.md', '高输入准备'),
         (PREP_REL + 'COMPARISON_GATES.json', '冻结比较门')]
if has_comparison:
    links.append(('comparison.json', '实际比较'))
for name, title in [('root_qa.json', '实际root QA'), ('execution_evidence.zip', '原窗口归档字节（状态见seal）'),
                    ('EVIDENCE_MANIFEST.json', '原包成员身份'), ('seal_receipt.json', '原封存回执')]:
    if (DEST / 'execution' / name).is_file():
        links.append(('execution/' + name, title))
nav = ' · '.join('<a href="' + escape(url, quote=True) + '">' + escape(title) + '</a>' for url, title in links)
renderer = summary.get('renderer') or {}
qa = summary.get('root_QA') or {}
prior_history = summary.get('prior_reference_history')
history_html = ('<details><summary>原参考历史普通元数据</summary><pre>'
                + escape(json.dumps(prior_history, ensure_ascii=False, indent=2)) + '</pre></details>') if prior_history is not None else ''
cross_errors = comparison.get('cross_errors')
error_html = ('<details><summary>实际工程误差与冻结门</summary><pre>'
              + escape(json.dumps(cross_errors, ensure_ascii=False, indent=2)) + '</pre></details>') if cross_errors is not None else ''

page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>L-CTIPFHIGH1 · 高输入导向力控</title>
<style>body{font:16px/1.7 system-ui,sans-serif;max-width:1320px;margin:32px auto;padding:0 24px;color:#182b3b;background:#f5f7fa}h1{line-height:1.3}a{color:#075d94}header,section,figure{margin:20px 0;padding:24px;background:white;border:1px solid #d5dee8;border-radius:10px}img{display:block;max-width:100%;height:auto}.scroll{overflow-x:auto}table{border-collapse:collapse;min-width:100%;white-space:nowrap}th,td{border-bottom:1px solid #ddd;padding:8px;text-align:left}figcaption,.note{color:#465b6d}.missing{color:#76502c}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{overflow-wrap:anywhere}</style>
<header><p>2026-10-23 · 已批准唯一执行 · ''' + escape(status) + '''／科学窗口已关闭</p><h1>机构平均输入1.06 mm：给定P，独立求未知工件q</h1><p>α=2.5e−7／r9 mm／圆心(80,40) mm／right92 mm／Lr80 mm；14720单元／29970DOF，生产57份源码保持。下表只显示闭卡记录中的实际接受态，包括内部N二分态。</p>
<p>数值路径：''' + escape(shown(force.get('status'))) + '；工程比较：' + escape(shown(comparison.get('status'))) + '；renderer：' + escape(shown(renderer.get('status'))) + '；root QA：' + escape(shown(qa.get('status'))) + '''。</p><div class="scroll"><table><tr><th>accepted</th><th>角色</th><th>P_half / N</th><th>未知q / mm</th><th>R_input / N</th><th>ON-body total Fx / N</th><th>material Fx / N</th><th>Hu Fx / N</th><th>min J</th><th>max |Hu| / mm⁻¹</th><th>base checks</th></tr>''' + ''.join(row_html) + '''</table></div>
<p class="note">P是已含t20的半模型有符号总外载；完整对称轴向外载2P，q不倍增。P0为原父态的非零预载，新核必须fresh一次原样通过；参考q=.025不是力控输入。R是保持机构平均输入的独立反力。total含material与Hu，ON-body和P反号，不认定为压力或纯接触承载能力。</p>
<p class="note">高输入旧位移参考有q=[0,.0125,.025]三接受态：只以原请求accepted[0,2]配对，.0125为历史内部二分态。旧首次直接大步invalid_J与低J／较强Hu困难完整保留，不假配新N内部态。实际数值与工程状态见原记录，不因媒体存在就升级资格。</p><nav>''' + nav + '</nav>' + error_html + history_html + '</header>' + '\n'.join(cards) + '''
<section><h2>实际接受态动画</h2>''' + animation + '''</section>
<section><h2>记录口径与功能限制</h2><p>媒体为本轮窗口内已生成的原字节；本页不渲染新图、调用HF、读科学数组或重开图像做像素检查。缺失产物明确标为未生成，实际QA以原回执为准，renderer的pending状态是QA前的历史原值。</p><p>当前force接口支持从固定工件父态开始的严格递增绝对P；不支持force保存态续算／力卸载、自由工件、摩擦或压力。即使本次通过，也只支持这两载荷的导向TMC总弱力平衡交叉，不授承载极限、纯接触抗拔、释放、稳定性或全路径HP／HF5资格。</p><p>准备包位于相邻high_preparation目录；本交付不重复旧父／参考科学payload或旧5.8MB参考result。原窗口归档是否完整以实际seal回执为准；DELIVERY_MANIFEST由单独发布阶段生成，发布不另行重封科学证据。</p></section></html>'''
write('inspection.html', page)

banner = ('> 2026-10-23 L-CTIPFHIGH1 **实际状态：' + status + '**：机构平均输入保持1.06 mm，给定两个非零绝对半模型载荷、独立求未知q；闭卡记录含'
          + str(len(rows)) + '个实际接受态。科学窗口已关闭，57份生产源码保持；[实际结果与图页]({p}RESULTS.md)、[功能／用法]({p}USAGE.md)、[下一步]({p}NEXT_STEPS.md)。'
          '数值路径与工程比较分别记录，保留旧低J／Hu及invalid_J历史；不升级压力、纯接触承载、释放或稳定性资格。下方为历史状态。\r\n\r\n')
for relative, prefix in [('README.md', REL + '/'), ('docs/CURRENT_STATUS.md', '../' + REL + '/'), ('hf_repo/README.md', '../' + REL + '/')]:
    target = ROOT / relative
    old = target.read_bytes()
    assert b'L-CTIPFHIGH1 **' not in old[:1500], 'Do not prepend the same current banner twice'
    target.write_bytes(banner.format(p=prefix).encode('utf-8') + old)

attributes = ROOT / '.gitattributes'
old = attributes.read_bytes()
entry = REL + '/wrapper/windows_owned_process_sup2.py whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof\n'
if entry.encode() not in old:
    separator = b'' if not old or old.endswith(b'\n') else b'\n'
    attributes.write_bytes(old + separator + ('# Preserve the unchanged byte-bound SUP2 copied for L-CTIPFHIGH1.\n' + entry).encode())

# publication.py delivery-manifest owns the separate delivery identity manifest.
print(json.dumps(dict(stage='L-CTIPFHIGH1',status=status,delivery=DEST.as_posix(),
    copied_existing_bytes=True,scientific_window_closed=True,existing_PNG=len(existing_images),
    existing_GIF=has_gif,new_scientific_calls=0,new_media_generation=0,
    delivery_manifest_owner='publication.py delivery-manifest'),ensure_ascii=False))
