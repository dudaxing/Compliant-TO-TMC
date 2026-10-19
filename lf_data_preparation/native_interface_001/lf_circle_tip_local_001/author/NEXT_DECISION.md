# L-CTIPLOCAL1结果驱动的下一步

**唯一执行及8项数值对账PASS；视觉QA为NOT_PASS，整阶段尚未完成。** 原图与历史保留。本轮仅准备后续计划，不在已关闭的LOCAL1窗口重绘。

建议下一阶段L-CTIPLOCAL2先修复medium_locations图顶部标题重叠：只调整布局并在新目录生成一张介质定位PNG、普通渲染JSON及人工页；继承已通过tip图链接而不读取/重绘旧媒体。同两态、同5NPZ/12字段上限、零新F/T/HP/Newton，原物理与门保持。完成新图一次像素检查后，再决定是否推进1.04→1.05 mm；本轮未实施或执行下一阶段。

1. 最小问题与修订：保持原地图数据、Q1/Simpson/Hu定义、全部9861非工件介质选择、两态共同坐标范围/色标/颜色、原定位与tie语义。仅修正constrained-layout的rect语义及全局标题位置；rect是(left,bottom,width,height)，当前(0,.075,1,.95)导致top=1.025。候选可用(0,.075,1,.85)使top=.925、suptitle显式y=.985，给上排panel标题保留空间；真实效果由新PNG检查，不以参数意图替代像素结果。不要改数值、图像原件、默认HF或依赖版本。
2. 最小读取与源：只用原STEP8的两态accepted0/global9/d1.03、accepted1/global10/d1.04，及LOCAL1已封存localization.json/原ordinary descriptors/geometry JSON。新窗口至多一次读取相同5NPZ/12字段：model coordinates/connectivity/solid/workpiece_cells；各态lift/fluctuation和J/Hu。原producer seal及字段契约不变；不得额外读取F、应力、节点力、切线、矩阵、旧PNG/GIF/CSV或调用新力学入口。位置/原值继承已对账定位，不新增接触/压力定义。
3. 输出：新目录一张medium_locations.png，render.json记录同两态/同源身份、读取计数、原定位来源和仅布局修改，manual.html展示新图并链接已通过的LOCAL1 tip_closeup和旧力/收敛图。通过tip图仅继承链接，不重开/重新解码/重绘。无第二张新PNG、无新GIF；对唯一新PNG最多一次像素检查。旧布局失败图与pixel记录保持。
4. 拟预算和停止：helper180秒/outer240秒、采样8GiB、四库线程配置上限16，单次启动、首终端错误停止；仅原新窗口内保实际partial/封存。无修复重跑、外部重试、延期、force、回滚或删除。无新测试/构模/F/T/HP/Newton/平衡求解/默认安装。先完成可审查的最小候选与有限静审，取得新执行窗口明确授权后才读取数组/生成新图；含记录、普通main推送与异路径local Git恢复核对。
5. 完成与再决策：分别报告execution、numerical comparison和visual QA；只有新medium图实际排版通过才能补足此视觉缺口，不改写LOCAL1历史。随后依据既有真实定位和原门决定是否准备单目标1.04→1.05 mm，不自动开始。若后来推进，仍保minimum_increment=.00625 mm；.01可首次尝试，但失败半步.005低于原限值时按原规则终端停止，不降限值或加重试。

数值和空间观察已得到真实结果：两态原unsigned Q1尖端距离为25.986与19.131微米，近景采用共同等比例实际坐标，root检查tip_closeup通过。9861个全非工件介质单元中，minJ由0.0149381895254降至0.00828417040294；首个见证均为e11199/Simpson6、local[1,-1]、reference(80,30)，actual坐标严格等于该态tip。1.04 mm actual为[79.6884963855901, 30.980869329953457] mm，exact tie count=1。它表明所保存九点样本最小J位于该介质单元的尖端共享角点，不能单独认定首次接触、压力或有效夹持。

全介质maxabsHu由0.439837816292增至0.451802886616/mm。首个C-order代表为e11344/component[1,0,1]，signed值-0.451802886616/mm、reference中心[60.25, 30.75]、actual中心[59.981891483801434, 30.74971921671674] mm，exact tie count=2。这个首个代表在尖端左侧约20 mm处，且不在右侧x89..92参考条带；仅有首个代表及并列总数，不能宣称全部并列只在同一单元/位置。Hu逐单元常值，中心仅为代表标记；Hu场峰值位置不等于正则弱力主要来源、压力或夹持力位置。

输入R=0.188497437516 N；下半工件signed Fy total/material/Hu=0.00885936998869/0.0045643384771/0.00429503151159 N，沿用STEP8普通记录、未重新求力，镜像不翻倍。原物理、生产门、路径/参考/压力/有效夹持等资格保持。当前空间定位没有发现原标量对账矛盾（8/8精确），并非新增失败的力学证据。

但medium_locations图的全局suptitle与上排J/Hu标题真实重叠，root已将此图QA记为NOT_PASS；唯一执行和数值对账PASS不覆盖该排版缺口，stage_complete=false。原图保留、未在关闭窗口后重绘。当前源码给ConstrainedLayoutEngine的rect=(0,.075,1,.95)，该接口实际含义为(left,bottom,width,height)，其上缘为1.025而非.95；本机layout_engine.py说明已只读核实。这是可用小型排版修订解决的功能缺口，不能默默将pixel结果改PASS。

LOCAL2尚未实施或执行。原成果、视觉失败、生产物理/验收门及全部资格保持，不新增高精度参考、压力、有效夹持、释放/稳定性、网格/域宽收敛或HF5资格。
