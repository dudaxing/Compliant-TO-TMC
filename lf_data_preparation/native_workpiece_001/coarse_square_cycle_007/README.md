# 固定方形工件1.5 mm：新递增加载与卸载探索卡

整体目标是普通LF几何下的独立HF非线性TMC正向力、变形、平衡及接触相关指标，供外部研究比较；HF不运行LF优化/dmftd/MPM。本卡依据006真实0/.5/1/.5/0完整循环、5接受态、10新HP/96781检查，继续实现更大真实行程。006峰值minJ=.4581891642，实际unsigned底边距=.9244251793mm、左边界距=1.7901563574mm；保存几何无交叉/near-touch，未做containment测试。这些已测值只说明006，不授007接触或夹持资格。用户已授权探索对称方/圆工件和较大变形，具体1.5mm工况由Agent按上一步结果选择。

保持a2d6原27模型数组：h1mm/3200cells/6642DOFs/376fixed/6266free，固定下半方形side16mm、center(70,40)mm、原底/左初始间隔2mm。E1MPa、nu.3、plane strain、厚20mm，gamma=alpha=1e-6、Lr80mm，输出/辅助弹簧0；平均输入+x、自由输出+y。仅四描述键、input.target_mm=1.5及ordered targets[0,.5,1,1.5,1,.5,0]改变，case目标同步核对；其余物理字段/方向/源与006一致，coreD5/mean205/CLI01f6/T/CI/B52无实现更新。

机械模式schema1.2/16force/3T/full非对称CSC，辅助材料能量not_evaluated/qualified:false/field_present:false，默认complete不变。原settings、minincrement.00625mm、Newton25/Armijo/backtrack12/bisection4与原残差、约束、force/Jv/HP门、分母/CI支持域保持。不重跑旧6测试或新toy；沿用已冻结且通过的集成证据。保留所有实际接受index，重复1/.5/0及二分态不去重；从零重新连续求解，不读取006缓存作新解。

| 唯一阶段 | helper / outer秒；采样树限额 | 内容 |
|---|---|---|
| prepare | 不适用 / 60；8GiB | 保留006的39输入，再加006四前例记录与007任务/方向/README三输入，共46；原003source63的3既有转换及007五包装，共68，准备113pins |
| production | 600 / 660；8GiB | 一次连续0/.5/1/1.5/1/.5/0，保存接受缓存及首次真实F/T范围异常原输入；无额外F/T；原控制器回溯按声明算法处理；科学协议186pins |
| fresh reference | 240 / 300；8GiB | 仅production完整pass且原前置满足后，全部实际接受态各新HP80/120（至少14次），包括二分态；全部3200cells/6642DOFs、原力/Jv/CSC/KKT/工件投影门，PORT方向而非全列HP |

额度依据006真实outer生产375.0062062秒、参考102.7997052秒（helper374.0031275/102.5191004秒），31F/18T/1solver、5接受态、10HP/96781检查；七态参考约144秒仅成本估计。1.5mm收敛、压缩/minJ、算术支持与二分费用均未测，原额度不保证足够。helper含imports/构建/IO/最后hash，outer监测协同stop，无OS硬内存cap/force kill。首正式阶段失败关闭本卡，保partial/首捕/原错误，不修复重试/增加额度或放门。声明控制器内部范围拒绝、回溯与二分是原算法，不是另起外部调用；记录真实started/completed计数。

实际数据生成后再冻独立保存图/几何卡，显示真实×1结构、共用N力箭头/真实mm色条、R/qout/minJ、下半工件材/Hu/总FxFy、镜像净力及残余，全部接受index保持求解顺序。真实unsigned Q1外边界距/交叉/near-touch与node-window代理分别说明，左边界最近点可能在角点，不当侧壁法向gap。partial不自动获资格，保存图保生产/失败/未资格标签，不补算平衡。

尚未授予能量/应力HP/全列T/一般支持域、旧未知T25/拒绝trial、signed normal gap/containment/接触法向压力/有效夹持或自由工件资格。006正unsigned距不能外推1.5mm接触阈值，小第三介质合力也不能证明夹持。根据007实际结果再选择下一行程、圆r8或细工况；已构建模型不等于已求解，不称不同LF设计为网格收敛。H2/H3/HF5/完整AD/JIT及整体HF目标仍未完成。

本卡目标、实现、原因、实际结果/成本/范围与下一步写本目录RESULTS及现有CURRENT_STATUS/NUMPY_FORCE_PROGRESS，保留006/004/003及closed005原证据；后续main与origin https://github.com/dudaxing/Compliant-TO-TMC.git保持。
