# 保存态续算正式集成：控制器兼容性静审

基线main `d45f6ee92d8a0d6ca740772a1762abdc691489fa`。未见阻止源码集成准备的问题。建议一次安装M-RESUME1已审、已实测的7份production源与原新增测试，保持力核、切线、构模、KKT和split运算不变；不另外编写一套续算算法。当前只读源码／普通JSON并比较AST，没有安装、运行测试或新科学计算。

`initial_parameter=0` 时，原load_only／ordered_cycle边界、初始双数组／R／K=None、signed-zero warm lift身份、原Newton校正、origin/loading/unloading角色和默认结果schema保留。新strict-anchor guard仅对非零p0开放。AST证实原 compensated `_dot`／measurement、clock／evaluate／impose／feasible／measure／metrics／step／advance未改；Newton除该一个guard外相同。NativeMean assembler、缓存状态SHA门及复制、workpiece观察和writer也保留，saved索引注释只在anchor分支执行。

mean约束仍由两数组补偿计算，增广矩阵的右上块为−b_in，左下块为+b_inᵀ，普通非对称LU。predictor保持负力与负mean RHS，port_projection只替换位移seed而保留dR；R继续表示actuator_on_model的signed乘子。未接受attempt回滚和此前复制的接受缓存保留；接受后callback／时钟异常仍可能已有有效接受态。

非零锚点仍需ordered_cycle、saved state和首绝对target=p0，初始K=None、fresh F/T原门直接合格；失败在correction／commit前停止。reader继承精确原task／suffix、settings／options（仅clock变化）、模型材料／BC和双位移身份，只检查并复用原两个机械kernel源，不读取原force／tangent／CSC。范围仍限原zero-lift完整ordered父路径中的original目标；不支持从child继续、任意extend、bisection anchor或load-only保存态。

兼容性措辞需精确：新的显式None选项代表默认，缺zero-start settings以invalid_settings拒绝，旧入口的缺参TypeError／无效None处理并非完全原样。安装后新运行的source SHA／descriptor字节必然更新，不能承诺整个result JSON逐字节相同；这不是数值算法回归。历史cards／protocol／baseline／已存results不得改写成新源身份。已核M-REF2的实际11份reference_sources不包含本次7个安装路径，可保留其历史资格与未改参考源；旧production pins仍描述原执行。

后续真正需验证的是安装后的默认import与原分支：非零affine lift／target_origin及signed-zero、mean补偿、非对称KKT／R符号、trial／二分／rollback、complete／mechanical与full／chunk256缓存／partial保存、五项saved public测试，以及若选择的CLI解析。已有测试可复用。M-RESUME1实际五项通过和13440单元首次下降证明的是隔离包，不自动替代安装包回归；第5测试会产生真实16-cell F/T。应在独立明确的测试范围与资源合同下再运行，不为源码安装重跑长加载。

逐项来源SHA、AST等价证据、现有测试名和限制见 [controller_compatibility_review.json](controller_compatibility_review.json)。本报告没有新增预算／验收门，也不证明全列HP、任意输入、压力、有效夹持、稳定性、完整卸载或HF5。
