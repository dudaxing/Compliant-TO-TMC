# 右侧介质余量：源码依赖读查

范围：只读本轮相关源码；不读running新结果，不写正式repo/geometry/protocol，不导入HF，不构造或调用F/T/solver/HP/观察/渲染。γ完整卸载和新参考尚待实际结果；本记录不选择下一张卡或预言padding效果。

结论：现有HF几何读取、原生映射与项目构造支持更宽的矩形HF数据包。最小真正新增功能是一个**显式派生HF分析域的几何入口**；不需要改变力学核，也不能把补域冒充重新优化的LF结果或原LF全域原生网格。

| 入口 | 已有能力／必须保持的含义 |
|---|---|
| `hf_repo/src/hf_eval/data.py:26,102–127,190–208,247–271` | Geometry按descriptor的网格与四个mask读取；域宽不固定80。新shape可为40×81或40×82、h=1 mm、origin/axes/y高度/厚度20 mm不变。新增列仅passive_void=1，其余三mask为0，满足分区。旧数组是只读对象（336–338），须新分配，不改旧包。 |
| `data.py:211–239,252–262` | 域与四mask参与geometry_id；tags/provenance参与descriptor SHA。补列必须获得新geometry_id/descriptor/NPZ与字段SHA，不能沿用旧几何身份。 |
| `hf_repo/src/hf_eval/regions.py:13–25,35–81` | 坐标/连接与tag索引由新nx重建；端口只要求物理轴对齐线段落在网格节点上，不要求在域外边界。原支撑、实体对称、输入线段及输出x=80,y28–30坐标和积分权重可保持。 |
| `hf_repo/src/hf_eval/native_map.py:33–56,59–86,98–105` | 映射不自动padding，但能读新HF包。LF背景来源仍按原descriptor给原区间的候选节点，明确不施加约束；可保留原LF provenance不改写。`native_geometry_preserved`仅指输入的派生HF网格在映射中不重采样。 |
| `hf_repo/src/hf_eval/native_project.py:30–33,142–181,197–241` | task仍使用当前唯一`analysis_grid.policy=native`，但绑定新HF几何。side18中心(71,40)、body[62,80]×[31,40]不变；新增右介质不改变解析工件选择。应用背景对称来自task，应把完整顶边延伸到x=81或82；原实体对称tag仍原坐标范围。 |
| `native_project.py:249,277–280` | `kr=alpha*length_mm**2*(kappa+4*mu/3)`；Lr独立于域宽。必须显式保留Lr=80 mm，不把它自动换成81/82。E、nu、gamma、alpha与Et沿所选完整合格基线保持。 |
| `hf_repo/src/hf_eval/lf_v2.py:54–58,79,142` | LF转换器明确无重采样且固定80×40域；补域应走新HF派生入口与`data.write_geometry`，不放宽或伪造这个LF转换合同。 |

派生policy/provenance应明确：operation=right_medium_padding；parent HF geometry/descriptor/NPZ及四字段SHA；原80×40物理子域四mask按行裁剪原字节一致；新增完整右列为介质；无重采样、阈值、清理、移动或重新LF优化。原LF provenance保留为历史来源；新的全域processing不能继续宣称ordinary_LF_v2_package/global source-native-grid-preserved。可记录“原LF单元在原子域保留，派生HF域全局新增”。旧绝对来源路径仅是历史语境，不成为新的运行依赖。

物理坐标保留不等于索引保留：nx变化会重排每一行的cell/node/DOF编号，不能比较flattened数组前3200项或统一加一个偏移。对照应按原逻辑单元(i,j)／原物理坐标映射；重建固定/自由集合、端口向量、工件覆盖与方向NPZ，不能raw复制旧方向。原右边界x=80成为内部分界，整条新增列都会产生介质耦合；这是分析域/边界余量敏感性，不只是局部工件右面补丁。

保存视图的已知依赖：`functional_views/workpiece_enlarge_20261007/complete_001/saved_shift_views.py:43,110,131,206`固定tip node2510。补域后的尖端物理位置仍(80,30)，编号须按坐标重选，不能raw复用当前viewer的2510假设。现有原生constructor/端口计算本身没有该假设。旧27数组raw全等与旧源向量/状态维度的卡不能用于补域身份声明。

尚无此派生域的构造、全周期、独立HP或保存几何证据；尚不能宣称余量收敛、域尺寸独立、网格收敛、压力/硬接触、自由工件夹持资格。可实现与物理合格是两个状态。待当前γ工况终态与参考到齐，再决定padding的基线与最小实验。
