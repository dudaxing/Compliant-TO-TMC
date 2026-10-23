# L-CTIPFHIGHPREP1：高输入来源、最小父树与声明身份核查

2026-10-23。独立审阅者 `/root/fload_controller`。本文件在author目录名为SOURCE_PARENT_AUDIT，交付为SOURCE_BINDING；机器记录交付链接：[SOURCE_BINDING.json](SOURCE_BINDING.json)。

**17/17项普通元数据／源码静态核对通过，未见当前_admit要求的来源阻断。** 只允许准备，不代表已执行新力控或已完成科学payload验证。ROOT为 `D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，读查main/HEAD `293c542557c0abe59e1321713e9c3e251eeca465`，当时工作树干净、origin仍为原Compliant-TO-TMC。

## 应当采用的真实来源

- 固定父：`D:/hpr1_001/parent_001/result.json`。完整load_only原13目标为[0,.25,.50,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06] mm；success、target_reached、path_completed及loading_peak_reached均true。
- 选态：accepted12/original12，真实最后原峰1.06 mm，不是旧中间态。state SHA `e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`，signed R=.19522304147728387 N。
- 位移参考：`D:/hpr1_001/run_001/science/result.json`。原请求q=[0,.025] mm，实际接受[0,.0125,.025]；未来比较原q0/终点分别用accepted000/002，不能把内部001误作第二个原请求。

上述result/model/selected/geometry/probe五份普通描述的canonical身份、模型与任务hash、父选态及参考来源关联均已核。公开仓库中原ALPHA父四份普通文件和PROBE1原result，与当前最小树普通文件的原字节身份一致；原PROBE1封存manifest中的对应普通文件声明也一致。

## 八份核心普通文件的实际身份

表内SHA是本准备阶段对**普通文件**实际读取并计算；科学NPZ和ZIP的SHA另列为旧记录声明，不能混为已验证。

|角色／绝对路径|字节|实际SHA256|
|---|---:|---|
|parent `D:/hpr1_001/parent_001/result.json`|289415|9e083bb057de9ea9b2b52694b3cc474a877ecbfcc3785d26fa50f55566e320ec|
|model `D:/hpr1_001/parent_001/model/model.json`|89774|7f56cf78700c85145cce33a5972f73ac48e05923f16c27e69f7f118e6d239e0b|
|selected `D:/hpr1_001/parent_001/accepted/012/state.json`|9579|c06fc6d2e3400832ca967ad5bffd546feb960c818a4e388cda3af9ec5e2a00ae|
|geometry `D:/hpr1_001/parent_001/model/source_geometry/geometry.json`|25085|9630f76972ffecbd60fa42eefb44da0c97c395db7baacaaede33cdabbbc9cf6a|
|probe `D:/hpr1_001/run_001/science/result.json`|5864469|91ab9a1ddf66382963052fbaed4fcfe61670fed4f6611af027b1d61a9466aadc|
|old validation `D:/hpr1_001/run_001/numerical_validation.json`|2391|2f20c26a1ce993da75bc956916561d1979cea7331122d6b8f3323cb1c423417b|
|old copy receipt `D:/hpr1_001/run_001/parent_copy_receipt.json`|3359|76bccc284b274ec1d7e56b0a46dc44f571b6378d99af3d3d95522433acefcf45|
|observer `D:/hpr1_001/observer_definition.json`|89917|c2ed1eb05a4934710f1ecf71dc6eacb80dd52bcfa7c6888eb9aad88258f5b638|

额外普通证据为原protocol、EVIDENCE_MANIFEST及公开原件一致性核对；完整路径/大小/SHA在机器记录中。5.86MB参考result已存在正式PROBE1目录，可关联，不需要在新准备包重复复制。可移植ordinary_source_context只需小型model/geometry/selected等普通描述；这不会变成新的科学运行树。

## 最小父树完整性与科学声明

当前父目录只有accepted/012缓存，没有000–011原科学缓存。它保留完整13态原路径**普通记录**，不代表本机已经恢复完整13态raw数据。当前不变_admit只读parent result→model→source geometry→selected012描述，并对3份NPZ做规定校验/解码；不读取其他12态的descriptor或科学缓存。因此实际所需的7份最小文件目前均在位，其他父缓存缺失不是该入口的静态阻断。

|将来角色／绝对NPZ路径|本次仅stat字节|SHA256仅为描述／历史封存声明|
|---|---:|---|
|model opaque `D:/hpr1_001/parent_001/model/model.npz`|324454|0752153a29e8c8691ad17dd9e0e66c0109e9af2d68e1d208d2a3f66913ad490e|
|geometry masks `D:/hpr1_001/parent_001/model/source_geometry/geometry.npz`|1636|188a0d2271e1ae81e4ed96428f93561cc6021e967bb1aa8f324730c027d08b3c|
|parent012 split `D:/hpr1_001/parent_001/accepted/012/state.npz`|219724|b106fd6f3a2c3d1b3ddab90ec024f437bda5fc343925b77932631d8aa9c04fdc|
|probe000 split `D:/hpr1_001/run_001/science/accepted/000/state.npz`|219724|b106fd6f3a2c3d1b3ddab90ec024f437bda5fc343925b77932631d8aa9c04fdc|
|probe002 split `D:/hpr1_001/run_001/science/accepted/002/state.npz`|219874|fea649e5664633096db0b2d4a1f377ace6a73af517167438abfd9b9c426cd6e2|

五个stat大小均与历史manifest声明一致，描述与manifest SHA声明也一致；**未打开这些文件、未重新hash、未解码字段，当前实际字节身份仍待未来授权worker核实**。父与probe000均声明lift/fluctuation两字段、各29970个float64，字段SHA和state SHA一致，R及check1记录一致。parent的archive路径是accepted/012、probe为accepted/000，路径因迁移不同是预期行为，不要求整个带路径descriptor字典相同。

原 `D:/hpr1_001/execution_evidence.zip` 仅stat为19408041字节；旧manifest声明SHA `53756be194e85ffc1baacf8b8c4bff213fac3a3667e0ac5305585ad144a8b07b`，未重新验证。旧3PNG/GIF也仅stat，没有打开。当前机器可以直接使用原树，下一运行卡不必为本机加入旧ZIP解压/旧科学复制；换机若需恢复，必须另明确其路径、读取和资源，不能把普通context称作完整payload恢复完成。

## 代码身份差异：必须保留，不能误称父四源全同

|源码|固定父声明|当前源码|当前_admit是否要求该SHA相等|
|---|---|---|---|
|native_mean.py|76fd9917…78fd6e4|同|否|
|split_displacement.py|151cc130f0a75e3b2f201b393541107ccf2feaa3de365db72d1987568dae1bb8|65e5cb15a54b53978abb744ee7e99928cadfffefb9afb71fdc6dcfcd139e295e|否|
|split_numpy_tangent.py|547143b1…9857f|同|是|
|split_kernel_invariants_hu.py|d5f7d20a…abd9a|同|是|

当前_admit没有controller版本相等硬门；它严格绑定force/tangent两kernel、原来源、原split/有符号R并要求新鲜平衡。该历史controller差异因此不是现有入口的准入阻断，也不意味着两版本所有行为都已证明相同。原父声明必须保留，不改成新SHA，不把缺失的相等检查伪称已通过。

原成功PROBE1的native_probe、split_displacement、force/tangent四源均与当前一致，且其q0记录已从上述父原split/R成功fresh检查；本准备只核这些普通记录与源码，仍不能跳过新力控P0的fresh F/T、独立g门和位身份核查。57份当前生产源码已只读hash/AST绑定于机器记录，无生产修改。

## 成员、端口、物理与后续输入候选

原模型14720单元、14985节点、29970 DOF，fixed1288/free28682；工件510单元/565节点，zero去重195，body-y/background交叠37，fixed去body-x为723。zero∪body恰为fixed；允许的交叠只在body-y/background，原input/output非零DOF均不含body。新reduced(w,q,R)维数28684，几何网格不改。

完整必需body/zero/fixed/port ID及权值在SOURCE_BINDING.json中；输入5节点[14060,14245,14430,14615,14800]、权[.125,.25,.25,.25,.125]。原observer的tip11260、right480格、81右界节点与父body及source_parent/model SHA一致。这次observer本来就指向1.06父；新binding应继续用本次准确高输入父SHA作为authority，不只凭历史名称认定。

保持mechanical/chunk256、α2.5e−7/γ1e−6、r9/center(80,40)/right92/Lr80、E1/ν.3/plane strain/t20/h.5、原端口/边界。父的历史controller时钟14400秒只是历史来源，不授下一卡资源；其余设置按原记录保留，未来只覆盖新clock并明确新force N步长。父port_projection是父metadata，新力控实际是guided_reduced_tangent，不混称算法。

拟半模型绝对P=[.0002399800950672949,.0002561572865437846] N，已经含厚度；P0与parent旧ON-body Fx反号一致且非零。ΔP=1.6177191476489698e−5 N，Nmin候选ΔP/16=1.011074467280606e−6 N。q完全未知，原q=.025只用于事后交叉；不取0/ΔP代替P0、不重乘t或倍增q。

原probe的第一次0→.025尝试invalid_J、depth0、rollback_bitwise_equal=true；原内部二分随后接受.0125和.025，二者depth1，终点minJ=.0004166085295994876、rho_F=8.840774882078524e−11。全部原失败/二分/3态记录均在机器记录保留，不能为下一卡抹掉困难或把它称作释放/承载极限。

未来最小读取仍可沿已验证结构准备：API 3不同旧NPZ，model只hash、geometry四mask+父两split共6字段；比较另4个state NPZ/8字段（旧probe000/002与新force锚点/终点），合计7不同路径、14字段；旧force/tangent/matrix不读。实际读取须新卡授权并在唯一窗口核实；本阶段仅stat这些声明路径，尚未执行该流程。

## 限制、检查修正与结论口径

本审阅初稿曾把q0整个带路径state字典与parent字典比较，因accepted000/012路径不同而产生一个静态false；随后按真正原合同改为比较archive/field/state SHA声明与binary64 R，并明确保留路径差异。该修正没有读取payload、改数据或放宽科学门，最终17项均通过；定义修正亦在机器记录保留。

仍待未来唯一运行证明的前置包括：3个准入payload SHA/字段真实一致、从mask重构得到的实际模型/材料/成员、q0两split/R真实位身份及fresh F/T原门+g门、正式新路径与工程交叉。旧minJ>0及普通success不能替代这些检查，历史controller差异也不能藉此静默抹平。

本来源审阅子任务实际科学payload字节读取0、hash验证0、字段解码0，ZIP/媒体打开0，HF/科学导入0，新F/T/平衡/测试/绘图0，生产修改0。此计数仅覆盖本来源审阅，不包括主任务另行完成的纯控制示意图。可以据此完成下一卡规格和资源准备，**当前没有新平衡执行授权或结果**。
