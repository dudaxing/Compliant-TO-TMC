# L-CTIPAFORCE1：两张峰值节点弱力图的显示方案

本文件仅为准备期布局建议，没有实现、绘图、执行或新授权；不能复用已关闭的ACOMP1窗口。依据ACOMP1现成比较JSON、已发布NEXT及旧FORCE1的`force_views.py`源码；本人未另读取两alpha的nodal/derived/geometry文件、科学数组或媒体。

根Agent后续完成普通输入身份/schema绑定：6份JSON共449948 B，两alpha各565个固定工件节点，node ID、固定坐标、四mask和边数组一致。新source为`lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012/{nodal,derived,geometry}.json`（共同前缀`lf_data_preparation/native_interface_001/`），global12/accepted12；详细路径及字段按新卡`input_inventory.json`和`input_schema.json`。本方案引用该绑定结果，没有另读节点JSON或计算新力指标。

只比较旧alpha=5e-7与新alpha=2.5e-7的原加载1.06 mm峰。该峰用于解释material/Hu分量重分配，不代表全程最大R、q、距离或total Fy差。1.02/1.03仍是后续候选，不进入本次图的数据范围。

## 图1：全部节点的空间弱力与原保持总向量

建议`force_vectors.png`为 **2行×3列，21×12英寸、160 dpi**：每alpha一行，三个原分量各一列。只画原ON-body节点向量，holding采用每行页脚的原总向量及符号说明，不重复绘制纯代数反号面板。

|行/列|total ON-body|material ON-body|Hu ON-body|
|---|---|---|---|
|旧alpha=5e-7|原total节点向量|原material节点向量|原Hu节点向量|
|新alpha=2.5e-7|原total节点向量|原material节点向量|原Hu节点向量|

- 六面板共用一套实际毫米坐标范围和等比例轴。范围由两source的全部固定工件坐标、尖端及原最近点见证的并集决定，并留至少2.6 mm边距；不根据最大节点力位置自动缩窗。固定下半工件是实际×1，既不镜像倍增，也不补画完整夹持器。
- 沿旧FORCE1的显示转换，**两alpha×三个原分量共同的最大向量模映射为2 mm显示箭头**，因此全部六面板共用一个`mm/N`比例。这只是箭头显示换算，不是新力指标、力阈值或位移放大。图头明确打印比例和“N对应多少mm箭头”，不逐面板自动归一化。
- 原total/material/Hu配色沿旧FORCE1，行名明确alpha、列名明确原ON-body分量；公共图注即可，无需六份重复图例。每面板全部565节点均保留浅色小节点标记，565个向量不筛选、不抽样、不按力大小截断。`quiver`固定`minlength=0`，避免零力被画成有限长度箭头；零向量仍有单独节点点位和原表记录，小力不裁除。
- 在每面板保留原工件闭边、实际tip与其最近工件点、原global closest pair。沿旧金色/紫色几何见证符号，明确连接线表示距离，不是力；约8–10微米距离在全工件尺度不可凭图分辨，原值在页内列出，不另生成放大图。
- 每alpha行页脚分别列出该source原保存的total holding reaction `[Fx,Fy] N`，明确其方向为`−ON-body total`，与原工件ON-body合力分开说明；不另画反号节点箭头。material/Hu反号仅为代数分量账本或显示，不作为独立测量或独立保存的支反力数组。

旧FORCE1 `_context/_map_base/_render_vectors`的边界、比例和符号定义可作为显示语义参照；这里只把共同范围/比例扩到两个source，采用2×3的alpha/分量布局及原holding总向量文字，不另解释局部压力。

## 图2：原节点Fx/Fy和原mask组贡献

建议`force_components.png`为 **3行×2列，18×15英寸、160 dpi**：

|位置|左|右|
|---|---|---|
|第一行|旧alpha：全节点total/material/Hu Fx|新alpha：全节点total/material/Hu Fx|
|第二行|旧alpha：全节点total/material/Hu Fy|新alpha：全节点total/material/Hu Fy|
|第三行|两alpha：四个原mask的有符号分量Fx|两alpha：四个原mask的有符号分量Fy|

- 前两行使用原global node ID作横轴，全部节点以散点显示，不用连线虚构空间轨迹。旧/新同一分量轴共用横轴范围和纵轴范围；Fx与Fy各自定范围，以免较大的Fy压扁Fx。保持正负、零及抵消；不对数值取绝对值或改为径向分量。
- total/material/Hu颜色沿原三色；alpha由源列区分。下排每mask的三分量各放旧/新相邻柱，颜色区分分量，实填/斜线纹区分alpha；只需一份三分量公共图例和一份alpha填纹说明，避免八条以上重复线图例。上下排标明节点值与组结果不同，不能用相同图形高度代替数值比较。
- 下排直接使用各source原`summary.groups`有符号分量和原node_count。已绑定的四类节点mask是互斥完整分区：`physical_only`71、`cut_only`35、`physical_and_cut`2、`interior`457，两alpha相同。另一个概念是physical边节点集与cut边节点集，它们恰有2个共有节点；不能把这两个边节点集合当互斥分区相加，也不能把四个互斥mask描述成相互重叠。
- 纵轴采用显式逐tick科学计数，避免offset与标题相撞；横向零线始终保留。微小负值或被大值遮蔽的差异由普通JSON及足够精度的人工表保留，不做地板、裁零或筛节点。该图不新增保持率、能量、压力或接触验收门。

## 人工页与一次检查

人工页保留两峰alpha/d/原leg/原target index/SHA，来源文件与原字段路径、原全部节点/分组数据、原三分量合力和原holding总向量。两张新图仅显示固定工件和已有机制见证点；完整结构仍链接原人工页的既有变形入口，不开旧媒体，不拼接或重绘夹持器。

执行前应按已绑定的每alpha各3份普通JSON路径和字段完成新整卡静审。获新整卡明确授权后唯一运行，用户若已明确授权整卡，不重复申请同一范围；当前准备文件不构成授权。拟helper180/outer240秒、采样1 GiB、四库线程上限16，两个图顺序生成和释放画布，不同时保留两个大画布。

两张新PNG实际产生后，各最多一次原尺寸人工检查，主要核对：

1. 两source确为相同1.06 mm加载峰，原SHA/alpha/leg正确，未混用resume anchor或卸载态。
2. 六空间面板轴范围、等比例和`mm/N`相同，箭头及箭头头部未出界；没有源间自动缩放、小力筛选、节点缺失或镜像倍增。
3. 全部零节点仍有标记；原负向Hu、抵消与微小值未裁除。密集箭头不可分辨时如实记录，原表可追溯，不能临时修复重绘。
4. 每alpha行页脚原holding total及`−ON-body total`约定清楚，material/Hu反号仅是代数分量，不包装成独立测量、新保存数组或新求解。
5. tip/最近点连接线与力箭头区分，图中没有根据少量见证点虚构全机构变形，也没有把正距离判为接触或释放。
6. Fx与Fy量程分别清楚，旧/新同分量量程相同；四mask互斥分区、两个边节点集合交2节点及各node_count语义可读；公共图例、科学刻度、标题和页脚无拥挤或遮挡。

保持首个终端错误停止、真实partial和原结果资格；不新增科学数组/CSV/gzip/旧媒体内容读取、构模/F/T/HP/平衡求解/测试、生产alpha修改或默认HF改动。节点全局弱力不是某个相邻面的牵引、法向压力或有效夹持力；不做径向投影。原峰HP范围、全路径资格和释放/稳定/alpha独立性均不因新图升级。
