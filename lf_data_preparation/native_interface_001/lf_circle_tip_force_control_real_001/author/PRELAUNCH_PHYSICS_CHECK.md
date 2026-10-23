# L-CTIPFREAL1：运行前物理／源码静态前置核对

2026-10-23。独立审阅 `/root/fload_controller`。结论：**12/12项普通元数据与源码静态核对通过，未发现当前正式来源或已安装控制器的静态阻断。** 这不是完整准入、fresh平衡或正式chunk256运行通过；worker及最终资源包装尚待后续独立静审。

正式ROOT：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，本次读查HEAD `e80009232796d158b466fbd887cde82fdd7859fe`，main工作树当时干净。57份已装生产Python源码全部AST可解析、source目录相对HEAD无差异；准备记录中的11份入口源码pin及LOW1父记录的4份原mechanics SHA均匹配。两新模块仍是已通过FLOAD1的原字节：native SHA `48342b5eb735c98dfd27ddfd15e398feb03ab2d1bc7d32b258c8489b2d22d322`、split SHA `975d1e1797403c2cddbda2ee04c8ef0e3d5e07d038bdb48473e4ff6e60fcf0c6`。

## 来源与_admit条件

仅读原 `D:/hlo1_001/run_001/parent_fixed` 中 result、model/model、accepted/002/state、model/source_geometry/geometry 四份普通JSON。用纯标准库复核其float.hex canonical描述身份，以及模型/任务/选态/源几何的普通SHA及嵌入关联；与已发布SOURCE_BINDING一致。未复制科学来源。

|核对项|静态结果|
|---|---|
|完整父任务|status success，path_completed/target_reached/loading_peak_reached均true；fixed_rigid/load_only，原目标恰[0,.25,.50]|
|选态位置|真实最后accepted index2、原target index2、is_original_target=true，d与原目标及mean target均.50 mm|
|原split来源|lift_origin_zero/lift_shape_zero声明true，选态state SHA为48fd7c621a8b1a060a5bec81307f2c8fe524569c6a4052da75884a8053e45bd8；signed R=.08589635225389337 N|
|归档字段声明|原选态只声明float64 lift/fluctuation，各29970项；这里只核声明，未打开归档|
|物理|r9/center(80,40)/right92/Lr80、α2.5e−7、γ1e−6、E1/ν.3/plane strain/t20/h.5与准备记录相符|
|模式|mechanical/chunk256，block256/full-batch selector；父port_projection仅作来源metadata，新力控为guided reduced tangent|

静态成员：14720单元，14985节点，29970原全场DOF；原free28682，原fixed1288；工件510单元/565节点，body-x565；zero去重195，body-y背景重叠37。`zero∪body DOF`恰等于原fixed，除允许的body-y/background外无冲突；input/output非零DOF均不含body。去body-x后的外力支撑DOF为723。新reduced未知(w_F,q,R)为28684，不能将其称成另一个网格或29970个自由未知。

原 `_admit` 的普通条件现在都可静态对应。其后仍必须在唯一worker内验证opaque model NPZ整字节SHA、重构geometry的四mask及actual material/grid/region、原selected split归档及字段SHA/dtype/shape、state hash和fixed零位。上述payload未打开，因此本审阅不宣称它们已经通过。本次卡不包含旧ZIP解压或旧科学包复制。

## 控制方程、尺度与chunk256兼容性

已逐段静读当前native_guided_force、split_guided_force、原_admit，以及split_numpy_tangent的full/chunk实现：

- API按父response_mode选原mechanical force；tangent_mode=chunk256分支调用原 `_tangent_chunked`，随后 `_assemble_tangent` 仍组装完整29970×29970 CSC，原fixed body行/列没有提前删除，因此新控制器可取得K_Fc/K_cF/K_cc。
- chunk函数从完整fields先决定small-product/direction selector，块内仅裁剪fields及lam/mu，保留原full-batch选择语义；不重选body或端口。它不是把小模型full的通过冒充正式chunk256力控通过；本次仍是后者首次真实尺寸验证。
- 新reduced块K_Fc与K_cF分别从实际K列和行求和，未互以转置代替，c权为1，P只进入generalized行一次。一般sparse LU，无对称化或隐蔽正则。求和只产生一行/一列，未创建29970×28683 dense选择矩阵。
- 正式d_scale=.50 mm，E*t=20 N/mm，F_floor=1e−7 N；mean bound=5e−11 mm。SF沿原free门；SP=max(abs(P),abs(P0),F_floor)，两个原P的g绝对bound分别3.686421133658022e−14及约4.327230694875673e−14 N，与大型输入R分开，不把弱body失衡藏入R主导范数。
- P0/P1均为正绝对half N：3.686421133658022e−5、4.3272306948756724e−5；它们来自正式LOW1，不能使用小模型负P或取增量替P0。保持厚度一次、P_full=2P_half而q不倍增。
- P0先fresh F/T；free/mean/g不过即停止，未进入predictor或mean投影。原split与R身份由capture再次核check1/hash/R bytes。后续mean可行补偿只作用非body port，q完全未知不夹限。
- merit固定当前base SF及目标SP，保原Armijo/backtracks/checks；N二分仅新4.0050597576103156e−7 N步长和depth4，mm .00625不混入N。17接受态上限是单区间的内部子增量容量，不是外部多次调用许可。
- support只含原fixed−body-x，global显式加(P,0)，body-y及zero去重；API以原rigid/global门验收。保存使用同state已缓存F/T，不再调用力或切线；异常保实际partial，资格flags不升级。

未发现这些源码分支与正式来源间的静态不兼容。真实reduced Jacobian是否可解、局部branch能否满足body合力门、以及端点工程回归是否通过，均只能由获批唯一路径的新证据判定；没有计算新切线、灵敏度或conditioning来预判答案。

## 已冻结门及下一步启动依赖

端点q及全场max-DOF物理位移各≤1e−6 mm，R≤max(1e−10 N,1e−7|R_ref|)，仍为预先声明的工程回归门。数学平衡、fresh身份与工程比较分别成立；不以工程界放宽原残差，也不以小模型约4e−13mm实差代替正式界。

下一步只在薄worker/资源包装冻结及独立静审通过后启动原卡：API1800；science worker连导入/准入/保存/清理≤1900；comparison60；display+root QA共享600；helper2700/outer2760；64GiB采样、四库各16、viewer8GiB。唯一API、首终端错停、无外部修复重跑、HP或测试，原同实例清理及原窗口一次字节封存。

若worker用sys.audit观察NPZ open，可据实证明只读文件路径与打开次数；字段6应明确由“成功API+冻结源码控制流”推定，而不能冒称动态逐字段监测。comparison自行解码的4个state/8字段则应独立记录实际读取。当前前置核对不安装运行监测器、未启动任何HF或viewer。

本审阅动作：只读普通JSON/源码、标准库AST/hash/canonical与只读Git；NPZ字节/哈希/字段读取0，媒体读取0，HF/科学导入0，新F/T/平衡/测试0，生产修改0。完整57份源码身份及12项布尔结果见同名JSON。
