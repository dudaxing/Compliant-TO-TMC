# 第三个LF夹持器：确定性源选择与边界元数据核对

2026-10-15（Asia/Seoul）。本轮用户已直接授权第三LF输入与未变形兼容检查、记录及可视化，并依据结果安排后续计算；此授权范围由主任务转交。本子任务仅定位源数据、读取普通描述并记录，不代替实际兼容检查或新增力学执行授权记录。没有从本文或源文件中的说明推断新授权。

## 选择结果与非性能规则

选取 `gripper__refine__kin_1e+00__kout_1e+00__wave`。规则在查看响应前固定：只在既登记30份交接集合中筛case=gripper、native_mesh=[160,80]、cell_mm=[0.5,0.5]，按descriptor member字典序排列，排除两既有LF geometry_id后取第一例。没有使用LF性能、HF反力、位移、预计成功率或排名选择。formal1800集合只核中央目录数量，不再扩选。

| 字典序 | design_id | 声明LF geometry_id | 处理 |
|---:|---|---|---|
| 0 | `gripper__refine__kin_1e+00__kout_1e+00__random` | `ed54b3c0507fd4e87ac327040c7b5eb313d872c7fa99b3418243947b424f8756` | 已用fine，排除 |
| 1 | `gripper__refine__kin_1e+00__kout_1e+00__wave` | `a8d12d0fbe070ac74e52193311f1acb6738367c5d7fb9af726bdc99b380667b9` | 选定 |
| 2 | `gripper__refine__kin_1e-01__kout_1e-01__random` | `4d4ae4a0681b195bf1a47bb97b5ae11175dbc327f96aba54da4ceff1a1ba46b4` | 后续未选 |
| 3 | `gripper__refine__kin_1e-01__kout_1e-01__wave` | `93d01a332aba33b84e8201ee339bf69387f71173cb7deda037de749489c53a71` | 后续未选 |

两既有LF ID为canonical `e8b33bb9121e3f2d6267422ec1e3bfcc149b6b37ae573534504b08b9a65b00a9` 与fine/random `ed54b3c0507fd4e87ac327040c7b5eb313d872c7fa99b3418243947b424f8756`。新wave声明ID为 `a8d12d0fbe070ac74e52193311f1acb6738367c5d7fb9af726bdc99b380667b9`；尚未解码NPZ重算该ID或核实际掩码不同。新HF准备后的ID也尚未产生，不能与LF原ID混称。

## 源身份及数量证据

源为用户显式提供的 `C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (10).zip`。实际归档身份检查终端d9bb64/exit0确认81,618,414 bytes，读取JSON前后整ZIP SHA均为 `79c44fbf2570651539137d74299714823c8046d13efd9c3bad6eb32bc389745e`，与既有source_inventory和grid_inventory一致。整ZIP身份哈希读取压缩归档字节；没有打开、提取或解码任何NPZ成员。

本次ZIP中央目录实际计得30个hf_export_v2交接design.json与1800个formal gripper design.json。既存30包元数据清单记录23个h1、7个h0.5；其中4个gripper h0.5描述本次均实际读取、逐SHA与清单核对。没有重新核全30个NPZ或1800个实体/被动区；不能把数量核对当作其转换或力学验收。

候选descriptor member：`Diversity-TO-Compliant-O-main/research/hf_export_v2/gripper__refine__kin_1e+00__kout_1e+00__wave/design.json`；原字节10,458 B，SHA `8d6629a966dab7411709c53c8c798cf6ee77c1a07446174aac9bca52162864f8`。数组member为同目录design.npz，中央目录长度1,483 B，声明SHA `972339221c71f30b37c9847277d484f5655217a0968a64bdb2a691de7301c736`；本子任务未读取其成员内容，因此数组实际SHA与掩码仍待兼容检查。

## 普通描述中的边界和网格

候选schema dmftd.hf_export.v2，native160×80、h0.5、域80×40 mm、厚20 mm、lower-half／y=40镜像线。声明输入为(0,38)-(0,40)、direction+[1,0]；输出为(80,28)-(80,30)、direction+[0,1]。两端口均normalized_reference_arclength_trapezoid，五权例[.125,.25,.25,.25,.125]；这些是源声明，实际consumer节点和权重仍须按准备入口核对。

support声明(0,0)-(0,8)、ux/uy、solid_incident；solid symmetry为(0,40)-(60,40)约束uy。background是y40上(60,80]的open_closed complement，source_policy=full_midline。它不能静默改成另一套支撑策略。当前HF既有明确84×40分析域的右侧纯medium扩展与task定义需通过同一已安装准备入口显式继承，原LF几何仍80×40，不能改写原包来迎合任务。

原LF native diagnostics声明4349实体单元、connected4/8=true、ports attached=true、fixed_nodes_attached=5；这是源的已有声明，不是本次HF附着、掩码或模型检查通过。LF生成参数和旧观测没有作为筛选依据，也不成为本次HF材料、工件或控制任务。

## 实际旧HF输入的明确对照位置

以下都由已保存model.source_geometry.snapshot定位；descriptor原字节SHA已核，NPZ只stat。它们是未变形HF输入快照，绝非旧位移或变形数据。两者声明solid shape均[80,168]，适用于第三例准备到同一h0.5/84×40分析域后的直接实体掩码比较。

### M：HF geometry `a8117291562fc32b9806a26f5bcf97441e06992f44e5e8c634f44c52e67e7fbe`

- model：`lf_data_preparation/native_interface_001/saved_extension_004/run_001/unloaded_alpha_half/model/model.json`
- descriptor：`lf_data_preparation/native_interface_001/saved_extension_004/run_001/unloaded_alpha_half/model/source_geometry/geometry.json`
- arrays：`lf_data_preparation/native_interface_001/saved_extension_004/run_001/unloaded_alpha_half/model/source_geometry/geometry.npz`
- descriptor raw SHA：`574ed624b2df79fc4fce3cca6eaa05218d60edb77674bc48b37cf968a4c7e34b`
- arrays声明SHA：`4c61b434584f7e7f278227c52bc8250a0c555f686cad51ab01900d65b66b93d2`；当前stat 1411 B，未解码。
- solid字段声明SHA：`66a372417082c9df122c673e16a4cdfd143bba68624abed9a251aab908c2ff60`；本阶段未实际重算。

### LF：HF geometry `ddc7a66a3ef45689e9b9a881155d5e5b4f71475615dcb33b5717a4353c60f91a`

- model：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/model/model.json`
- descriptor：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/model/source_geometry/geometry.json`
- arrays：`lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/model/source_geometry/geometry.npz`
- descriptor raw SHA：`7822ba5baf98f03c65cb179d154972182411f9a51d5eae8166355e68c06e4c43`
- arrays声明SHA：`21c37f408ce228e70d93ca0fcdd7cef028ed1ed64082b3cd6096c26f847897bb`；当前stat 1624 B，未解码。
- solid字段声明SHA：`98afa184aeb0da60ab1a73c33c6f0411f6c126c555fae49467f4d528037f51f6`；本阶段未实际重算。

必须由接下来实际兼容检查证明：新最终实体掩码与上述两例均不同，而不只看geometry ID。原declared ID不同和4349实体数只是元数据线索；未变形图、实际数组身份/几何、端口附着、任务合同与兼容结果均尚未由本子任务执行。实际结果产生后再安排计算，本文没有预授新HF平衡路径、参考、压力、有效夹持或正式标签/排名。

实际只读工具证据：ec1f0b（4个fine gripper库存及源文件存在），d9bb64（ZIP前后身份/成员数量/四JSON），17cbca（wave regions），924064（两旧HF输入snapshot）；均exit0。未扫描整盘或平行项目、未修改既存文件。本文和source_selection.json是本子任务仅写出的两份普通准备记录。
