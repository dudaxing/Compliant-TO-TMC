# Coarse square cycle009：保留完整九目标的分块切线实现

本卡修复 cycle008 时间超限的功能障碍，保留原请求：
从独立零状态加载到1.75 mm，再按 [1.5,1,0.5,0] 卸载，完整九目标
[0,0.5,1,1.5,1.75,1.5,1,0.5,0]。不删观察点，不承接008的状态或资格。
008失败及末端0未接受的证据原样保留。此前八目标后续建议已由本卡取代。

## 改动与前置证据

numpy_tangent_chunk_001：一次真实三态3F/9T/9CSC比较，三张完整切线及完整CSC
与冻结旧源码和旧保存值逐字节相同，单次切线加快1.84–1.87倍；12项测试通过。
native_mean_chunk_integration_001：一次10项测试通过，默认full和显式chunk256
临时小循环、失败回滚、缓存保存及执行信息正确。均无工件新路径或新HP资格。

仅显式 tangent_mode="chunk256" 使用256单元块；全批次只选择一次small_products，
九积分点、八方向、单元内固定归约及全域非对称CSC顺序保持。
原DD核心逆提取AST同旧源码；默认 full 未切换。native API/CLI和每接受态声明执行信息。
原003 63份闭包之上，四项显式源码过渡为机械force D5、native入口、
CLI入口、切线重构与可选分块；B52保存张量consumer和B850 private reference未改。

## 物理任务及门

同一原27字段模型：1 mm原网格3200单元/3321节点/6642DOF；
下半16 mm固定方形工件中心(70,40)，下半实体[62,78]×[32,40] mm；
初始底/左间隙2 mm，E=1 MPa、nu=.3、plane strain、厚20 mm，
gamma=alpha=1e-6、Lr=80 mm，零输出和输入辅助弹簧。
原输入三节点加权平均+x控制，输出三节点自由平均+y测量；
固定DOF376、自由6266，不绑单个输入节点，不更新几何、工件或材料。
task与008仅三个描述键不同，input/path数值完全相同；与007比较仅原允许行程描述变动。
每张新任务仍独立从zero lift/zero fluctuation启动。

原控制器残差、约束、Armijo、25checks/12backtracks/4bisections、
minimum_increment=.1/16 和所有原force/Jv/CSC/KKT/body门原样继承。
有界数值线搜索及分步属于原控制器；正式阶段失败关闭后不补跑。
辅助energy仍explicit not_evaluated，不增加energy或all-column资格。

## 执行范围、预算及停止

prepare：一次只读输入/源码冻结，outer60 s，0 F/T/solver/HP。
production：一次独立完整九目标求解，helper600 s / outer660 s / sampled RSS8 GiB。
reference：仅整个productionpass后，一次独立新HP80/120复核；
helper240 s / outer300 s / sampled RSS8 GiB，每实际接受index包含重复目标与分步，
不能仅挑峰值/回零。旧参考方程、分母、尺度和门未改变。

首次正式失败保存部分路径及首个实际range输入，不增加F/T重建；
关闭卡，无修复重试/force/续时/跨卡拼资格。失败production不运行本卡reference。
资源是调用边界协作检查和采样进程树RSS；非操作系统硬中止，最终超预算不通过。
字段、call计数、完整source/physical输入hash和恢复hook须与真实终态相符。

## 可视化及完成条件

只从实际保存态显示输入力、自由输出位移、结构真实×1变形、J、Hu与工件弱式力，
并明确上半镜像方向、单侧/两侧标量/全装配net的区别；
几何距离、区域SAT和完整夹持/接触压力是另外的功能验收，不能从弱式力自动推出。
production与独立reference均pass后，才称本新任务机械与平衡门通过。
目标本项目仍是独立HF正向评估器，无LF优化、dmftd/MPM、无正式批量标签或排名。
