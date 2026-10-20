# L-CTIPAREF1：新α峰值保存态独立参考

用户已明确批准开展本卡，无需再次批准。本卡依据已发布ALPHA1 NEXT_STEPS，在原物理条件与15项严格验收门下，仅核对新α=2.5e-7的1.06 mm峰值保存态。

整体目标是普通LF几何进入独立、可恢复的大变形/TMC分析，并使结构变形和工件作用力可审查。ALPHA1真实从零完成13加载目标；新旧α的峰值净工件Fy接近，但material增加、Hu减少且介质minJ下降，存在抵消。先核本态的数值可靠性，再选择后续功能或物理实验；旧α参考不能转授新α。

唯一状态：ALPHA1 accepted12/global12，loading，1.06 mm；SHA `e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`。来源为原完整模型和accepted/012保存缓存，完整14720单元／29970DOF。α2.5e-7、固定圆形工件r9 mm、圆心(80,40) mm、右域界92 mm、Lr80 mm及其余原材料、网格、边界、平均端口、对称和生产设置保持。

复用原11份独立参考依赖，字节不改。新driver只适配从零13态的生产来源，核对实际accepted12，撤去旧双态续算专属假设；原PREP材料比较显式只允许α与派生kr减半，其余材料项精确保持。原误差图副本仅标题与返回接受行两处身份元数据改为accepted12／新α，误差条目、归一化分母、门、log显示和布局不变。旧child命名的兼容字段在本卡明确表示实际接受行12，不伪造续算来源。

HP80／HP120各一次，共2次。原三力、同一固定兼容PORT方向切线、完整CSC系数组装身份及方向作用、KKT、工件与holding投影检查保持。PORT方向不等于全矩阵所有列的HP核验；独立解析能量只归档，不授应力／能量资格。

原15项门保持：production_residual1e-9、independent_residual1e-8、force_evaluation1e-9、average_constraint1e-10、global_force_balance1e-6、fixed_displacement_mm8e-11、hp80_hp1201e-40、total_force1e-11、material_force1e-9、regularization_force1e-9、total_tangent1e-10、material_tangent1e-9、regularization_tangent1e-9、augmented_force_tangent1e-10、augmented_constraint_tangent1e-10。原算法、分母、容差不修改。

先做薄包装与有限独立源码静审，再唯一启动。helper900秒／outer960秒，采样8GiB，OMP／OPENBLAS／MKL／NUMEXPR线程上限16，配置不等于实测16核。沿原参考launcher的采样与合作停止，不增SUP2或硬抢占清理资格。六份既存科学输入只在唯一helper窗口读取／哈希／解码：model、012 state/forces/tangents/total_matrix，以及source_geometry原身份；预备只读普通JSON并继承ALPHA1 producer seal及stat。

原门全部通过后，一次读取新普通参考摘要生成1误差PNG／JSON，新PNG最多一次原分辨率像素检查。原六图与13帧GIF只链接，不重开／哈希／解码／重绘。零、小值保留，不加显示地板或新门。

首个终端错误停止后续参考／绘图，保真实partial，原窗口内封存实际产物。无外部重试、修复重跑、延期、force、新生产F/T、平衡求解、测试、默认HF修改、API关联、安装、删除或回滚。完成后只读普通记录并继承seal/stat，不闭窗重开科研gzip或数组。记录目标、动机、来源、误差、真实调用／资源、QA和后续判断，普通main推送与远程main核验，同机异目录local Git objects fetch／ff-only恢复核对。

通过只覆盖此新α保存态及声明方向，不授全部13态、卸载／完整循环、α收敛、局部压力、有效夹持、自由释放、稳定性、网格／域宽或HF5资格。原ALPHA1生产结果与旧α结果／参考范围保持。新物理或计算范围根据本次实际结果另行安排。
