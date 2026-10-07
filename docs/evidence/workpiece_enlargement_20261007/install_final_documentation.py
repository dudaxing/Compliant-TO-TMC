"""Install actual saved outcomes and concise fronts; no numerical mechanics."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
from PIL import Image

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
PROPOSAL = AUTHOR/'final_documentation_001'
EVIDENCE = ROOT/'docs/evidence/workpiece_enlargement_20261007'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
pin = lambda p: sha256(p.read_bytes()).hexdigest()

data = read(PROPOSAL/'progress.json')
new = data['cases']['side18_projection']
assert new['whole_path_passed'] and new['reference_qualified']
assert new['view']['status'] == data['projection_fit']['status'] == 'pass'
assert data['validation']['passed'] and new['accepted_states'] == 24
assert new['reference']['HP_calls_completed'] == 48
frames = {}
for label in ('pose_E1', 'projection001'):
    file = ROOT/'functional_views/workpiece_enlarge_20261007/complete_001/view'/label/'actual_states.gif'
    with Image.open(file) as image:
        frames[label] = dict(file=file.relative_to(ROOT).as_posix(), frames=image.n_frames, sha256=pin(file))
assert frames['pose_E1']['frames'] == 17 and frames['projection001']['frames'] == 24
shutil.copyfile(PROPOSAL/'progress.json', EVIDENCE/'progress.json')
quadrature = EVIDENCE/'quadrature'
quadrature.mkdir()
for name in ('quadrature_corner_source_review.json', 'quadrature_corner_note.json', 'quadrature_corner_note.md'):
    shutil.copyfile(AUTHOR/name, quadrature/name)

report = (PROPOSAL/'WORKPIECE_ENLARGEMENT_20261007.md').read_text(encoding='utf-8')
first = report.index('\n\n整体目标')
report = report[:report.index('\n\n')] + '''

**本轮已完成右缘到80 mm、边长18 mm固定方体的0→1.2→0 mm循环：24个真实接受态，48次新HP80/120及465220项参考检查通过。** 峰值单侧工件Fy=0.1190075723 N，两侧法向幅值和=0.2380151447 N；输入R为半模型的0.4071352773 N。钳尖位于(79.71689116,30.99429925) mm，在有限底面的覆盖范围内，距离为0.0057007523 mm（5.7 μm）。完整回零后力与位移返回数值零附近。
''' + report[first:]
report = report.replace('下一项功能改变只选择初猜：', '本轮新增的功能只改变初猜：')
report = report.replace('尚需完成接触附近稳定全周期的资格、圆体与自由工件运动/释放、摩擦、接触压力、同设计网格与介质/正则参数收敛，以及HF5与既有研究层的同任务耦合。',
    '本24态机械全周期的独立参考已经完成。接触/夹持判据和压力定义、同设计网格与介质/正则参数收敛、圆体与自由工件运动/释放、摩擦，以及HF5与既有研究层的同任务耦合仍待推进。')
report += '''

## 功能效果、成本与取舍

输入从0.85增至1.2 mm时，输出端qout只从0.9684366增至1.0088870 mm，而单侧工件Fy从0.0025242增至0.1190076 N。输出趋于平缓和工件力快速增长与本轮的接触目的相符；最右钳尖在有限底面的覆盖内，保存几何各态均无已测结构/工件内部重叠或舍入模糊。该图的几何检查范围是固体与工件，未增加自接触、完整包容或压力资格。

同一side18物理任务的加载0.5 mm态，新旧初猜的ΔR=8.79407e-12 N、ΔFy=3.527777e-14 N。新初猜改善进入可行Newton区域；这项单点一致性不证明全路径唯一性。峰态全固体最大Green主应变0.03282013，原局部窗口的量与全域量分别解释。

`q_out=.25 uy(80,28)+.5 uy(80,29)+.25 uy(80,30)` mm；它是加权输出端口，而非钳尖间隙。图中橙线/绿射线是距离；力箭头为工件节点弱式力。夹持力报告单侧Fy和2|Fy|，完整工件净力另为(2Fx,0)。当前工件固定，厚度20 mm、E=1 MPa、1 mm网格，右侧介质余量为零；这些条件属于本算例。

| 阶段 | helper/outer授权 秒 | helper/outer实际 秒 | 实際工作 |
|---|---:|---:|---|
| 控制器/API验证 | 180 / 240 | 13.907 / 15.513 | 15测试；22个小模型求解，0完整工件路径/HP |
| 新生产 | 3000 / 3060 | 2839.981 / 2841.369 | 354/330F，176/176T，1求解，0HP；24原目标 |
| 全状态新参考 | 1500 / 1560 | 716.989 / 718.808 | 24态、48HP、465220检查；0候选F/T/求解 |
| 完整保存观察/图 | 180 / 210 | 43.146 / 47.767 | 41几何+41节点力观察（17旧+24新），0新力学/HP |
| 缓存局部图 | 120 / 150 | 9.492 / 10.231 | 复用上一步数据，0新几何/力学/HP |

以上各卡RSS授权8 GiB；新生产helper/outer采样峰562446336/560816128字节，新参考424910848/428838912字节。采样与合作停止不等于操作系统硬内存限制。生产24次未完成F是原线搜索正常拒绝的14次invalid_J和10次范围异常，全部随后半factor恢复；0失败加载尝试、0额外二分态。计数适配只支持真实已恢复分支，1817项纯保存复现及独立审查通过；原B028与新计数器分别保存。首次范围试探ordinal325仍无独立力学资格。

首次参考命令漏传`--protocol`，在读取不存在的默认文件时退出，早于执行卡加载、receipt及子进程创建；0正式调用/HP。该操作入口错误保留在[原记录](../lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/reference_operator_entry_001.json)和[独立审查](evidence/workpiece_enlargement_20261007/source_context/reviews/reference_operator_entry_static_review.json)。之后显式传入冻结协议，正式参考只启动一次；协议b80111a6…、预算和原始结果未改变。两张失败生产卡始终关闭，未重试或复用其前缀。

根审一度把九点规则误认为内部Gauss点，提议另核介质角点。源码确认当前9点Simpson/Gauss–Lobatto含全部四角，原正J门已覆盖；额外卡在创建/冻结/执行前撤回，新增调用为0。[源码纠正与撤回记录](evidence/workpiece_enlargement_20261007/quadrature/quadrature_corner_note.md)完整保留这一取舍。

图和CSV使用原保存数组；新动画24帧，旧对照17帧，均为实际索引，无插值帧。已人工检查整体/局部/场图；原生产三项独立资格flags保持false，新参考资格由独立summary给出，限该24态机械力、PORT方向切线作用、组装、平衡和工件投影。辅助能量、应力HP、全切线列、压力和自由工件稳定夹持仍不在本轮资格内。

## 接续开发

先人工检查本轮位置、×1变形和力，再以同一物理任务逐项检查网格、gamma/alpha和右侧介质余量的敏感性；在此基础上明确接触/夹持判据与压力，再推进圆体、可动工件、局部柔顺性及HF5/LF-N4接口。现有研究层保持，后续均在main上开发。

[当前状态](CURRENT_STATUS.md)、[跨目录恢复](RESUME_DEVELOPMENT.md)、[作者资料及审阅索引](evidence/workpiece_enlargement_20261007/source_context/INDEX.md)、[真实状态与资源JSON](evidence/workpiece_enlargement_20261007/progress.json)。普通文件与当下源码经移交清单核对；历史闭卡及pending作者快照作为时间点记录，不是接续重跑命令。基线提交b310033，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。整个HF项目尚未完成。
'''
report = report.replace('實際工作', '实际工作')
(ROOT/'docs/WORKPIECE_ENLARGEMENT_20261007.md').write_text(report, encoding='utf-8')

terminal = '完整24态、原24目标和回零成功；新参考48 HP80/120、465220检查通过；峰值单侧Fy=0.119008 N、双侧法向幅值和=0.238015 N、钳尖底面距0.005701 mm（5.7 μm）。'
tokens = {'PRODUCTION_TERMINAL': 'success；24态完整加载/卸载，354/330F、176/176T，1求解',
          'REFERENCE_TERMINAL': 'pass；24态、48次全新HP80/120、465220检查',
          'VISUAL_TERMINAL': 'pass；41几何/41节点力观察；新24帧实际动画；缓存局部图完成',
          'CURRENT_VERIFIED_RESULT': terminal,
          'ACTUAL_PEAK_AND_COMMON_LOADING_READINGS': '峰值单侧Fy=0.119008 N，双侧幅值和=0.238015 N，半模型输入R=0.407135 N；钳尖有限底面距离0.005701 mm。完全卸载Fy≈−1.50e−27 N。相同side18任务的加载0.5 mm点，新旧初猜ΔR≈8.79e−12 N。不同工件的1.8/1.2 mm峰值分别报告。'}
for name in ('README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
    file = ROOT/name
    before = file.read_bytes()
    template = (AUTHOR/'front_documentation_candidate/fronts'/name).read_text(encoding='utf-8')
    for token, value in tokens.items():
        template = template.replace('{{'+token+'}}', value)
    prefix = '' if name == 'README.md' else '../'
    links = ('[整体/力曲线]('+prefix+'functional_views/workpiece_enlarge_20261007/complete_001/view/comparison.png)；'
             '[钳尖/应变/节点力]('+prefix+'functional_views/workpiece_enlarge_20261007/fit_001/view/local_fit.png)；'
             '[24帧实际动画]('+prefix+'functional_views/workpiece_enlarge_20261007/complete_001/view/projection001/actual_states.gif)。')
    template = template.replace('{{ACTUAL_VISUAL_LINKS}}', links).replace('<!-- front proposal 2026-10-07; dynamic results require final actual records -->', '<!-- current-front 2026-10-07; actual complete records; baseline b310033 -->')
    template = template.replace('实际终态（待最终记录填写）', '实际终态')
    assert '{{' not in template
    file.write_bytes(template.encode('utf-8')+before)
for name in ('docs/HF_FUNCTION_PROGRESS_20261004.md', 'docs/WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md'):
    file = ROOT/name
    with file.open('a', encoding='utf-8') as stream:
        stream.write('\n\n2026-10-07接续：右缘到80mm、side18的新24态循环与48次新参考通过；峰单侧Fy=.119008N，双侧法向幅值和=.238015N，钳尖底面距.005701mm。参见[新功能与取舍记录](WORKPIECE_ENLARGEMENT_20261007.md)，本页既有内容保留为原时点历史。\n')
record = dict(schema_version='final-saved-documentation-install-1.0', source_sha256=pin(Path(__file__)),
              figures_inspected=['comparison.png', 'peak_fields.png', 'local_fit.png'], GIF_frames=frames,
              new_F=0, new_T=0, new_solver=0, new_HP=0, new_geometry_API=0,
              files={name:pin(ROOT/name) for name in ('docs/WORKPIECE_ENLARGEMENT_20261007.md', 'README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md')})
(EVIDENCE/'documentation_install.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
shutil.copyfile(Path(__file__), EVIDENCE/'install_final_documentation.py')
print(json.dumps(dict(status='actual_documentation_installed', frames=frames, new_numerical_calls=0)))
