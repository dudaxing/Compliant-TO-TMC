# L-CTIPAFORCE1：双α同峰节点弱力空间对照卡

2026-10-21，Asia/Seoul。**只读准备完成；整卡实施与执行尚未授权、尚未启动。** 本卡不沿用已关闭的 L-CTIPACOMP1 窗口。

## 决策与整体目标

LF负责独立优化，HF仅读普通几何，在一致任务下计算大变形／第三介质响应，供外部研究层比较。已完成的native输入、完整加载卸载与保存态续算是当前功能基础；正式夹持资格、完整路径独立参考及HF5资格仍未获得。HF不含优化，不调用dmftd，不实现MPM，不借用其他HF线的资格。

当前main `289450a8d27d915e1832beef9c75ca4fcc168232` 已完成双α的20原目标／260项描述差。1.06 mm处材料Fy增、Hu Fy减而总量较接近；峰值介质最小J更低。下一步先回答力的变化发生在工件哪些节点、如何在原四类节点间分配。峰值用于解释材料／Hu分量重分配，不代表最大反力、位移或总Fy差；1.02／1.03 mm仅留作后续候选。

## 真实工作区与只读恢复

- 正式Git根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；源码为其下`hf_repo/`，外层旧目录不是开发位置。
- `main`工作树干净；origin为`https://github.com/dudaxing/Compliant-TO-TMC.git`。本轮fetch成功，`main...origin/main`无差异；未pull、merge、rebase、提交或推送。
- 现有HF环境Python3.13.6、NumPy2.4.6、SciPy1.17.1、Matplotlib3.10.9、JAX/JAXlib0.11.0；不升级依赖、不移除严格选项。该环境仅作普通JSON与绘图，拟运行过程不导入HF力学包。
- 已核真实源码入口：`native_evaluate.py:evaluate_native`、`native_batch.py:evaluate_native_batch`与`native_force.py`／`native_tangent.py`。本卡不调用这些入口；只复用旧FORCE1的普通观察／显示语义及原SUP2。
- 正式状态、发展路线仍以仓库`docs/CURRENT_STATUS.md`、`docs/PHYSICAL_FUNCTION_PROGRESS.md`及`docs/RESUME_DEVELOPMENT.md`为准，不建立平行全局状态体系。

本次只读准备核对6份普通节点JSON、两份producer元数据、必要定义源码及既有普通对照记录。仅检身份、字段、SHA和结构；未重求节点合力、未计算新跨α节点差、未生成图、未执行候选／科学计算／测试。准备材料位于仓库外，冻结结果与正式工作树均未改。

## 固定输入与原语义

`input_inventory.json`固定6份普通JSON的真实路径、bytes与SHA，合计449948 B；`input_schema.json`固定字段与节点身份。每个源均为`nodal.json`、`derived.json`、`geometry.json`：

| 来源 | α | 实际保存目录（仓库相对路径） | accepted/global | d与原leg |
|---|---:|---|---|---|
|baseline|5e−7|`lf_data_preparation/native_interface_001/lf_circle_tip_step_010/run_001/view/wave_circle_tip_step10/001/`|1/12|1.06 mm loading|
|new|2.5e−7|`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012/`|12/12|1.06 mm loading|

原state SHA分别为`dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6`与`e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`。每源565节点；全局ID、固定工件坐标、mask及边连接已只读核对一致。四mask为互斥分区：physical_only71、cut_only35、physical_and_cut2、interior457；物理边与切面边的节点集合另有2个交点，不能混为重复分组。

保留原完整nodal／derived／geometry对象、节点ID／坐标／mask／边、三分量ON-body向量、原summary四组与合力、原holding总反力、原矩及37项row观察。原矩只保留，不新增力矩积分或移动原点。节点ON-body=-原内部弱力；只有total holding有原保存反力，材料／Hu反号只是代数显示，不能称独立测得反力。

工件固定坐标作为实际坐标的依据，继承各producer绑定的“工件全部lift与fluctuation为零”合同；本步不另读保存数组重验。两source的viewer封条与定义源码SHA已核对；元数据键原为viewer相对路径，按其声明解析，未改写原数据。准备时一次只读查询对键形式的错误假设及纠正已如实记录在`producer_provenance.json`。

两份原人工页只核大小并链接，间接提供既有变形入口，不打开／解码／重哈希／复制旧媒体。执行helper仅读上述6份节点JSON；协议、授权与源码读取另列为控制／来源读取，不另读task、summary、convergence、HP或source_history。

## 最小实施与唯一执行

整卡获明确授权后，先实现最小研究包装及显示模块，完成有限静审、冻结源码／六输入／协议身份，再唯一运行。若用户已批准本整卡，不重复申请相同范围。

1. 六输入按SHA读取，核accepted/global/d/leg/state SHA；按原节点ID精确配565对，不按坐标近似匹配，不筛小力或零节点。节点／mask／边不兼容须明确记录并停止，禁止重编号或改分类求兼容。
2. 复用原FORCE1的身份、finite、长度、原group count、原summary三力=derived六标量、原geometry／tip距离精确对账规则。原生产15项门、材料、边界、半径9／圆心(80,40)／right92／Lr80均保持，不重做科学验收。
3. 写1130条节点原值、565组配对、三分量各Fx/Fy共3390项new−baseline节点描述差；保原4组×2源结果及对应描述差，保原三力／holding总反力。math.fsum全体／原mask重组、与原summary之差、total−(material+Hu)尾差仅描述，无新容差门、不吸附为零、不生成恢复／能量／压力指标。
4. 生成一个包含原对象、原值／差量、原汇总及描述对账的普通比较JSON、恰2PNG和人工页。记录目标、做法、原因、实际效果和限制，链接原两人工页；不重新构造完整机构。
5. root对两新PNG各最多一次原尺寸检查，执行状态与图像QA分开。随后根据实际结果制定唯一近期下一步，更新现有状态入口，普通main提交推送、远端身份核对、同机异目录local-Git恢复及回执归档；不称异机科学复算。

## 两图与人工检查

图1`force_vectors.png`：2α行×total/material/Hu三列，共6空间面板；全部565点及向量，共同实际毫米坐标／等比例和跨两α三分量的单一箭头mm/N比例（共同最大模映射2 mm，仅显示换算）。`quiver minlength=0`，零节点另有点位标记，保小力，不逐面板归一化。原holding总向量在每源页脚明确列示，符号与ON-body相反。图仅固定下半工件、真实尖端／距离见证，不镜像倍增，不伪造全夹持器。

图2`force_components.png`：上两排分别旧／新源全部节点的有符号Fx、Fy散点；下排两α原四mask的Fx／Fy分量柱。相同分量旧／新共用量程；颜色区分三分量、柱纹区分α。原节点零值、负号、抵消、计数及微小差保留，科学刻度不使用易撞标题的offset。图看不清的密集／极小量如实记录，以原值表为准，不临时增加放大图或重绘。

原节点弱力不是局部面牵引或法向压力，不做径向投影；不据原无符号Q1距离认定接触／释放。细化布局见`VISUAL_PLAN.md`。

## 资源、完成及停止

唯一helper180秒／outer240秒，采样RSS1 GiB，OMP／MKL／OpenBLAS／NumExpr各最多16线程；两图顺序生成释放画布。输入约0.45 MB，不新增机械求解，此界限沿已完成普通图卡量级；线程数是配置上限，不声称实测16核利用。原SUP2同实例终止覆盖与句柄释放合同保持，不用PID消失替代，不增加force清理。

完成需：固定来源与身份通过、565对／3390差按原定义输出、两图／人工页及实际记录可审查，原结果与资格保持，普通发布与恢复核对通过。首个终端错误立即停止后续处理，保实际partial和原窗口内已产生证据；无外部重试、修复重跑、延期、force、回滚、删除或补绘。

不新增科学数组／CSV／gzip／旧媒体内容读取、构模、生产F／T、HP、平衡求解、测试、默认HF修改／安装、API关联或生产α调整；暂不加载新目标。既有峰参考各保原态与方向范围，不相互迁移，不升级全路径参考、压力、有效夹持、自由释放、稳定性、α独立、网格／域收敛或HF5资格。

## 意见与粗路线

当前阻断：无数据／身份阻断；本卡尚无整卡授权。证据是ACOMP已闭卡及下一阶段false；最小处理是批准本具体卡，不能默用旧窗口。

下一步前置：获授权后才编写包装，完成有限静审与身份冻结后唯一执行；当前只有计划和只读字段核对，不能称SOURCE或ACTUAL通过。

非阻断改进：六空间面板替代重复反号面板，原holding用文字；共同标尺与显式刻度减少遮挡。实施时采用该已固定布局，真实QA记录剩余可见性限制。

未来研究：先用峰值空间结果判断正则化贡献来源，再决定是否检查1.02／1.03 mm、调整物理任务或做受限网格／参数实验；其后才讨论可靠接触指标、可用夹持报告与外部研究层批量比较。不开新优化、不自动扩全路径审计或批量标签。

**本轮停在只读准备完成、近期整卡待授权。未开始编码。**
