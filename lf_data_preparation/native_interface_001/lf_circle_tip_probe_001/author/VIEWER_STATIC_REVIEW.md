# L-CTIPPROBE1：纯保存态显示候选独立静审

2026-10-22（Asia/Seoul）；审阅者 `/root/move_runner_impl`，未编写本viewer。本轮只读源码及普通冻结定义；未导入HF／NumPy／Matplotlib，未解码NPZ、执行viewer、读取媒体内容或进行像素检查。

最终候选：`D:/hpr1_001/render_probe1.py`，27072字节，SHA256 `65a96a9efe56dc6d3aeffa1982a6ba739adb73ed2bb003d72d03a198e63b4dd0`。**12／12项静态通过，未见当前启动阻断。** 这只核源码定义与接口相容，不声称图已生成、排版已通过、实际字段／帧数已满足或真实工件路径成功。

冻结协议实际普通文件：`D:/hpr1_001/protocol.json`，18337字节，SHA256 `fb68f482a312c6b26f40f59aab5100ec06cb07f73ac0b08c67322815b1797d57`；status=`frozen_ready_for_unique_authorized_launch`，68个binding。其viewer条目与上列实际SHA／字节完全相符；observer条目89917字节／SHA `c2ed1eb05a4934710f1ecf71dc6eacb80dd52bcfa7c6888eb9aad88258f5b638`。协议声明600秒／8GiB、字段[J,Hu]、3PNG、至多5态，与本审查一致；未修改协议或其binding。

|项|静审结论与依据|
|---|---|
|1 入口及纯度|只使用stdlib、NumPy、Matplotlib和PIL；没有HF import、API、F/T、HP、Newton或subprocess调用。CLI明确protocol／new result／新output目录，output已存在即拒绝。|
|2 新schema|读取`hf-native-guided-probe-1.0`的accepted_steps、model.reference coordinates／connectivity／solid及保存actual positions，要求成功且2..5态；不调用原fixed-body viewer或旧nodal入口。|
|3 固定观察成员|body cells/nodes、right480 cells、right81 nodes、tip、input weights取冻结observer；核body节点匹配新model、body连接集合和right非solid／非body。移动后不按新x重mask。|
|4 科学字段读集|逐新态只读取fields archive一次，仅索引J／Hu。逐archive SHA及两字段dtype／shape／原数组SHA核对；J为(ne,9)，Hu为(ne,2,2,2)，有限且J>0。无新state／F／force数组或旧科学缓存读入。完整5态最多5 archive／10字段。|
|5 物理边界与切面|最终版本145–149行保留full edges绘图；另以reference y=40剔除body／solid symmetry-cut边。179–183行tip／全物理边界／body-right距离和strict-boundary节点均用physical edges；右域侧边仍是其81个原节点。初稿未排切面的问题已修，未通过改数据或像素回放掩盖。|
|6 实际几何|所有结构填色和实际边界取本次positions，坐标轴等比例、无位移放大；参考轮廓单独虚线，q0／末态与每帧明确q和input hold。右界标作actual free right boundary，未画成固定墙。|
|7 距离／内部观察|point-to-segment、segment相交及双向vertex-to-edge使用实际坐标；严格内部节点只作binary64几何观察。没有使用接触核或把距离当压力／夹持判据；不把未观察到crossing等同于完整无交叠或稳定性证明。|
|8 力的口径|Q总／material／Hu、ON-body Fy与机构R独立面板；保存signed q0和ΔQ，明确Q=-ON Fx、half N已含t20、只有显式轴向全装配换算才2Q。箭头mm/N尺度写明，绘图锚点不是牵引分布。|
|9 控制与收敛|实际q对接受序号，input mean-hold另轴并显示原constraint bound；全newton_history按实际检查序号画residual和正J，未将恒定target_displacement误作新输入行程。保全部trials／failed_attempts／linear diagnostics进表。|
|10 介质及定位|right480格采用新actual网格，cell min J用全新数据最小值的log颜色，不裁掉小J；Hu为cell最大绝对分量。全非body介质minJ定位用原九点Q1插值，Hu定位明确是cell-centroid，非虚构采样点。|
|11 三图／实际动画|源码只生成01_actual_geometry.png、02_force_and_convergence.png、03_right_medium.png与animation.gif；每个实际接受态一帧无插值。最终只打开新GIF一次核实际n_frames=N，receipt记录metadata读取1次；不读取旧媒体。|
|12 记录／时间／资格|600秒原viewer时钟含imports、归约、图像和receipt，另由SUP2硬窗约束。state_table保逐态原标量、三力、互斥ledger、q0差量、J／Hu与几何摘要及source SHA；component求和尾差仅描述，无新门。输出清单有大小／SHA，receipt读字段／帧／科学调用声明可供runner核；独立HP／有效夹持／释放保持false。|

数值与图片仍须实际执行证明：原API先完成全数值门及q0身份检查、helper调用唯一viewer、实际receipt计数匹配，然后root对每新PNG至多一次检查。源码静查不能证明运行时清理、字体布局、颜色可读性或物理成功。

纯几何观察限制为既存新positions的binary64计算与原单元边界拓扑；不计算科学力或压力，不授完整接触、释放、稳定性、域宽或参数独立资格。必要资源／source封存／root外层监督分别由其他记录核，不在本审阅内替代。

本审阅实际调用数：scientific imports=0，NPZ decode=0，HF／API／F／T／HP／tests／viewer=0，media reads=0，new PNG=0。
