# 固定方形工件1 mm：新递增加载与卸载探索卡

整体目标是普通LF几何下的独立HF非线性TMC正向力、变形、平衡及接触相关指标，供外部研究比较；HF不运行LF优化/dmftd/MPM。本卡依据004真实0.5mm完整循环、6新HP/58197检查及unsigned边界距2→1.471935964→2mm，继续实现更大真实行程，不能把旧态/资格当成新结果。用户已授权Agent探索对称方/圆工件和较大变形；这里的具体1mm工况是Agent选择的探索任务。

同a2d6原27模型数组：h1mm/3200cells/6642DOFs/376fixed/6266free，固定下半方形side16mm、center(70,40)mm、原底/左初始间隔2mm。E1MPa、nu.3、plane strain、厚20mm，gamma=alpha=1e-6、Lr80mm，输出/辅助弹簧0；平均输入+x、自由输出+y。仅四描述键、input.target_mm=1及ordered targets[0,.5,1,.5,0]改变，case目标同时核对；其余物理字段/方向/源与004一致，coreD5/mean205/CLI01f6/T/CI/B52无实现更新。

机械模式schema1.2/16force/3T/full非对称CSC，辅助材料能量not_evaluated/qualified:false/field_present:false，默认complete不变。原settings、minincrement.00625mm、Newton25/Armijo/backtrack12/bisection4与原残差、约束、force/Jv/HP门、分母/CI支持域保持。保留所有实际接受index，重复.5与0及二分态不去重；从初始重新连续求解，不读取旧缓存作新解。

| 唯一阶段 | helper / outer秒；采样树限额 | 内容 |
|---|---|---|
| prepare | 不适用 / 60；8GiB | 只冻结普通输入、原source63的3既有转换及005五包装，共68，自有字节caps；0新力学 |
| production | 600 / 660；8GiB | 一次连续0/.5/1/.5/0，保存接受缓存及首次真实F/T范围异常原输入；无额外F/T；原控制器回溯按声明算法处理 |
| fresh reference | 240 / 300；8GiB | 仅production完整pass且原前置满足后，全部实际接受态各新HP80/120（至少10次），全部3200cells/6642DOFs、原力/Jv/CSC/KKT/工件投影门，PORT方向而非全列HP |

额度依据004实际生产213.73秒/约853.5MB、参考66.12秒/约423.3MB；五态参考约110秒仅成本估计。1mm收敛、压缩/minJ、算术和额外二分费用未测，原额度不保证足够。helper含imports/构建/IO/最后hash，outer监测协同stop，无OS硬内存cap/force kill。首正式阶段失败关闭本卡，保partial/首捕/原错误，不修复重试/增加额度或放门。声明控制器内部范围拒绝、回溯与二分不是另起外部调用；记录真实计数，不把这些行为隐藏为首异常即退出。

每实际接受态保存并显示真实×1结构、共同N箭头/真实mm色条、R/qout/minJ、作用在下半工件的材/Hu/总FxFy、镜像净力及残余；保存图与实际unsigned Q1边界距/交叉/near-touch在取得数据后另冻有界只读卡，node-window仅代理。生产或参考不成功时不把partial自动授予资格；可视化保失败/未资格标签并读原缓存，不补算平衡。

尚未授予候选能量/应力HP/全列T/一般支持域、旧未知T25/拒绝trial、signed normal gap/containment/接触法向压力/有效夹持或自由工件资格。当前正unsigned距不能外推1mm接触阈值，也不能由小第三介质合力认定夹持。根据1mm实际结果再选择2/3mm、圆r8及细工况；已构建圆/细模型不等于已求解，不称不同LF设计为网格收敛。H2/H3/HF5/完整AD/JIT及整体HF目标仍未完成。

本卡的目标、实现、原因、实际结果/成本/范围与下一步写本目录RESULTS及现有CURRENT_STATUS/NUMPY_FORCE_PROGRESS，保留004/003旧证据，后续main与origin https://github.com/dudaxing/Compliant-TO-TMC.git不变。
