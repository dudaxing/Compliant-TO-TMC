# 已有弱式工件力、连续压力与最近功能缺口

只读审阅完成；基线 `c4d81620fe7d1a9260cf0f7d27ab35970d463e46`。本轮读取相关MD／PY／普通JSON及其SHA，未读取NPZ／NPY、科学gzip、CSV或媒体原字节，未导入HF／API、运行测试／力学／绘图或修改正式仓库。以下为源码与已有结果的取舍，不是新执行卡、数值通过或稳定性资格。

## 已经实现，哪些解释已补齐

固定体total／material／Hu弱式合力、保持反力、镜像上半作用、完整净力和两侧法向幅值和已实现（`native_mean.py:67–108`、`native_response.py:50–67`）。原alpha=1e−6的24态／48HP与新alpha=5e−7的两个child态／4HP均有各自力／原PORT／组装／工件投影参考。无需重复载荷API、账本、三分量箭头GIF或同类HP。连续压力不是报告这些固定体弱式作用的前置。

四层已有诊断回答了不同问题：

| 已有阶段 | 实际作用 | 不能据此宣称 |
|---|---|---|
| M-PTRACE1／saved_material_trace.py:20–30,84–110 | 外邻owner的材料Piola参考迹P·N；原厚度一次、符号和端点不平均 | 包含Hu的总压力、当前面积压力或线迹等于body弱力 |
| M-SUPPORT1／saved_material_support.py:30–38,104–124 | 原材料组装与工件基函数支撑追溯；大差定位到底边owner | 用corner_only补大差、单面压力、求解器错误 |
| M-VOLUME1／saved_material_volume.py:84–134 | 四个旧alpha case九点体积观察V与原弱力W吻合，eta层解释与上缘T的不同 | DD收缩重播、真实DivP原因、强制V=T |
| M-BOUND1／saved_q1_hu_boundary.py:71–106,139–154 | 原Q1 Hu四顶点符号、侧边成对平移抵消、owner／节点partition关系 | 非零节点=局部压力、corner_only=物理角点类别、唯一分配相邻面 |

例如旧alpha峰值cell10407的W_y=0.08022435531475952 N，T_y=0.01938390857410906 N；四case Fy的舍入P体积V与W同值。这说明两种离散作用不同，并没有出现需要再重建DD核的证据。旧Hu side-owner净平移作用为零仍可有非零组装节点作用；原数据已解释，不能据此抹掉局部Hu。这些局部数值属于旧alpha两个loading态，不能搬到新alpha上。

## 连续压力和有效夹持的真实缺口

当前总广义弱作用可写为材料一阶项＋Hu二阶项。`split_kernel_invariants_hu.py:169–180`实现c_e HᵀHu，c_e=krΣw exp(−5J)；`split_numpy_tangent.py:84–93`对这个实际残差包含dJ引起的系数导数。力里没有朴素½c_e||Hu||²能量梯度的额外项。因此不增加能量梯度oracle或“修复”原Hu力。

Q1 Hessian仅有xy／yx（`tmc_kernel.py:47–65`）。归档`nested_hu_boundary_001/author/physical_basis.json`已说明：声明常值Q1等效hyperstress可以表达相同离散作用，但其高阶边／端点作用不是一个普通Hu压力标量；同一有限nodal covector不唯一确定连续场迹或角点面归属。九点P也不唯一给出真实连续P／DivP。未来压力功能必须先明确恢复场、reference／current面积及法向、边导数／端点／跳跃与弱式剩余项的合同，不能将Hu补到P·N或把节点N除一个任意面积。

固定体反力可以报告为“作用于下半固定工件的有符号弱式合力”。两侧幅值和不是整物体净力或可移动工件的持重能力。有效夹持还需明确工件自由度、被抵抗的外载方向、摩擦／运动假设、成功条件和物理稳定性。已有HP核对的是声明的离散方程／方向，不能补网格／域／参数稳定性或压力资格。本轮只使用已有归档论文核查，不读取PDF或检索新文献。

## 三已有点的解释足够，不再独立开重复图卡

M-AVIEW1已有两个alpha的14加载态比较。新信息是alpha半值首次回撤及同两态新参考／API关联。原JSON可直接并列loading1.15／peak1.20／unloading1.15：

| alpha／阶段 | R（N） | 下半工件total Fy（N） |
|---|---:|---:|
| 1e−6 loading1.15 | 0.3471343276801674 | 0.10502110575473947 |
| 1e−6 unloading1.15 | 0.34713432768016655 | 0.10502110575478034 |
| 5e−7 loading1.15（父12） | 0.34703768154036385 | 0.10671287553103004 |
| 5e−7 unloading1.15（child1／原14） | 0.3470376815403639 | 0.10671287553103108 |

全为原保存值，未做新差值／比率。同输入局部回撤原值接近，是短段事实；不能认定全卸载可逆、无迟滞、根唯一或两点稳定。新alpha loading1.15父态没有被新4HP自动授予独立参考；峰值／回撤child的参考另行标明。没有必要为这几个既有点单独再生成数值图卡。

## 最近最小功能：显式末态卸载延伸的源码准备

支持root提出的最近方向：新task保旧15目标前缀，明确只append1.10 mm，从实际已接受1.15 mm末态续算一个新卸载步。成功后能增加目前没有的实际卸载态、变形和工件作用；比重复关联／HP／账本或先实现未定义连续压力更直接推进功能。新数值／测试／原viewer执行仍待具体候选及新批准，本审阅不选预算或新科学门。

必须前置的合同：

1. 锚点取` saved_continuation_001/run_001/resumed_alpha_half/result.json`的child1／原14，不取failed原alpha父result中不存在的第14态。其parent实际success，targets仅[1.2,1.15]。`native_resume.py:88–96`当前既要求完整旧task suffix又排除末目标，不能只传新targets；新增explicit extension模式，默认strict same-task分支保持。
2. 新task的旧15前缀／顺序精确保持，除path外全部物理／几何／网格／材料／工件／BC／控制字段保持。新canonical task SHA、model有效task身份要更新；旧result／model不改写为新task。若还改描述／task_id须单独说明，不能含糊称“只改path”。
3. 原lift／fluctuation／有符号R与状态SHA原样运输，target_origin=0、absolute initial_parameter=1.15；不以舍入−0.05重定位。fresh F／T锚点仅按原残差／均值门验证，不校正锚点；K=None，不借原force／tangent／matrix。原预测、未对称增广、R符号、回溯／回滚不变。
4. 验证实际child的original-index／continuation映射、最后接受态、descriptor／source／material／region／options身份。新直接parent诚实记success和短段完成；原M-ALPHA1 failed／time_limit及producer flags作为祖先历史完整保留，不把新parent强写failed或丢失旧failure。新child短段完成不冒称一次完成旧／延伸全路径。
5. 兼容性准备针对默认旧分支、非法prefix／物理变更／非末态拒绝、原状态运输、fresh-anchor失败不得校正、实际index14／15及viewer leg映射。真实一步和显示产生后才解读新数值；试探invalidJ不是新接受态，旧HP资格不转给1.10新态。

压力／自由体／摩擦随后独立推进。近期可将这个最小新接受态与已有原alpha同1.10卸载态作同任务敏感性解释，但不能在本轮预先算差值或给稳定阈值。当前只冻结物理／接口取舍，保持所有原数据、门和资格。

逐文件SHA、原值来源和最小模式风险见`physical_gap_review.json`。
