"""Record the post-run physical decision from ordinary saved observations only."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_right_pilot_001'
STAGE=ROOT/REL
names=['run_001/view/wave_circle_right_pilot/summary.json','run_001/convergence/convergence.json','author/PHYSICAL_DECISION_DRAFT.json']
sources={name:sha256((STAGE/name).read_bytes()).hexdigest() for name in names}
summary=json.loads((STAGE/names[0]).read_bytes())
next_step='优先提出L-CTIPPREP1：将圆形候选置于(80,40)mm、r9保持，并将参考分析域右界从84显式扩至92mm，先做输入/未变形兼容性与tip对向检查；本轮不实施。当前.5时最近位置仍是x76横梁，tip仍距2.039mm，右介质参与压缩，继续.75不优先于核清布局。'
interpretation='''## 本轮物理判断与取舍

本轮实现了新布置零起点短程前向分析和保存态右侧介质可视化，默认力核、切线及控制器没有修改。3态通过原门，无失败、回溯拒绝或二分；这回答了当前任务能否计算。

同一最右tip节点10300从(80,30)移动至(79.86047,30.48127)mm，tip距2.5→2.27017→2.03897mm。全机构最近距离1→.803043→.603816mm；末态最近见证是(76.01342,30.39633)→(76,31)mm，仍为横梁内侧与工件阶梯底部。三态未观测到边界交叉、近触或跨区域单元内部重叠；完整包含关系未测试。当前仍未证实尖端接触或夹紧。

末态下半工件Fy=0.000296836N，其中材料0.0000684625N、Hu项0.000228374N。它是包含原介质/正则化作用的弱式合力；几何仍分离时出现非零值，不能单凭该值认定已接触、有效夹持或连续表面压力。

右条带在.5时minJ=.651485，见证e10246/q2参考(83,30.5)mm，实际(82.96463,30.77568)mm；Green最小主值−.300930、最大|Hu分量|.00246425/mm。全条带最大节点|u|=.736785mm位于底右角node168，实际(84.49875,.542308)mm，不是工件附近间隙闭合量。参考x84节点允许移动；实际坐标越过初始x84不是新增固定壁或域门违规。已观察到介质参与变形，尚未证明域污染、域过窄或域宽收敛。

据此优先准备更面向tip的新布局：圆心候选(80,40)、r9，明确将HF参考域右界扩至92mm，并保持Lr=80mm。新候选解析圆最右89，理论留3mm；实际Q1覆盖、端口/支撑冲突、原机构和全部新增介质、全域顶部uy、外界自由DOF及是否进入tip最近区域都须下一轮实际准备后核验。此计划会同时改变工件位置与分析域，比较时须注明两项变化。不预先保证tip先接触或域宽足够。

当前(74,40)/x84的全部通过结果保留；本轮不继续.75、不新增HP或改任何物理/门。更高载的当前布局仍可作为另一个明确物理问题，但对当前‘最右tip接触’目标，先核新布局更直接。独立判断见[物理草稿](author/PHYSICAL_DECISION_DRAFT.md)。
'''
plan='''# L-CRPILOT1后的计划：先核尖端对向布局

当前L-CRPILOT1已PASS：r9/(74,40)、84×40mm参考域，从零[0,.25,.5]完成；5PNG和实际3帧动画已生成。最近点仍在x76横梁，末态tip距离2.039mm、最近距离.604mm，右条带minJ.6515。本页不授权或启动新计算。

下一步建议 **L-CTIPPREP1**，只做输入与未变形检查：

1. 新候选r9/(80,40)mm，将HF参考域右界从84明确扩至92mm。圆理论伸至x89，理论余3mm/6列h.5介质；这些是布置算术，尚未做实际网格检查，也不是域宽收敛证明。
2. 保原LF机构/端口位置、方向和权重、支撑、h.5、E1MPa、nu.3、plane strain、厚20mm、gamma1e-6、alpha5e-7、固定工件ux/uy。正则化物理长度Lr继续80mm，不能随新域改为92；全域顶部uy必须明确延至92，新外边界ux及非顶uy沿用自由类型。
3. 优先复用已有LF输入准备/构模入口，生成独立几何身份与新任务。核原机构网格/四掩码语义和源绑定、完整圆Q1覆盖/固定节点、与原实体/支撑/端口不冲突、原/新增介质归属、所有约束和端口。不得把旧84域的geometry_id原样冒用为92域。
4. 用固定reference tip(80,30)与实际未变形Q1有限边核最近点、tip距离、可能并列及右侧完整介质。圆底对向tip也不自动保证tip唯一最先接触。生成一张同尺度布置/局部/介质/约束对照PNG和完整输入说明。
5. 候选准备预算建议helper180/outer240秒、采样64GiB、四库16；无新F/T、平衡、HP或测试，首错停，独立静审与冻结后唯一准备。必要包装与读取范围在新卡具体化后执行，当前窗口已关闭。
6. 只有新准备通过，再根据实际几何安排另一次零起点[0,.25,.5]短试算及同定义变形/反力/收敛/右介质显示。当前x74结果作为历史对照；涉及位置与域宽同时变化，比较须如实说明。是否另做固定位置的域宽敏感性检查由具体不确定性决定，不预授域独立资格。

本轮没有启动新候选、没有继续.75或新增HP；原失败历史、通过结果及原资格保留。压力、有效夹持、自由释放、稳定性、完整父路径及HF5资格仍按原状态。
'''
decision=dict(card='L-CRPILOT1',execution_status='pass',next_card='L-CTIPPREP1',next_step=next_step,
    source_sha256=sources,observed_rows=summary['rows'],next_proposal=dict(workpiece=dict(center_mm=[80,40],radius_mm=9),
    reference_domain_mm=[92,40],h_mm=.5,regularization_length_mm=80,changed_physical_fields=['workpiece.center_mm[0]','analysis_domain.right_extent_mm','background_symmetry.points_mm[1][0]'],
    implemented=False,executed=False,compatibility_passed=None,boundary_width_converged=False),
    interpretation_md=interpretation,next_steps_md=plan,scope='Ordinary post-run interpretation and future proposal only; no new scientific or geometry computation.')
target=STAGE/'author/NEXT_DECISION.json'
assert not target.exists()
target.write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
(AUTHOR/'NEXT_DECISION.json').write_bytes(target.read_bytes())
(STAGE/'author/record_decision.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(status='actual_physical_decision_recorded',new_scientific_calls=0,next_proposal_executed=False)))
