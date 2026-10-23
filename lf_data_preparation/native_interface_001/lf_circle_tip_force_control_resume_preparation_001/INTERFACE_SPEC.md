# 最小接口与状态继承合同（候选，未实现）

## 显式新入口

```python
# 未来候选签名；当前安装版本不存在，不能执行本段。
from hf_eval.native_guided_force_resume import extend_native_guided_force
child = extend_native_guided_force(
    saved_force_result, full_extended_body_load_targets_half_N, output_directory,
    fixed_parent_result=None, time_limit_seconds=60., on_accept=None,
)
```

`saved_force_result`是成功force结果；只选其最后接受态且必须是完整原目标末点，不提供任意selected index。载荷列表为完整延伸任务：原full P列表精确前缀＋至少一个严格增加的绝对有符号half-N。实际仅计算`[P_parent_last]+新增后缀`，首点fresh复核。无q、R、force_settings或物理覆盖参数；除新clock外，原settings/force_settings、response/tangent、guided predictor全部继承。q可正可负，P可正可负；不能把“严格递增”解释为增大abs(P)。

输出必须是直接force父树和实际解析的root固定父树之外的全新目录。默认`evaluate_native_guided_force`签名及fixed父/q0准入保持；不添加CLI、通用fallback或任意任务迁移框架。

## 最小源码范围

|文件|必要变化|
|---|---|
|[split_guided_force.py](../../../hf_repo/src/hf_eval/split_guided_force.py#L101)|增可选`initial_body_q_mm=0.`与独立`force_scale_anchor_half_N=None`；默认仍原零lift/q0；续载保绝对q和root尺度，原非对称KKT/Armijo/N二分及原门不改。|
|[native_guided_force.py](../../../hf_repo/src/hf_eval/native_guided_force.py#L54)|提取一次私有执行/缓存保存runner，原入口仍走原_admit；新入口复用同一力、缓存、ledger、capture及保存代码，避免第二套求解/组装。|
|新增`hf_repo/src/hf_eval/native_guided_force_resume.py`|显式force父准入、完整任务前缀/来源绑定、唯一选末态、继承与新结果谱系。|

另新增一份有限测试，作为研究证据交付；不安装到生产src。原57源中其余55份保持同字节，完成后生产共58份。原kernel/tangent/默认fixed/probe/native_resume/__init__/response/CLI不改。若实现发现必须超此范围，应在启动测试前说明并修订候选，不默加修改。

## 可接受来源与准入

只支持已知`hf-native-guided-force-1.0`原任务或本次拟新增`hf-native-guided-force-1.1`延伸任务。必须status=success、target_reached=true、failure=null；末态是原请求最终载荷，原目标覆盖当前段，完整任务严格递增，schema/状态/索引一致。partial/probe/fixed结果不是本入口合法force父。

原1.0 source有固定父/模型/geometry绑定；从root固定模型的普通描述和四geometry mask重建project，核网格/材料/区域/端口/支撑/工件节点及source身份。不可直接调用旧native_probe._admit：它会拒非零lift并多解无用的fixed q0 state。新准入只解直接force父末态lift/fluctuation两字段，不读fields/旧力/切线/矩阵或fixed q0 split。

先核普通JSON原字节与canonical身份/已知schema及任务，再核opaque model身份、geometry四mask与selected state archive/字段SHA、dtype、shape、state hash。保原producer源码身份声明；API/controller授权演进不要求六文件全部与旧producer相等，但两force/tangent kernel SHA必须与当前相同，不能重写旧pin。新模块进入新结果producer清单。普通source错误在F/T前typed拒绝；本准备只完成静态合同，没有完成这些未来payload/fresh门。

1.1 child保浅层root固定来源、root force结果历史pin及直接force父pin/selected元数据，不把整个父result或历史嵌套复制。再次延伸只读直接父及root固定result/model/geometry，按直接父完整目标首点保持rootP0、前缀/索引/原设置；不递归读祖先force结果或NPZ。root force pin是保留谱系，不宣称本次独立重核了每个祖先的全部数值路径；普通canonical/SHA是身份绑定，不是真实性签名，不能检测全部可信pin被一起伪造重写。

唯一来源定位参数`fixed_parent_result=None`默认用父声明的root固定result路径；换目录时可显式指定该文件的新位置，但raw SHA/canonical必须与保留的root固定pin相同。model/geometry只从该固定result的相对声明派生，并核原pin；不能借此换模型/物理。新结果分别记录历史声明和实际解析位置，原source字节不改。它不允许指定q/R/settings或替换selected split；后者从直接force结果的相对路径读取。小模型child采用一次显式同字节固定树迁移，grandchild再按其记录默认解析，以验证换目录路径而不另加真实路径。

## 位移、预载与fresh检查

原物理位移`u=lift+w`，工件lift_x=q_absolute，其他lift=0，w[原fixed]=0；x_body=X_body+q。准入保selected两split原字节，finite q/R/P及元数据一致，精确工件lift与q声明，原body/zero结构不变。fresh不重建、不重排、不投影，保持state hash及q/R/P的float64字节，Newton checks=1，无predictor或修正线性解；失败即`initial_state_not_equilibrated`，不强行修复成新起点。

新步仍求`(w_free,q_absolute,R)`。impose覆盖body-x的lift，不累加；R沿原符号，mean约束相同。segment_anchor_P是直接父终点，scale_anchor_P永远最初force根P0；即使负P逐步靠零也保`SP=max(abs(P),abs(root_P0),Ffloor)`。mm minimum_increment与half-N minimum_force_increment分别继承，原N二分/rollback/时间门保持。

## 新结果语义

新结果用1.1，原根结果不改。`force_task.body_load_targets_half_N`保存完整延伸目标；`anchor_target_half_N`保持根P0语义，新增`force_scale_anchor_half_N`=rootP0、`segment_anchor_half_N`=直接父P末值。`continuation`保存直接父result pin、末态P/q/R/state/archive pin、完整源目标、新完整目标、段目标、global offset、root普通身份、fresh检查与身份结果。

1.1再次准入必须明确核`full_targets[0] == anchor_target_half_N == force_scale_anchor_half_N == root_P0`，末原态P等于full_targets[-1]，段锚点/段目标覆盖/global index相互一致。1.0没有这些新增字段时，从其完整force目标首点按已知旧schema提取rootP0，不能用当前段首点猜测。

`accepted_steps`只含本段fresh锚点和实际新增态，包括内部二分；`original_target_index`映射完整任务global index，另保segment_original_target_index。`load_increment_from_anchor_half_N`明示指本段锚点，另报`load_increment_from_root_half_N`；q从不减q_anchor。path_summary只描述实际本段，明确`full_extended_path_executed_by_child=false`，不能把带谱系的任务前缀说成本次重算。

数值success仅为本段原门通过；独立参考、整路径HP、压力、有效夹持、释放/HF资格均不因续载升级。所有F/T尝试与完成计数、内部失败/二分/回滚、actual accepted/新保存缓存及ordinary摘要如实保留；save-time F/T=0。新段K从fresh F/T取得，不载旧矩阵或旧force字段。

## 有限错误合同

|触发|结果|
|---|---|
|schema/源身份/非success/非末原目标/坏split或q声明|`invalid_saved_state`，F/T前拒绝|
|缺新目标、改原前缀、重复/下降/非有限或非实数载荷|`invalid_task_extension`（新入口），F/T前拒绝|
|clock/callback/output参数错误|沿用`invalid_settings`/`invalid_input`|
|低层initial_body_q非有限/非实数；q与原lift结构不符|分别`invalid_input`、`constraint_conflict`，F/T前拒绝；新公共入口把坏保存态声明归`invalid_saved_state`|
|fresh原态不平衡|失败partial，`initial_state_not_equilibrated`，无修复|
|后续真实数值/时间/保存错误|原typed failure与实际partial；不转成success，不补零、不重跑|

准备没有改任何现有错误码；以上新增入口码约定待候选静审与有限验证确认，不在旧默认入口改错误语义。
