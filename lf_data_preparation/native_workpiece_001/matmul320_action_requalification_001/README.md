# 保存候选的新补偿切线作用：独立重新验收卡

阶段：`matmul320_action_requalification_001`。用户已授权连续功能开发和循序渐进探索，本卡落实已完成诊断得出的最小消费端修正。原 matmul320 candidate reference 首错已关闭，不重新运行、修改或改名其失败结果。

## 问题与改动

完整保存数组诊断覆盖3200单元×三分量：原Hu action有693个超过原门，精确保存binary64 K×同一v均在原门内；C布局仍507个越门。新增 `hf_repo/src/hf_eval/tangent_action.py::apply_element_tangent_numpy`，用现有CI乘积补偿和固定顺序两词求和，在输出边界只舍入一次。只消费已计算的张量，不改变TMC公式、原CI支持范围、原门限、分母或任何冻结内核。live core暂仍旧版本；被验收的保存F/T来自已冻结matmul320候选，两者来源分别绑定。

## 单次执行与资格边界

只调用新action consumer三次，处理保存的总/材料/Hu K和原dyadic witness。读取原候选一次已完成完整F/T的保存向量、完整CSC和原失败reference在首错前**实际完成**的HP80/HP120全3200单元参考。新增F、T内核、HP力学evaluate、Newton/JIT均为0；历史2次HP不计作本卡新调用。来源字段、数组、实际终止回执、候选全来源、HP文件和新consumer依赖都冻结。不重算模型、修改方向或借用原reference通过资格。

使用同一完整输入F36和声明方向，重新判19200个局部三力/三作用原门、9个全局力/新作用/原保存CSC作用原门，并从保存完整单元张量逐项重构614400个局部存储贡献及三完整CSC。全6642DOF保留。新global action由新local action scatter产生；原失败action永久保留为对照。资格仅属于此保存F36、此候选源码身份、此新consumer及此方向；不授平衡、接触压力、应力HP、全部矩阵列、任意输入或旧七态新源码资格。

原规则：总力1e-11，总action1e-10；材/Hu各1e-9；两HP一致1e-40。局部力尺度max(norm(HP80总力),2e-13 N)，分力max(norm(HP80分力),1e-12总尺度)；action尺度max(norm(HP80 action),1e-10)。全局同原规则。数值精确转Decimal后比较；HP scatter在3000位、Inexact陷阱开启，范数比较120位。新门/旧门名称与是否重用数据明示，原错误不被抹去。

## 资源与停止

独立新窗口：helper120秒、outer150秒、8GiB采样树RSS，包括import、加载、consumer、全部比较、CSC重构与保存。依据上张完整保存数组分析实际4.55秒，给出有界新执行窗口，不继承关闭卡的时间。一次执行，首数值门失败、来源改变、异常或资源失败即停止；保存失败回执，不修复重试、不force。合作检查及采样RSS不是OS硬内存限。

执行前完成新module/wrapper静态独立审查，冻结protocol及全部来源；执行后等待真实exit和资源回执。若通过，先审查实际证据再决定最小生产合入与新的有序0.5mm返回路径，之后根据实际几何和成本进入1mm。未执行的行程不能提前授资格。
