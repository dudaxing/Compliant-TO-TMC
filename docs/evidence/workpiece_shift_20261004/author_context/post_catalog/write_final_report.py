"""Write the living project record from closed comparison metadata only."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, json


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--repo',type=Path,required=True)
    root=p.parse_args().repo.resolve(); evidence=root/'docs/evidence/workpiece_shift_20261004'
    data=json.loads((evidence/'final_comparison.json').read_text(encoding='utf-8')); c=data['cases']
    old,pose,soft=(c[k] for k in ('old010','pose002','soft001'))
    rows=[('| 工况 | 原 x70 / E1 | 右移 x71 / E1 | 右移 x71 / E.5 |'),('|---|---:|---:|---:|')]
    metrics=[('输入反力 N','R_input_N'),('自由输出 +y mm','q_out_mm'),('下半工件总 Fy N','total_body_Fy_N'),
        ('材料 Fy N','material_body_Fy_N'),('Hu Fy N','regularization_body_Fy_N'),
        ('最右钳尖到有限右面 mm','tip_to_right_mm'),('最右钳尖到有限底面 mm','tip_to_bottom_mm'),
        ('底面首次法向射线 mm','bottom_first_ray_mm'),('自由介质 min J','medium_min_J'),
        ('实体 min J','solid_min_J'),('实体全域最大平面 Green 主应变','solid_Green_principal_max')]
    for title,key in metrics:rows.append('| '+title+' | '+' | '.join(f'{x["peak"][key]:.10g}' for x in (old,pose,soft))+' |')
    rows.append('| 接触边邻接实体最大主应变 | '+' | '.join(f'{x["local_fit"]["adjacent_solid_Green_principal_max"]:.10g}' for x in (old,pose,soft))+' |')
    rows.append('| 实际接受态 / 新 HP / 检查 | '+' | '.join(f'{x["N"]} / {x["reference"]["fresh_HP"]} / {x["reference"]["checks"]}' for x in (old,pose,soft))+' |')
    costs=['| 工况/阶段 | F 开始/完成；T 开始/完成 | helper / outer s | helper / tree RSS bytes |', '|---|---|---:|---:|']
    for name,x in c.items():
        q=x['call_counts']; r=x['production']; t=x['reference']
        costs.append(f'| {name} 生产 | {q["force_calls"]}/{q["force_calls_completed"]}；{q["tangent_calls"]}/{q["tangent_calls_completed"]} | {r["helper_seconds"]:.8f} / {r["outer_seconds"]:.8f} | {r["helper_RSS_bytes"]} / {r["tree_RSS_bytes"]} |')
        costs.append(f'| {name} 独立参考 | 0新F/T/模型/求解；{t["fresh_HP"]} HP | {t["helper_seconds"]:.8f} / {t["outer_seconds"]:.8f} | {t["helper_RSS_bytes"]} / {t["tree_RSS_bytes"]} |')
    local_gain=100*(soft['local_fit']['adjacent_solid_Green_principal_max']/pose['local_fit']['adjacent_solid_Green_principal_max']-1)
    reaction_ratio=soft['peak']['R_input_N']/pose['peak']['R_input_N']; body_ratio=soft['peak']['total_body_Fy_N']/pose['peak']['total_body_Fy_N']
    text=f'''# 工件右移与软硬度：目标、实施、排查和实际效果

本轮阶段标识20261004，终态整理于韩国时间2026-10-05。整体目标仍是让独立 HF 从普通自包含几何和显式任务计算第三介质非线性响应，为已有 LF/N4 研究层提供可对照的力、变形和接触相关指标；HF不运行优化，不导入、安装或子进程调用dmftd，不实施MPM。整个项目尚未完成。

## 本轮判断

用户希望工件稍靠右，使最右钳尖更直接接近工件，并允许降低夹持器刚度以观察接触后的贴合。已分别完成位置与材料两组完整循环及全部接受态的独立参考。**右移1 mm明显有效；均匀实体刚度减半没有进一步拉近最右钳尖。** 因此保留x71/E1作为当前较高工件受力的基准，x71/E.5保留为低驱动力、更多局部变形的探索工况，不将E.5直接设为所有任务的默认值。

峰值输入均为1.8 mm。工件中心由(70,40)移至(71,40) mm、边长16 mm；原网格1 mm、实体、支承、端口与11目标不变。下半固定方体由[62,78]×[32,40]改为[63,79]×[32,40] mm。模型3200单元/3321节点/6642 DOF；376固定、6266自由，工件128单元/153节点/306固定DOF，与数学对称切口17个uy DOF重叠。

软化采用实体E1→.5 MPa、ν=.3，gamma/alpha同时1e-6→2e-6、物理正则长度80 mm与厚度20 mm不变。这使实体Lamé减半、**绝对第三介质Lamé与全局kr保持原值**；Hu相对于实体变强。只相对合格位置模型改变lam/mu/gamma/Et四个字段，其余23字段字节相同。Et力尺度20→10；原floor公式及数值门保持。因此本实验不是把整体所有内力均匀乘以.5，也不是接触压力资格。

## 实际数值与局部贴合

{chr(10).join(rows)}

软化的峰值输入反力为原位置对照的{reaction_ratio:.4%}，工件竖向力为{body_ratio:.4%}；所选原生y30、x63–80物理接触候选边邻接实体的最大Green主应变增加{local_gain:.3f}%。这支持局部变形有所增加，但钳尖有限右面距离.167270→.172489 mm、底面首次射线.005809→.011498 mm，未支持贴合改善。全域最大应变约5.18%，与局部边约.115–.125%的应变不是同一测量区域。

峰态右移钳尖节点2510=(79.167270432,32.009274354) mm；软化=(79.172489199,32.004129825) mm。**两者钳尖仍在工件右面x79外；不能宣称钳尖已直接接触。** 底面小射线来自边2509–2510内部点对工件右底角的命中，不是钳尖间隙。TMC在介质正J压缩下传递力，有限正间隙/无已测跨域内部重叠不是精确硬接触、压力或真实夹持成立。

全部原11目标为0/.5/1/1.5/1.75/1.8/1.75/1.5/1/.5/0 mm。position实际17态、soft实际14态，由原二分控制器新增状态而非改变目标。三组完整返回0；position返回R={pose['return_to_zero']['R_input_N']:.10g} N、q_out={pose['return_to_zero']['q_out_mm']:.10g} mm，soft返回R={soft['return_to_zero']['R_input_N']:.10g} N、q_out={soft['return_to_zero']['q_out_mm']:.10g} mm。保留实际极小值，不归零、不去重初始与返零。

![实际x1结构、峰值与返零](../{data['master_view']}/comparison.png)

![局部物理边、有限面距离、共同比例应变和节点力](../{data['local_fit_view']}/local_fit.png)

完整实际动画：[原位置12帧](../{data['master_view']}/old010/actual_states.gif)、[右移17帧](../{data['master_view']}/pose002/actual_states.gif)、[软化14帧](../{data['master_view']}/soft001/actual_states.gif)。[共同峰值应变/J/Hu图](../{data['master_view']}/peak_fields.png)与[实际距离/三Fx曲线](../{data['master_view']}/distances_forces.png)供人工检查；各工况数值曲线坐标按图上刻度阅读，不误认为所有分图纵轴相同。节点箭头与场色标使用共同尺度。图中上半为对称显示，未追加求解DOF或新状态。

## 已排查的问题、改动与失败保留

旧010卸载T44/F77范围拒绝已由独立一次缓存诊断重现：cell1981方向dT的低位×低位产生约2^-410归一化非零低位，低于原2^-400门；108事件传播至材料/总切线各16条目，Hu支持完整。原tiny-G分支未选择导数缩放，不能把已有NaN的后续传播重复算成根因。诊断0新F/模型/CSC/求解/HP，预期拒绝重现不是内核通过。

唯一核心修正是[split_numpy_tangent.py](../hf_repo/src/hf_eval/split_numpy_tangent.py#L33)的v5方向尺度分支：全批near且参考算子/系数≤2^8时保持2^128共同方向尺度至三张量末尾再缩回，full/chunk各从全批选择一次。净增7行；原力、乘积选择器、算术守卫、物理公式与控制器不改。一次300/360 s、8 GiB验证通过12项原focused测试、缓存full/chunk三张量字节/stride一致、fresh HP80/120对3200单元及6642共享DOF的9603原作用检查；确定方向覆盖原3/5失效方向，最大局部总作用误差约1.14e-14、门1e-10。范围限该缓存及已验证测试，旧F90不是因此自动证明解决；不外推全列、任意状态、压力或未接受态平衡。

| 阶段 | 实际效果与状态 |
|---|---|
| t44_cached_diagnostic_001 | 15.3697535/15.8207675 s，预期旧异常重现；原输入和胶囊保留 |
| t44_direction_scaling_repair_001 | 77.5334787/78.8542090 s，12测试/2缓存T/2HP/9603原门通过 |
| shift_square_pose_001 | 900/960 s卡time_limit失败，13接受态；F108/102、T58/57、HP0；helper908.2539639/outer910.0598497 s，终末T58因窗口停止，未捕获新范围错误；不拼前缀资格 |
| shift_square_pose_002 | 新零起点完整同任务，仅time_limit明确1500/1500/1560 s，6预测首F invalid_J回滚二分；74历史、57试算、79LU；独立34HP通过 |
| shift_square_soft_001 | 新零起点材料对照1800/1860 s；3预测首F23/31/50 invalid_J回滚二分；60历史、46试算、62LU；全部14态28新HP通过，无新F/T范围捕获 |
| shift_counter_metadata_001 | 8纯数据例通过：旧010完整trace、旧001超时拒绝、显式synthetic前缀形状及5负例；不是新短任务/物理资格，0F/T/模型/求解/HP |
| preview_001 | 旧12态＋失败位置13态共25次几何/25节点观察，只作先前预览；失败完整状态不变 |
| complete_001 | 误选旧010未通过reference，2.2145296 s在元数据阶段失败，0几何/节点/F/T/求解/HP；原卡关闭保留 |
| complete_002 | 相同viewer字节，新卡显式改用已通过coarse_square_cycle010_ref_003；43几何＋43节点观察全部通过，47.1284709 s outer；0新F/T/模型/求解/HP |
| fit_001 | 复用合格完整视图的缓存边/节点报告；0新增几何观察/力学/HP，10.3976897 s outer；实际三组局部图通过 |

## 资源、独立参考和资格范围

{chr(10).join(costs)}

右移参考900/960 s；软化参考另冻900/960 s，实际14态需要28新HP，以position17态618.89 s参考成本比例估计约509.68 s并预留390.32 s。均8 GiB、一次连续窗口；首错关闭，无同卡修复/重试/延时/force。RSS为合作采样，不是OS硬内存帽；helper可包含Windows peak_wset，tree采样另计。构造分别只有1模型且0F/T/求解/HP：pose002 helper4.8186423/outer5.9762540 s，soft helper6.4347542/outer7.6805693 s。

新参考逐一覆盖全部实际接受态、全部单元/DOF的三力、声明固定lift的PORT方向切线作用、full CSC、平均约束/KKT平衡及有符号工件投影；使用原B850机械run_state、aa86工件检查及B52作用consumer，数学门不改，不借旧HP前缀。**不是切线全列、拒绝态、压力/应力HP、辅助材料能量或自由工件夹持资格。** 保存生产原equilibrium/independent_HP/HF flags仍false，独立参考另有全路径pass记录，未回填或改旧descriptor。

固定下半工件力是负的保存全局内力；holding反向。2|Fy|是双侧法向幅值之和，镜像净力为(2Fx,0)，两者不可混用。工件全ux/uy固定，外部支承承担holding；目前没有自由刚体平移/旋转未知量及平衡、摩擦或稳定夹持证明。Green与普通节点力矩来自保存数组，未新增应力/力矩HP资格；J图为单元均值，极小值另在表中报告。

## 下一步与可恢复交付

下一功能优先把最右尖端纳入工件的有限接触面覆盖，再决定是否局部软化；不继续盲目降低整体E或增大行程。当前1 mm原生网格下，中心x72、边长16会使工件右面位于x80外边界、右侧第三介质消失，是一个**新边界贴靠任务**，不能继承x71的工件覆盖/数值资格。若要保持右侧包围介质，需新的扩大HF分析域/区域与边界身份，不能静默改变LF实体、Lr或网格。该x72任务尚未执行。[实际钳尖与边界取舍说明](evidence/workpiece_shift_20261004/physics_tip_alignment_note.json)。

其后仍需圆体与自由工件任务、明确接触/释放定义、匹配设计的网格与介质/正则参数收敛，以及当前HF后端接入既有LF/N4同任务评价/HF5批量标签；已有上游优化/评分流程无需在HF重做。更完整的实现位置和缺项见[物理功能进度](HF_FUNCTION_PROGRESS_20261004.md)。

源码与当前状态、原始失败/通过输入输出、70项源胶囊、全部接受态、各协议与资源回执、作者版本/静态审阅及图像均保留于main。origin固定https://github.com/dudaxing/Compliant-TO-TMC.git。其他机器按[恢复入口](RESUME_DEVELOPMENT.md)克隆main到任意新路径；交付verify证明文件身份，历史卡/硬编码作者来源不是异目录同卡重跑指令，也不证明完整外部Release资产恢复或数值重验。

原始主要证据：[position生产](../{pose['result_file']})、[position新参考](../{pose['stage']}/reference/summary.json)、[soft生产](../{soft['result_file']})、[soft新参考](../{soft['stage']}/reference/summary.json)、[完整比较JSON/输入SHA](evidence/workpiece_shift_20261004/final_comparison.json)、[作者复制/版本记录](evidence/workpiece_shift_20261004/author_copy_receipt.json)。旧010合格参考实际位于coarse_square_cycle010_ref_003，不能误指旧010/reference失败记录。
'''
    doc=root/'docs/WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md'
    old_text=doc.read_bytes(); previous=evidence/'master_report_before_final.md'; assert not previous.exists()
    previous.write_bytes(old_text);doc.write_text(text,encoding='utf-8')
    record=dict(status='living_report_finalized',created_utc=datetime.now(timezone.utc).isoformat(),
        old_sha256=sha256(old_text).hexdigest(),new_sha256=sha256(doc.read_bytes()).hexdigest(),
        writer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),numerical_calls=0,
        scope='Closed saved facts and explicitly stated future scope; whole HF project remains incomplete')
    with (evidence/'report_write_record.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record))


if __name__=='__main__':main()
