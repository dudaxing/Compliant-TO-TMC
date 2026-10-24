# 最小正式续载接口及验收细则

2026-10-24，仅准备。[精确合同](CONTRACT.json)、[来源](SOURCE_BINDING.json)。保持mean1.06及原导向物理，只新增绝对P2，未知q2由平衡求解。

```python
# 候选调用说明，本准备未执行。
from hf_eval.native_guided_force_resume import extend_native_guided_force
result = extend_native_guided_force(
    saved_force_result="D:/hfh1_001/run_001/force/result.json",
    full_extended_body_load_targets_half_N=[0.0002399800950672949, 0.0002561572865437846, 0.000260201584412907],
    output_directory="D:/hfst1_001/run_001/force",
    time_limit_seconds=1800.0,
)
```

不传q/物理/非clock覆盖，不改58份生产源或依赖，不添加CLI/另一个求解器。output须新建于直接force与fixed父树之外；本机fixed父原位，无需fixed_parent_result覆盖。跨机另显式核同字节恢复范围，不能在本卡静默解包。

## 成功分类

1. 来源/fresh：同一直接父及原fixed/model/geometry、kernel、完整前缀/非clock设置；首态global1/segment0/fresh/checks1，q/P/R bits与原state/两split字段SHA保持。不以小误差替代硬身份，不修复锚点。
2. 数值路径：每态含内部点保原ρF/ρP、mean、正有限J/F/Hu、global和rigid门；末原目标P2/global2精确达到。完整三目标只是谱系，`full_extended_path_executed_by_child=False`；segment_completed/target_reached等依据真实结果，不声称重放旧P0→P1。
3. 普通核对：独立进程只读协议与新result，核继承、global/segment索引、rootP0/segmentP1、原标量门、目标/源身份；不解码state NPZ、不新建参考。正增SP=P不代表可免核rootP0字段。
4. 参考/资格：P2给q/HP参考not_available，相关q/fullDOF/R误差null，不能填0或借旧P1工程界。q2−q1、力/介质变化只描述，不设q必须增加/预期斜率。局部总弱力平衡不授容量/稳定性/压力/纯接触/释放。
5. 显示/清理：数值与普通核对通过才生成5PNG/真实N帧GIF、各新PNG一次检查；四层SUP2原合同与有余量一次封存；数值、显示、清理、封存分别记录。partial/只有fresh不写达到P2。

## 读取和计数

API仅3旧NPZ不同路径（model只opaque hash，geometry四mask，直接HIGH1 state两split）共2解码档6字段；不读fixed012/probe/旧fields/force/tangent/matrix。新保存NPZ raw回读/hash另计，字段解码数与文件open观察分开。

普通核对只协议/新result；viewer四普通JSON：protocol、observer_binding、新result、continuation_check。沿原565body节点/510格、tip11260、右480格ID，先核新result.model相位；不重mask/读取旧媒体或局部字段。×1实际变形、坐标zoom和箭头倍率分开标，不把全域J/Hu曲线说成局部场图。

full3目标，本段2原请求（fresh P1、新P2），global offset1；内部态global原索引2/is_original_target=False。至多5态由原Nmin截止派生，不改maxdepth4或强截。原PROBE q=.0125/invalid_J只历史，不硬配未来N内部态。

原Armijo/有界N二分允许；首个终端错误停止后续科学/核对/显示，保存实际partial。无外部重试、修复重跑、延期、force、q目标回退、新HP/测试、生产修改/安装、API关联、旧包解压/科学复制、删除/回滚或补封窗。资源及共享deadline以候选卡为准。
