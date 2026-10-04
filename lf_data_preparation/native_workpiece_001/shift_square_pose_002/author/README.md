# 工件右移1 mm：未执行候选

本候选只定义固定下半方体中心(71,40) mm、边长16 mm，保留010的原材料、端口、1 mm网格、背景约束和全部11个1.8 mm加载/卸载目标。实际半方体为[63,79]×[32,40] mm。尚未构造模型、执行力/切线/平衡/HP或测量；静态作者稿不授新工况资格。

## 两个入口与一次资源合同

外部`build_pose_card.py --mode prepare`仅安装本作者资料到正式Git根的新`shift_square_pose_002`控制目录，原F3 launcher字节复制为`launch_pose.py`，并生成`preparation_protocol.json`。它不执行准备。`run_001`须不存在。准备真pass后，`--mode production`才动态绑定新fixture、input_inventory、source_freeze、70胶囊与准备终态，独占生成`production_protocol.json`；它不启动生产。作者文件本身不构成完整独立runtime，仍需完整Git根与依赖。

```powershell
$repoRoot = '实际完整Git根'
$caseRoot = Join-Path $repoRoot 'lf_data_preparation/native_workpiece_001/shift_square_pose_002'
python -B '外部作者目录/build_pose_card.py' --repo $repoRoot --mode prepare
python -B "$caseRoot/launch_pose.py" prepare --protocol "$caseRoot/preparation_protocol.json"
python -B "$caseRoot/author/build_pose_card.py" --repo $repoRoot --mode production
python -B "$caseRoot/launch_pose.py" production --protocol "$caseRoot/production_protocol.json"
```

冻结基线为`38ecc77cc14fee9fd0c69d026ed8df1e32b19bc2`。准备argv明确`--repo .`、control/author/task.json、`--output control/run_001`和三个修正证明角色。独立修正证明读取`lf_data_preparation/native_workpiece_001/t44_direction_scaling_repair_001/{protocol.json,validation_launch.json,result/receipt.json}`；其实际pass只接纳明确的新切线来源。

命令仅供root在独立静审与协议冻结后使用，本候选没有执行它们。准备为一次120 s helper/150 s outer、8 GiB；生产为一次1500/1560 s、8 GiB。STARTED包含第三方导入，helper采样RSS/Windows peak_wset；root须单独冻结argv及全树采样的协同outer包装，原F3 launcher的stop_requested.txt写到控制目录；两入口同时检查run_001与其父控制目录，保留本地stop角色。不是OS硬终止合同，未新增Supervisor。准备/生产各一次，正式首错关闭，无同卡修复重试。后续参考预算、来源、计数合同必须另明确，不能借原300 s或Ref003600 s窗口。

## 保存与身份

准备直接调用一次原`build_native_project`和writer，保存`fixture/model/{model.json,model.npz,source_geometry/...}`，原方向快照、task、70源码胶囊（010原68作为来源上下文，当前切线有下述唯一显式替换+本两包装）、source_freeze/input_inventory及preparation_receipt。来源不是独立搬走flat capsule即可运行；重放仍需完整Git根和Python依赖。前序要求010生产真pass及**实际Ref003** summary/launch真pass并绑定同一旧result，原010失败参考不能冒充前序通过。

当前来源仅允许`split_numpy_tangent.py`从原FE365胶囊过渡至新v5实际SHA。须先核独立修正卡protocol、validation_launch和result/receipt全部实际pass：原focused测试无错误/跳过、2次缓存T与2次fresh HP完成、9603原作用门、全3200单元/6642DOF、full/chunk全三张量字节相同、原F与range guards未改、300/360 s与8 GiB未超。`source_transition`保存旧胶囊SHA、新actualSHA和三份证明的相对路径/SHA；旧68历史胶囊不改，当前其余67项必须原字节。新任务尚需自身完整路径与fresh参考，旧Ref003只说明历史接受态。准备脚本不执行修正卡或借其预算。

位置case实际比较21 intrinsic原字节不变、6字段改变：fixed/free与四个workpiece索引集合；新27字段整体具有独立NPZ/descriptor/task/effective-boundary身份，不再冒称a2d6原模型。cell/node ID平移+1，bodyDOF和背景overlap平移+2；merged固定集合由原API重新去重。实际检查128cells/153nodes/306bodyDOF/17背景uy重叠、376fixed/6266free，方向不碰新fixed DOF；passive_void、机制/端口节点分离等由原构造器检查。初始节点线gap记录实际新值，不沿用旧2/2假设。

生产沿旧010完整观察器薄迁移，显式mechanical+chunk256，原控制器、门、最小增量.00625和原F公式不改，切线使用上述独立修正后的明确新来源。一次native_mean内部构造与solve，writer仅保存本次实际缓存。全部原目标和所有实际接受索引（含重复、可能二分）保留，次数从真实结果读。保存原首次F范围输入16字段、首次T异常输入17字段及同对象25force fields、计时/序号/源绑定；原tuple/bare raise/finally还原不变。每次生产新27与准备fixture全字节比较，再核其对原a2d6的声明差异。

`execution_receipt`新增`model_comparison`、`declared_workpiece_model_arrays_equal`、`declared_workpiece_model_sha256`，替代旧`original_workpiece_model_*`语义。失败路径/接受缓存和真实F/T开始/完成、hooks/capture仍按旧包装保存；不存在成功的补算。原T44/F77失败卡/数据不动；新切线资格限独立修正卡已证的缓存范围，改变位置本身不能称为修复，也不能将新运行冒称为旧来源运行。

## 后续参数case与参考

同包装仅额外接纳未来**另卡**的E=.5 MPa、gamma=alpha=2e-6、相同位置/path参数task；本次task保持E1/原1e-6。未来组合只改变四个material字段lam/mu/gamma/Et，以及6 overlay字段；全局kr和原非实体medium lam/mu字节不变，因为E半与alpha/gamma双抵消。因此此组合软化原实体，并非整体第三介质/正则化同时降低。Et由20变10，原floor公式必须随实际Et推导，原阈值不能改。未来task/模型需新身份和资格，本次不会执行它。

没有复制Ref003特定“恰一T失败/回滚二分”计数合同，不硬填T44/F77/F90或12态。新参考应先核真实完成/缺失事件，再对每个新接受态fresh80/120保原力/PORT-Jv/CSC/KKT/工件门；未知缺失事件不能隐藏。辅助能量保持not_evaluated，压力、夹持、全切线列、失败trial资格仍未授予。方体region接口可据新task中心派生有限面，任何新距离/节点力图都须在实际保存数据产生后另观察。

## Independent resource revision

The closed900s pose001 card is preserved as failed complete-task evidence. This new card repeats all eleven targets from zero once, with explicit settings.time_limit_seconds1500 and helper/outer1500/1560s,8GiB. Task and producer bytes, mechanics, original numerical gates and max bisections remain exact. Old001 contributes cost/rejection provenance only; no accepted prefix or HP qualification is inherited. Historical author diffs and notes retain their original role; current resource_revision_note and resource_delta diffs describe this card.
