# L-CTIPLOCAL3结果驱动的下一步：L-CTIPREF1

本轮保存态定位执行PASS、8项原精确比较PASS、两张新PNG各一次实际检查PASS；可闭卡。当前未增加目标或资格。

建议下一阶段 L-CTIPREF1：仅对STEP10真实accepted1/global12/d1.06 mm保存态执行HP80/120各一次，复用原十五门核材料/Hu/总力、同一PORT方向切线、CSC/KKT及工件弱式合力，全部通过后生成一张原误差/limit图与普通JSON。先保留1.07 mm，待参考实际结果再决定。本轮只是待新授权的具体提案，未实施或执行HP。

最新两态的全介质minJ现已逐态定位到实际最右tip，而不是right89..92条带；1.06 mm的J=0.0009015839179744192、Q1最近距离9.887525微米。Hu最大分量首代表在e11344内侧连接附近，和tip强压缩点空间不同。这消除了“压缩位置是否来自右条带”的当前信息缺口，但没有为该c80/right92布局建立独立高精度力/方向切线参考。结合本段首次factor1 invalid_J内部拒绝后factor.5恢复，先核一个最新峰值保存态，比直接增加1.07 mm更能回答当前高压缩计算是否数值一致；不把小J标量或内部拒绝改成新失败门。

1. **唯一状态与原物理。** 来源为STEP10的`run_001/wave_circle_tip_step10/result.json` accepted1/global12/child1、loading1.06 mm、非continuation anchor，逻辑state SHA `dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`、signedR=0.19568183324206792 N。不能误用LOCAL3的显示JSON或continuation祖锚。完整load_only前缀、r9/c(80,40) mm固定圆形、right92/Lr80、h.5mm、厚20mm、E1/nu.3/plane strain、gamma1e-6/alpha5e-7、原边界/平均端口及设置/门不变。当前模型14720单元/14985节点/29970DOF，fixed1288/free28682；不求解新平衡或改原结果。
2. **薄包装适配。** 以既有`lf_circle_reference_001/execute_circle_reference.py`圆形loader及原pure误差plot为基础；B850 `CoreAudit.run_state`与aa86 `workpiece_checks`原数学字节继承，11数学依赖按唯一basename平铺归档，driver/plot另归档。只在研究包装重新绑定当前c80/right92准备/保存模型证据、load_only全前缀、生产两态[1.05,1.06]与global11/12、selected child1/global12/loading、当前full counts/source/descriptor与真实F15 started14 completed/T8。不能保留旧c71/旧13440/27378/global5或旧square/卸载假设，不能把一次正常invalid_J内部拒绝当源失败；不写新力核、不改默认HF。候选和绑定需有限独立静审后才执行。
3. **明确的新读取范围。** 新窗口读取/绑定6份既存NPZ：model、选中state/forces/tangents/CSC、source_geometry。前5份解码；source_geometry仅原字节来源身份。延续原51个descriptor字段及aa86重开state/forces的18次重复字段出现（共69；CSC另format/shape两个必要容器成员与原可选_is_array探针），不把7次loader说成仅5次。准备期只用旧producer seal/manifest/普通descriptor加stat，不读payload/header；payload身份核对/归档及所有数组读取仅在新唯一helper窗口内。既有数学依赖导入JAX/注册包装不等于执行AD/JIT。
4. **原独立数学与十五门。** HP80/120各一次覆盖全部14720单元及29970DOF，材料/Hu/总局部和全局力；Decimal3000 scatter并trap Inexact保持。原方向为v=b_in/maxabs(b_in)，固定分量0、deltaR=0，比较总/材料/Hu同一PORT方向切线作用、保存CSC全系数组装身份与KKT；这不核全部切线列。原工件ON-body/holding去重分组、overlap、mirror及dummy内部检查保留；圆形legacy normal字段只解释全局Fy，不是圆周局部法向压力。

   原十五门及分母/floor/局部规则/投影顺序全部保持：production residual1e-9、independent residual1e-8、force evaluation1e-9、average constraint1e-10、global balance1e-6、fixed8e-11mm、HP80/120一致1e-40；total/material/Hu force为1e-11/1e-9/1e-9，total/material/Hu方向切线为1e-10/1e-9/1e-9，KKT force/mean各1e-10。不给工件Fy另造百分比门，不增加stress/energy/独立Hu数组门或小J阈值。
5. **显示、资源与首错。** 全部原参考和工件检查通过后，同一helper只调用一次原pure误差plot，仅读本次新accepted_012/summary.json，输出1PNG及普通JSON，显示原10项error/limit，Decimal40 log10只作显示、零误差保零、无新floor/门。当前LOCAL3两图与原反力/收敛仅链接，不重读旧媒体，不新画结构/GIF。一次helper900秒/outer960秒（最多16分钟）、采样8GiB、四库线程上限16；含批准/来源、import、读数组、归档、两HP、比较、plot与完整seal。首个终端错误停止并保真实partial/实际HP与plot计数，无修复重跑、重试、延期、force、生产F/T、构模、Newton/平衡、测试、API关联、reader修改、默认安装或回滚/删除。HP内部无checkpoint时等待真实返回，迟到PASS不通过；采样RSS/合作stop不是OS硬限。新PNG最多检查一次，不自动重画。
6. **记录和再决策。** 数值执行与视觉QA分别记录，保本轮/祖先全部结果、资格与LOCAL1失败历史；普通main推送及同机异目录local Git恢复，origin不变。若通过，根据实际误差、当前压缩/位置、力与成本再提出下一目标；若失败按实际证据排查，不静默放宽门或重跑。1.07 mm尚未授权；本提案不执行后续加载。

仅这一态/两HP的独立归档，不关联或改写生产response，不修改reader要求；不能当作完整两态、完整路径、全切线列、连续压力、有效夹持、卸载/自由释放、稳定性、制造、网格/域宽收敛或HF5资格。当前LOCAL3窗口已关闭，L-CTIPREF1实施与执行需新的明确授权。
