# LF(10) 来源、数据与接口审计

日期：2026-09-20。性质：本轮实际只读审计记录。本文中的“通过”只对应明确列出的读取、哈希、数组与代数检查，不代表重新执行 LF 优化、LF 有限元或 HF 接触求解。本文最后记录与 N(19) 和参考会话的关系；它们的历史授权、测试结果和关闭状态均是来源材料，不是本仓库新的执行指令或验收结果。

## 1. 输入身份与审计方法

| 输入 | 可追溯身份 |
|---|---|
| 新 LF 快照 | `C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (10).zip`，81,618,414 bytes |
| 新 LF ZIP SHA-256 | `79c44fbf2570651539137d74299714823c8046d13efd9c3bad6eb32bc389745e` |
| 新 LF ZIP comment 所记提交 | `a726cfa832de81ec2c9a3a73c55431edb472f529`；这是归档元数据，不等同于本次联网验证 Git 提交 |
| 旧 LF 快照 | `../reference_inputs/lf_snapshot.zip`，24,790,441 bytes；本仓库冻结几何包的来源 |
| 旧 LF ZIP SHA-256 | `c37da0d7c631c84f3cd353997d7539fa60275607183a45b7c91f574091d5d4b0` |
| 当前冻结几何包 | `../geometry_dataset/`，`dataset_id=hf1_lf_snapshot_native_pair_v1`，395文件（包含清单自身） |
| N(19) 快照 | `C:/Users/Lenovo/Downloads/Compliant-Nonlinear-TMC-A-main (19).zip`，29,895,080 bytes，SHA-256 `5de1f65aadeb88320adf0d844680459f52c381c830bae021fba7bd1c4a2c91bf` |
| N(19) ZIP comment 所记提交 | `49528eca1f4a8445ff33a8a12513bce603d18b5e` |
| 参考会话本地副本 | `referenced_conversation.json`，SHA-256 `d9c96090529d173d6f9faa2b323c240230a78c985b94edde7a56fa3abb900307` |

输入总清单见 [input_inventory.json](input_inventory.json)。该清单的 LF ZIP `members=6827` 包含目录成员；本次比较的 **4666** 是排除目录后的普通文件数，两者口径不同。

方法：直接使用标准库 `zipfile/json/hashlib` 读取归档成员；使用本机 NumPy 2.4.6 以 `allow_pickle=False` 读取 NPZ；使用 `scipy.ndimage.label` 对二值实体掩膜分别做4邻接与8邻接标记。未导入 `dmftd`，未运行快照脚本，未按快照中的命令访问外置科学归档。数值引用与来源自报结果均与本次实际复算分列。此前读检不写任何旧文件；本文及接入决策文档是本子任务新增的唯一两个文件。

下文 `LF:` 路径均相对于 ZIP 根 `Diversity-TO-Compliant-O-main/`；`N:` 路径均相对于 N19 ZIP 根 `Compliant-Nonlinear-TMC-A-main/`，本轮只读提取副本位于 `sources/N19/`。

## 2. 相对旧快照的实际文件变化

按去掉 ZIP 顶层目录后的相对路径逐成员比较字节：旧包534文件，新包4666文件；新增4132、删除0、修改2。仅旧 `README.md`、`research/README.md` 改变，其余532个旧文件逐字节相同，包括旧数据、内核、合同和既存脚本。因此新研究是追加资产，不是旧几何或旧 LF 内核的替换。

| 新增组 | 文件数 | 内容 |
|---|---:|---|
| `LF:research/hf_export_v1/` | 61 | 30例的 JSON/NPZ 与索引 |
| `LF:research/hf_export_v2/` | 61 | 同30例按明确区间和支承政策重导出 |
| `LF:research/n4_pilot_gripper_v1/` | 388 | 54次候选准备试点及普通数据包 |
| `LF:research/n4_formal_gripper_v1/` | 3608 | 1800次正式 LF 生成的索引、协议、普通数据包、C1与外置归档索引 |
| `LF:errata/E006_hf_export_region_semantics_v1/` | 2 | E006报告与v2导出补记 |
| 新注册表 | 2 | `contracts/contract_registry_v14.yaml`、`contract_registry_v15.yaml` |
| 新脚本与测试 | 10 | 6个脚本、4个测试文件；仅作为来源阅读，未执行 |

该比较基准是旧 LF(6)。参考会话所述“LF(10)相对LF(9)只改一份README”使用另一组基准，与本表没有矛盾。本次未单独取得LF(9)并重做该邻接版本比较。

## 3. 两例冻结几何与新增导出的关系

比较对象：

- `inverter__sweep__kin_1e+01__kout_1e-01`
- `gripper__sweep__kin_1e+01__kout_1e+00`

分别读取 `LF:research/hf_export_v2/<id>/design.npz` 与 `../geometry_dataset/canonical/<case>/geometry.npz`，逐元素比较：

| 新导出字段 | 冻结字段 | 反向器变化格数 | 夹持器变化格数 |
|---|---|---:|---:|
| `solid` | `solid` | 0 | 0 |
| `design_domain` | `design` | 0 | 0 |
| `passive_solid` | `passive_solid` | 0 | 0 |
| `passive_void` | `passive_void` | 0 | 0 |

新字段为bool，冻结字段为uint8。两例均保留原生40行×80列、1×1mm单元、80×40mm下半域、20mm厚度、数组第0行位于物理底边、原点(0,0)、x向右/y向上。夹持器输入段x=0、y∈[38,40]、方向+x；输出段x=80、y∈[28,30]、方向+y。反向器输出段x=80、y∈[38,40]、方向−x。原生端口梯形平均权重均为0.25/0.5/0.25。

冻结HF `geometry_id` 为：反向器 `2e2bb3466ade06f920dfbb92577ccbe46106acec430837bac8e1a30b8083527a`；夹持器 `d4e82cfd629e37f7d0c85aed672ab5df228314147cf5db59aeabb279cee5d91d`。新导出自己的几何ID规则使用v1格式头及内容哈希，与HF规则不同；跨模式身份应由数组、物理描述与映射记录建立，不能把ID字符串不同解释为几何改变。30个LF v1/v2包之间使用同一规则，逐例ID相等已检查。

冻结数据包现存395文件；其 `file_manifest.json` 所列394文件SHA-256全部一致，清单自身不被自身覆盖。本检查没有改写清单，也没有对清单自身声称新的外部历史哈希认证。

旧两例二值设计域占比为0.3525和0.3533783783783784，仍高于新正式池的0.35资格阈值。旧角色为接口/求解诊断，资格pending；新导出成功不能将其自动升级为新协议下严格合格。

## 4. E006：背景对称段与支承附着政策

主要证据：

- `LF:errata/E006_hf_export_region_semantics_v1/report_v1.md`
- `LF:errata/E006_hf_export_region_semantics_v1/addendum_v2_export_v1.md`
- `LF:contracts/contract_registry_v15.yaml` 的 `hf_export_region_semantics_E006`
- `LF:research/hf_export_v2/<id>/design.json` 的 `regions_mm`

v1从原生节点集合反推闭线段：80×40夹持器背景段写为[61,80]，160×80写为[60.5,80]。物理含义实际为实体对称段[0,60]之后的 **(60,80]**。消费者若把原生闭线段原样应用于更细网格，会漏掉60与原生首背景节点之间的节点。

v2新增 `kind=complement_on_line`、`start_exclusive_mm=60`、`end_inclusive_mm=80`、`interval=open_closed`；`first_native_node_mm`只说明来源网格，不能作为消费者网格的物理起点。消费者应在自身网格上得到60+h、…、80，x=60只属于前段。实体对称段与背景补集覆盖整条对称线；用于分侧反力的标签不得重复累计同一DOF。

支承 `x=0,y∈[0,8]` 明确 `attachment=solid_incident`。只固定实体附着节点与固定全段介质节点是不同任务；端口和线段都显式标明区间开闭。LF参考中的 `symmetry_solid` 是对称线段名，不意味着TMC中只约束该段实体附着节点；若使用完整半模型对称，该段介质节点也在对称线上。

对当前O线的影响：`../hf_repo/src/hf_eval/project.py` 第128行要求支承为 `solid_incident_nodes_only`，第142–146行要求完整y=40背景线；第196–211行记录实体与背景节点选择，固定DOF集合合并。`../docs/HF3_REPORT.md` 第31行也明示该政策。现有O线从独立冻结任务生成完整背景条件，并未消费v1的[61,80]闭线段，所以E006本身不证明现有O线漏约束或旧验收失效。它为将来新导出读取、细网格派生和分侧测力提供必要接口约束。

快照中的D1/D2已执行、D3转达仍待办，是LF来源的历史登记。本轮已阅读并记录语义，不代表其他仓库的历史登记被自动修改。

## 5. 新LF试点与正式池的有效研究结论

`LF:research/n4_pilot_gripper_v1/index.json`、`README.md`、`summary.md` 记录54次160×80夹持器试点：k_hat_in∈{0.1,1,10}、k_hat_out∈{1,sqrt(10),10}，2种子、3名义体积、每次200更新。各体积水平运行成功18/18；二值严格资格分别为0.350→0/18、0.345→16/18、0.340→18/18。基准0.350全部因二值体积超0.35失格，所以“两个严格合格结构之间的保留比”未定义；有效LF分数之间的配对响应比可以另行报告，不能替代前者。

预先单项余量规则选0.345；正式协议结合池大小信号，在新HF标签出现前另选0.340。这是来源协议的决策记录，不能改写试点原规则结论。正式生成见 `LF:research/n4_formal_gripper_v1/{README.md,index.json,run_list.json,protocol_freeze.json,N4_P3_protocol_v1.md}`。

正式批：200池×9格=1800次、160×80、体积上限0.340、p=3、beta=4、eta=0.5、滤波3mm、200次MMA更新，种子20260920+i；每池九格共享该池同一噪声初始场。生成提交 `0e917ad62318ce4beb5272cadb51f42dbacbdeda`。全部记录为 `max_iterations`，只证明预算终态，不声称收敛。严格资格包括二值设计域体积≤0.35、4/8邻接承载路径、无仅角点铰接、支座受约束、端口附着；一单元细颈和支承附着长度是标签。

来源记录给出每池唯一P=9，C(eta=0.5)为7（195池）或8（5池），无完全重复、无细颈标签。全部新数据明确 `no_hf_evaluation=true`；没有本仓库HF4/HF5结果。壁钟46,835.622636s、18 workers、各作业经过时间之和831,658.486266s（约231h）是来源成本记录；含并行争用，不能称CPU时间或移植后的性能保证。

支承附着长度的行记录分布为0.5mm×600、1.5mm×599、2mm×601。这为后续支承政策、网格和接触敏感性分层提供标签；“无细颈”不能推出附着长度足够宽。正式池仅覆盖这一夹持器生成政策，不能自动代表反向器、其他体积分数或一般拓扑家族。

## 6. C1评分口径偏差及恢复层

证据为 `LF:research/n4_formal_gripper_v1/score_erratum_c1.json` 与同目录README的C1节。正式协议要求钉定评分输入弹簧1.4604287860303493N/mm；实际包的 `lf_reference.ersatz_floor_free.native.comparison_profile.k_in_N_per_mm` 为160×80自身参考值1.4339777207450293N/mm。旧导出器未接收评分reference/profile导致偏差。优化生成弹簧、几何与资格没有由C1重写。

恢复关系是在单位输入力、原生去地板线性端口模型中应用秩一输入弹簧恒等式：

`L(k) = q_out(k_in=0) / (1 + k * C_in(k_in=0))`。

它恢复指定线性评分profile，不是非线性接触力修正。恢复/实际分数范围0.9822263980073297–0.9844911487667298。来源报告的实际分数恒等式重建最大相对误差1.506e-12、12个直接线性测量抽检最大相对差6.192e-13属于来源计算，本轮未执行其有限元复核。本轮用全部1800包的k_in_zero原量重算恢复公式，与C1逐行恢复值的最大绝对差为0。

C1明确写于另一线HF标签解盲之后。原包、原index、原运行清单不变；原实际分数、恢复分数及各自顺序必须并存。恢复值可作为正确口径的主要展示，但不得把恢复顺序说成“任何HF标签之前已冻结”。

全部1800正式包标记exporter revision2.1；新快照脚本 `LF:scripts/export_hf_designs_v2.py` 的当前revision2.2显式接收/核对评分profile。该脚本SHA-256为 `c8de0d605bf5e5eccf9f064f39747615c73f7d86d5713d28e42fb9103dc8faab`。根README仍指v14、v15内“当前导出器”仍列2.1，属于文字登记滞后；不据此覆盖真实包和C1身份，也不执行新版脚本以重写历史包。

## 7. 实际完成的全量/抽样读取校验

| 检查 | 范围 | 本次结果与边界 |
|---|---|---|
| 归档新旧字节比较 | 534旧文件及4666新文件目录映射 | 532旧文件一致、2个MD修改、4132新增、0删除 |
| 冻结数据包清单 | 394被列文件；另存在清单自身 | 被列文件哈希全部一致；现存395文件 |
| 两例新旧几何 | 每例4类原生数组 | 每类0变化格；bool对uint8 |
| handoff导出文件绑定 | v1和v2各30包，JSON/NPZ | 与各自index记录的文件SHA-256全部一致 |
| LF v1/v2几何身份 | 30例 | 同规则geometry_id全部相等 |
| 正式包hash及行引用 | 1800个JSON、1800个NPZ、index与C1 | 文件哈希、内部数组包hash、geometry_id绑定全部一致 |
| 正式权威掩膜身份 | 全部1800个solid数组 | raw bool字节SHA-256与行级clean_sha256相同；1800个不同掩膜 |
| 原生数组读取与分区 | 全部1800包 | shape=(80,160)，无object数组；三分掩膜覆盖/互斥，实体不占被动空区、包含被动实体 |
| 二值体积复算 | 全部1800包，以solid∩design_domain计数 | 与行记录一致；范围0.34180743243243245–0.34679054054054054；全部整数比较通过0.35 |
| 全实体连通分量复算 | 全部1800包；4邻接和8邻接分别标记 | 两种邻接每例均恰好1个实体分量；未据此替代支承刚性/非线性稳定性验证 |
| C1公式复算 | 全部1800包 | 恢复分数最大绝对差0；C1所绑定index hash一致 |
| 冻结协议/清单 | protocol文本统一LF换行；run_list原始字节 | 与protocol_freeze记录一致；未执行运行器或重跑数值规格 |

未独立重算项目内核给出的LF严格实体有限元参考、ersatz参考、优化历史或反力；未逐一复核所有54个试点包的内部文件hash、全部资格判据和几何端口附着；未重新执行1800例完整资格函数。1800例几何连通性、体积和数组身份是独立复算，其余完整资格状态仍是来源声明。不得把表中通过范围扩张为整个研究流水线重新验收。

主要成员hash：

| LF成员 | SHA-256 |
|---|---|
| `research/hf_export_v1/index.json` | `9faf04c40fddc3d6ea653f80a811eb008a40eb4c2e532c4be17bef441004a094` |
| `research/hf_export_v2/index.json` | `c7c64f3e982c7bdedf6f67f03a364c91c1835de4d5f1789b06a8c096af3d1ad0` |
| `research/n4_pilot_gripper_v1/index.json` | `fe933e76fb9fa74de3f3518803d99f9470d5094400df1597e1e108a7664bf014` |
| `research/n4_formal_gripper_v1/index.json` | `5e0cc609f43fff082629cef57be7efde4cfe14b6696b41e813817b10fd5aa954` |
| `research/n4_formal_gripper_v1/score_erratum_c1.json` | `3c5d1ddcfd891377d431caa600a20841356962e132f95a99f931223b61c65ac9` |
| `research/n4_formal_gripper_v1/archive_manifest.json` | `314bd417deaf44a13e29f3f149c5c0fbc10a08431f4b2a0d38ef0413e776398f` |
| `research/n4_formal_gripper_v1/run_list.json` | `c5685f827a10925713da927d66aff8fb7c8a8aedde9f0c931188379a499c3f30` |
| `research/n4_formal_gripper_v1/N4_P3_protocol_v1.md`（LF换行规范化） | `7150dc09c6a49df0a8b654be271b67b56f7c9e3dea858bff29635ffac21e9648` |

## 8. 原始记录的保存边界

正式批 `archive_manifest.json` 记录12600文件、1,880,882,259 bytes，即每次运行的 `arrays.npz/history.json/summary.json/geometry.npz/row.json/spec.json/attempts.jsonl` 七类文件。记录的身份是相对归档路径+哈希。来源README自报两份副本核验和40例恢复测试；这些外置文件不包含在本次LF ZIP里，本次未访问或认证外置副本。

ZIP中1800份JSON/NPZ导出包足以作为权威最终几何的普通资产，配套index与C1足以读取评分记录；它们不能单独证明每一步优化轨迹和全部计算成本来源。包内绝对机器路径、旧命令和授权描述一律只作来源文本，不成为运行路径。

## 9. 与N(19)、参考会话的差异及本线使用边界

参考会话本地副本包含4个turn；最近turn为 `e3657674-eb02-414a-8ef2-d58c1f389add`，会话ID `6aaf4b17-7044-83e9-ac6e-7954cfdae948`，标题“TMC开发”。本次阅读其最近评审内容，并静态阅读N19的 `docs/N3b_record.md`、`docs/N3c_record.md`、`docs/N4_P4a_diagnosis_and_pilot_proposal.md`、`research/n3b_contact_v1/rules.md` 和README。未重跑该会话声称的16项测试、P4a离线回放、统计复算或任何N线HF标签。

N19固定工件A是实体、有限底面、无摩擦主动集模型；输入端口节点逐点规定ux=d，工件为x∈[70,80]、y∈[32,40]的刚性矩形，名义任务5mm。LF端口参考是分布力/平均位移及弹簧模型，O线HF3是平均输入位移控制、自由输出，O线HF4-B是指定均匀法向TMC任务。这些任务不能因几何相同而混为同一物理测量。

N19来源记录中最可复用的失败经验：有限平面节点越界后仍被约束会虚增接触力；越界释放后重入且穿透的非主动节点也必须拒收；全部积分点J>0不阻止实体与工件整体重叠；有效前缀必须检查所有接受态，包括插入态，不能只查看共同检查点。来源证据位置分别为 `N:docs/N3b_record.md` 的修订节和 `N:docs/N3c_record.md` 的前缀修订节。本次吸收其诊断需求，不继承其测试通过、容差例外或一般接触精度结论。

最近参考会话对N19/P4a的科学解释提出限定：种子主效应小不能推出池之间不独立；P4a是解盲后复用数据的探索，不是新确认实验；LF双端口模型对自身线性模型的精确关系，不代表实际逐点位移/夹爪面接触A的精确表达。恢复版顺序是在C1解盲后产生，不能追溯成为原盲态顺序。反力上限停机读出不同于真实力控制，粗路径插值和检查点单调也不提供区间内严格物理误差界；“所有下界/所有上界都命中”不足以证明任意合法区间组合都命中。这些属于研究解释和后续协议的约束，不要求本线立即重跑P3统计。

本线当前取舍与近期执行顺序见 [INTEGRATION_DECISIONS.md](INTEGRATION_DECISIONS.md)：保留O0.5.0稳定内核、split状态和严格门槛，先增加独立几何交面积与严格有效前缀诊断，再在小尺度宽平面、预先闭合接触分支上验证受限A0参照。HF5统计暂缓；新LF候选池是后续资产，不是越过接触验证的理由。
