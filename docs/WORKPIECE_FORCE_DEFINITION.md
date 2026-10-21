# 单侧工件作用力：定义与字段用法

本规则说明已有保存数据中的单位、方向、符号、分量、节点范围与字段位置，供外部研究层比较LF几何的非线性／TMC响应。它不改变现有力核、物理任务、保存数值或验收门。

已有结果与实际变形／力图集中在[保存研究报告人工总览](../lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/run_001/REVIEW.md)。完整原对象由[load_saved_study_report](../lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py#L54)返回；轻report只有索引、来源与资格，不能把其中的selector字符串当作节点数值。

## 当前对象、单位与厚度

当前双α比较针对固定圆形工件的下半模型：半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm，α分别为5e−7与2.5e−7。全部工件节点的ux／uy均固定；这不是自由工件承载或释放试验。

这两个比较来源各自的几何快照与model材料元数据都明确指定厚度20 mm：

|来源|α|实际保存model的厚度字段|
|---|---:|---|
|baseline|5e−7|[wave_circle_tip_step10/model/model.json，187行](../lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/wave_circle_tip_step10/model/model.json#L187)|
|new|2.5e−7|[wave_circle_tip_alpha1/model/model.json，187行](../lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/model/model.json#L187)|

厚度由geometry的`thickness_mm`提供。task绑定几何ID和描述符SHA，不必重复存一个厚度键；task没有thickness键不等于模型厚度未指定。[native_project.py:251](../hf_repo/src/hf_eval/native_project.py#L251)把几何厚度显式传入TMCModel，[tmc.py:88](../hf_repo/src/hf_eval/tmc.py#L88)传给operators，[tmc_kernel.py:65](../hf_repo/src/hf_eval/tmc_kernel.py#L65)将其计入面积积分权重。当前NumPy力核在[材料项](../hf_repo/src/hf_eval/split_kernel_invariants_hu.py#L173)及[Hu项](../hf_repo/src/hf_eval/split_kernel_invariants_hu.py#L178)各使用一次这些权重，[public NumPy入口](../hf_repo/src/hf_eval/native_force.py#L58)不再乘厚度。

因此，现有`*_N`是已计入原模型厚度的N，不能再乘20，也不能未经另行定义就标为N/mm。积分前应力的MPa与积分后节点弱力的N是不同对象；原矩为N·mm。**20 mm仅指上述两个实际来源**；其他模型须读取各自geometry／model，不沿用这个数值或generic TMCModel的默认厚度。

逐条源码、两model／几何文件SHA及量纲链见[厚度与单位证据](../lf_data_preparation/native_interface_001/lf_circle_tip_force_definition_001/author/UNITS_SOURCE_AUDIT.md)和[对应JSON](../lf_data_preparation/native_interface_001/lf_circle_tip_force_definition_001/author/UNITS_SOURCE_AUDIT.json)。厚度元数据明确，不等于实物厚度或承载能力已经验证。

## 有符号的下半工件作用量

原坐标+x向右、+y向上。对每个原工件节点及每个分量，ON-body保存约定为：

`工件节点ON-body力 = −对应global内部弱力`

负号与节点选择见[workpiece_nodal.py:53](../hf_repo/src/hf_eval/workpiece_nodal.py#L53)。下半工件合力采用全部原工件节点的原保存合力，不重新求和、筛小力、取绝对值或截零。

竖直报告量命名为“下半固定工件竖直作用力（有符号，N）”，直接读取合力Fy。正值表示模型对下半工件沿+y作用，负值保留−y方向；同时报告Fx、α、source、原leg、d、accepted／global序号及state SHA。圆形边界的局部法向沿边变化，竖直合力不是某处局部法向压力。

既有producer字段`normal_force_on_lower_body_N`在[native_mean.py:100](../hf_repo/src/hf_eval/native_mean.py#L100)直接赋值为total Fy。它的历史键名保持不变，使用时解释为上述竖直合力。当前研究周期的对应字段是`total_body_Fy_N`；producer的`normal_force_on_lower_body_N`没有作为当前两份comparison的可读取字段提供，reader没有它的直接selector。

## 三分量与holding

原分量键为`total`、`material`、`regularization`；Hu是最后一项的解释名称，不替换原键。三者来自同一离散弱式与原组装顺序。total与两分量的重组关系按原表达解释，已有浮点尾差保留，不增加逐位相等门或重新计算差值。

material与Hu分别报告。total接近不能证明分量接近或α独立；Hu不能静默删掉，material也不能独自当作已验证的真实夹持力。

`holding_reaction_on_model_N`是保持固定工件的原总支撑反力。在当前工件没有外加端口力的任务中，其方向与ON-body total相反。[节点summary](../hf_repo/src/hf_eval/workpiece_nodal.py#L70)独立保留这一总向量。当前返回nodal对象不暴露material／Hu独立holding或逐节点holding数组；分量反号只是代数记账，不是新增的反力测量。原producer确有`support_reaction`数组，此接口边界不表示该原数组不存在。

## 对称镜像、节点分组与原矩

当前y=40 mm对称任务的producer针对total定义以下不同报告量，源码见[native_mean.py:100–102](../hf_repo/src/hf_eval/native_mean.py#L100)：

|量|既有producer表达|解释|
|---|---|---|
|下半工件合力|`(Fx,Fy)`|原下半模型有符号作用量|
|镜像上半工件合力|`(Fx,−Fy)`|对称推导，非另一次上半求解|
|完整工件全局净力|`(2Fx,0)`|不能用y净力为零否认相向作用|
|两侧竖直幅值和|`2*abs(Fy)`|不是完整工件净力，也不自动是合格夹持力|

镜像、完整净力、两侧幅值和及producer的holding DOF分区，均未作为当前两份comparison rich对象的可用字段提供，reader没有相应直接selector。上述公式解释既有producer语义，不向当前rich对象补算或插入数值。holding DOF分区也不是下述工件节点几何mask。

四个原节点mask为`physical_only`、`cut_only`、`physical_and_cut`、`interior`，当前两峰计数分别为71、35、2、457。这四类构成节点分区；physical边与cut边的节点集合另在两个角点重叠，见[原mask构造](../hf_repo/src/hf_eval/workpiece_nodal.py#L36)。不能把交点弱力任意归入某个入射边，也不能只取physical_only当作接触力。正式下半合力沿用全部原工件节点，不删除交点、interior或微小项。

原矩应与`nodal.moment_origin_mm`一起读取。源码[默认原点](../hf_repo/src/hf_eval/workpiece_nodal.py#L44)为工件节点均值，或采用调用者明确给定的点；不能默认圆心。原z矩正号为`x*Fy−y*Fx`，坐标是相对该原点的力臂，见[原矩表达](../hf_repo/src/hf_eval/workpiece_nodal.py#L62)。使用保存值，不重积分或平移原点。

节点弱力不是可归属于单一相邻面的连续牵引，不能除以任意节点面积就称压力。已有无符号几何距离也保持原定义，不以微小距离或力阈值宣告接触、释放或有效夹持通过。

## 使用现有reader返回对象

下表是字段位置说明，不再次调用API。`study`是现有函数已经返回的对象；`s`为`baseline`／`new`，`c`为`total`／`material`／`regularization`，`a=0/1`表示Fx／Fy，`i`为原节点位置，`g`为原mask名，`j`为周期行位置，`p`为相应配对表位置。配对须看记录身份，不能把数组位置当accepted或global序号。

为缩短字段路径，下表使用以下对象缩写，均指原返回对象而非新函数：

- `C`：`study["cycles"][s]`。
- `S`：`study["scalar_comparison"]`。
- `P`：`study["peak_node_comparison"]`。
- `N`：`P["sources"][s]["original"]["nodal"]`。

|所需原数据|精确selector|用法|
|---|---|---|
|完整原周期|`C["timeline_rows"]`|保原角色、来源、原目标／接受态身份|
|周期三力Fx／Fy|`C["timeline_rows"][j][field]`|field为下列六力键之一，单位N|
|选定峰三力Fx／Fy|`P["sources"][s]["state"][field]`|当前global12／loading／1.06 mm；旧accepted1、新accepted12|
|节点三力|`N["forces_on_body_N"][c][i][a]`|与`node_ids[i]`、`coordinates_mm[i]`、`masks[g][i]`同位|
|原下半合力|`N["summary"]["force_on_lower_body_N"][c][a]`|全部原工件节点的原保存合力，N|
|原total holding|`N["summary"]["holding_reaction_on_model_N"][a]`|一个原总反力向量，不是三分量或逐节点holding|
|原mask合力|`N["summary"]["groups"][g]["force_on_body_N"][c][a]`|节点分类贡献，不是面牵引积分|
|原整体矩|`N["summary"]["moment_about_origin_Nmm"][c]`|同时读取`N["moment_origin_mm"]`，N·mm|
|原mask矩|`N["summary"]["groups"][g]["moment_about_origin_Nmm"][c]`|保持原参考点及原分组|
|节点身份／边|`N["node_ids"][i]`；`N["edges"][edge_group]`|edge_group为closed／physical／cut；边端点是global节点ID，不是位置i|
|同α既有加载／卸载对照|`C["same_input_pairs"][p]["metrics"][field][within_value_key]`|7个原配对；仅使用原within键|
|跨α既有标量对照|`S["pairs"][p]["metrics"][field][cross_value_key]`|20原目标对；保global_index／display_branch／d／两SHA|
|跨α既有节点对照|`P["node_pairs"][p]["on_body_N"][c][cross_value_key][a]`|565对／3390已有分量差，保node_id／mask／raw索引|
|跨α既有mask对照|`P["group_pairs"][p]["force_on_body_N"][c][cross_value_key][a]`|4对／24已有分量差；按记录group识别g|
|跨α既有整体三力对照|`P["whole_resultant_comparison"]["force_on_lower_body_N"][c][cross_value_key][a]`|6个已有分量差；没有新增holding分量差或矩差selector|
|轻索引峰关联|`study["report"]["peak_links"][s]`|身份及对象位置；节点值须取P原对象|

六个原力键是`total_body_Fx_N`、`total_body_Fy_N`、`material_body_Fx_N`、`material_body_Fy_N`、`regularization_body_Fx_N`、`regularization_body_Fy_N`。跨α13个metric另含位移、距离、J和Hu等非力值；不能把整个metrics表都标N。

两类原值键必须分开：

|对照|原值／差量键|
|---|---|
|within-alpha|`loading_value`、`unloading_value`、`unloading_minus_loading`|
|cross-alpha|`baseline_value`、`new_value`、`new_minus_baseline`|

零位within配对的参考raw leg仍是`origin`；`loading_value`只是原列名，不证明存在loading零态。不混用两套键，不重新减法、插值、计算比例或引入归零门。

reader[直接保留原对象引用](../lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py#L144)，并[核对同一α两峰的37项原观察](../lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001/saved_study_report.py#L103)。这仅是既有来源关联，不是新的力学通过；原source、α、accepted／global、leg、d及state SHA分别保留，不能按同d合并加载／卸载或转移参考范围。精确字段与源码定位另见[字段图谱](../lf_data_preparation/native_interface_001/lf_circle_tip_force_definition_001/author/FORCE_FIELD_MAP.md)及[JSON图谱](../lf_data_preparation/native_interface_001/lf_circle_tip_force_definition_001/author/FORCE_FIELD_MAP.json)。

## 适用边界

本规则让既有力值的单位、对象、方向、符号和字段取用可复核，不新增函数、指标、科学通过记录或资格。各源原qualification分别保留，缺失字段仍缺失；选定态／方向参考不迁移为完整路径独立参考。

固定工件弱力、原分组、已有图像及输入回到零，都不能替代自由工件承载／释放任务，也不授压力、有效夹持、稳定性、α独立、网格／域收敛或HF5资格。进一步物理验证需要明确允许的工件运动、外载与成功条件，并另行定义任务。
