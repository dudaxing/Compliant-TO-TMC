# 力控保存态续载接口

**已安装并通过本卡小模型验证；本页示例是调用说明，不表示已执行正式r9续载。**

```python
from hf_eval.native_guided_force_resume import extend_native_guided_force

result = extend_native_guided_force(
    saved_force_result,                     # 成功的力控 result.json
    full_extended_body_load_targets_half_N,  # 完整旧前缀 + 新绝对P，不是ΔP
    output_directory,                       # 全新、在两个父树之外
    time_limit_seconds=controller_seconds,
)
```

这里只新增直接Python入口，没有额外CLI或隐式改写默认固定工件入口。现有环境需将`hf_repo/src`加入Python搜索路径，依赖沿仓库既有环境。

## 输入和物理口径

机构平均输入保持父任务值；工件仍为原导向刚体，只有原x平移q未知，其他刚体限制不变。q是相对于原未变形位置的绝对mm，不是从当前末态重新归零的增量；R是原机构输入端有符号反力。P为原+x方向定义的有符号半模型轴向外载N，已包含模型厚度；完整镜像装配对应2P，位移q不加倍。输入R与工件P属于不同广义自由度，不能相互替代，也不能将节点弱力称压力。

`full_extended_body_load_targets_half_N`必须为至少两个有限实数的list，严格递增且逐项精确保留旧完整前缀。比如旧`[P0,P1]`延伸至`[P0,P1,P2]`，只计算`[P1,P2]`；下次输入完整`[P0,P1,P2,P3]`，只计算`[P2,P3]`。负P也按有符号大小递增。本入口当前不支持力值下降/反向回程、修改旧目标或同时覆盖物理、非clock数值设置。

父态必须是已完成所有原目标的`success`力控结果（1.0或已验证续段1.1），并选择其最后原目标接受态。probe、failed/partial、内部二分非末原目标、未知schema不作为续载源。原几何/模型/力核/切线及split身份必须匹配；producer历史不伪装成新producer，也不要求过去所有控制器字节与当前完全相同。

## 继承与结果

读取直接父的两字段`lift/fluctuation`，保原q、P、R及state identity；fresh只允许一次原门检查通过，不做锚点修正。后续自动继承材料、厚度、边界、掩码、平均输入、原非clock`DisplacementSettings`、`GuidedForceSettings`和原Nmin。尺度保持root P0；段首P1只用于段增量，不替代原根尺度。

返回原运行逻辑的普通结果dict并写新`result.json`、新段接受态split/fields等。续段schema为`hf-native-guided-force-1.1`；`continuation`显式包含source/full/segment目标、global offset、root/段P anchor、源state身份及浅层来源。`full_extended_path_executed_by_child=False`表示本次只执行新增段，不把祖先重放或重新授予资格。

原内部Armijo、二分、typed失败/部分态保存保持；异常或partial后按照各执行卡停止。本入口不是从失败态自动修复或重试的入口。`on_accept`可选且必须callable；只有clock允许新正有限实数。原数值门及输入端R和工件合力门保持。

## 同字节固定树迁移

```python
result = extend_native_guided_force(
    saved_force_result, full_extended_body_load_targets_half_N,
    output_directory,
    fixed_parent_result=relocated_fixed_result,
    time_limit_seconds=controller_seconds,
)
```

`fixed_parent_result`仅用于同字节原固定父树换目录，不能借此换模型。需要原固定result/model/geometry和选定直接力控state；原固定model与geometry按原相对链解析。支持已记录迁移位置的子段继续续载，历史路径另保留。output须全新且位于直接力控树、解析后的固定父树之外。

异机时不要编辑已绑定的JSON以更换盘符，也不要逐个改写descriptor/SHA；先按[恢复说明](RECOVERY.md)恢复原字节树，显式传同字节固定父位置，再在新执行卡下求解。根力控祖先pin为历史记录，不递归解码祖先数组或宣称重核旧路径。

## 已验证例与错误

本轮实际小模型从prefix的q≈.000125 mm/P1出发到P2，再从child的q≈.00025 mm/P2到P3；结果及原值见[RESULTS](RESULTS.md)。相同P的分段/直算6对三误差全0，给q参考10对最大位移差3.99e−13 mm；这不是正式r9或HP结果。

新源准入问题返回`invalid_saved_state`；改前缀/空追加/非递增等为`invalid_task_extension`；clock为`invalid_settings`；既有/嵌套output及非callable callback为`invalid_input`。保留原数值失败类型和已通过的真实部分态，不自动回滚已安装源码或重启求解。
