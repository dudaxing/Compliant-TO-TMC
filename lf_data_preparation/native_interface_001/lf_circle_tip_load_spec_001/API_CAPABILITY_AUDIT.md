# L-CTIPLOADSPEC1：真实native接口能力与最小扩展缺口

只读准备，2026-10-21 Asia/Seoul。未编码、调用/import HF、计算新力／平衡、测试、绘图、读取科学NPZ/CSV/gzip/媒体、操作Git或写正式仓库。当前main身份由root报告为`8d589b65ab2e4efe8ca01b95034ed329fca81171`；本审计未另做Git操作。

**现有native API支持固定工件与一个机构输入平均位移约束，不支持“保持输入＋独立工件刚体位移q／外载”的新物理任务。旧固定边界保存态也不能直接作为新physics的默认续算。**

## 真实调用链与已有能力

真实public入口是`hf_repo/src/hf_eval/native_evaluate.py:evaluate_native`（23–26行），不是native_api.py。它接受geometry/task/output、机构单标量targets、设置和严格saved_result选项；103行调用`solve_native_mean`，其175行`build_native_project`，249行进入`solve_split_displacement_path`。没有独立body-q/body-load参数。

|已有能力|精确源码|当前边界|
|---|---|---|
|固定圆／方工件|native_project.py:97–107|仅fixed_rigid，fixed_components必须[0,1]|
|工件原区域与DOF|native_project.py:150–168、228–231|中心在上边y对称线、完整半工件必须入域；节点与原机构/端口/支撑分离；所有body ux/uy并入fixed|
|机构平均位移控制|split_displacement.py:55–75、189–207|唯一b_in·u=d0+s；未知机构反力R_input；原output仅测q_out/一般弹簧|
|同物理任务保存态续算|native_resume.py:153–209、229–248|原task/model/material/boundary/source/options严格相同，仅新clock与规定path扩展例外；新鲜F/T复核anchor，不恢复旧矩阵|
|固定工件弱力观察|workpiece_nodal.py:13–21、32–43、53–76|全body DOF必须固定；原参考坐标、三力、holding和矩；不是可动body或外载入口|

现有研究reader只读保存报告，不施加载荷或改变自由度。上述能力不授外载承载、自由释放或稳定性资格。

## fixed_rigid并不是已实现的可动刚体

`native_project.py:97/106`不允许改kind或只固定某一分量；`_object`（project.py:72–75）拒绝未支持字段。即使后续只放宽解析，原_workpiece_region仍在168行取全部ux/uy、231行并入fixed；JSON标签不能改变这套运动学。

这里的工件是原passive_void上的运动约束overlay。原材料分类仍按源solid/medium，见native_project.py:160–161、244–245、274–276；184–185明确全部工件节点保持未变形、内部F=I/Hu=0。把565节点解锁，得到的将是可变形的原介质区域，不能称刚体平移；只约束节点平均量也不能约束其刚体形状。

若规格选择仅+x导向平移，最小运动学需明确所有工件节点共同ux=q_body、uy=0且转角固定。这是未来约束映射／绑定的需求说明，不是已经可用的JSON选项或候选实现。改变center_mm是另一个参考布置，不等同沿已变形路径施加body-q。

## 两个控制量与一个mean约束的差别

当前targets是一个标量向量；native_project.py:78和split_displacement.py:105–108还禁止相邻重复目标。它表示机构输入目标，不能用重复d列表来偷偷表示“机构输入保持不变时，body-q继续变化”。

`displacement.py:105–114`的KKT只有一列b_in及一条平均约束；126行只取一个标量multiplier。b_out用于output测量／弹簧，不是第二个独立位移控制。`split_displacement.py:116–117`还要求所有fixed DOF的lift为零，故现成affine lift选项不能移动当前fixed workpiece。

拟议双控制任务须有明确(d,q_body)路径及两类反力。若采用双mean方程，需两套独立控制列／约束与乘子，并另有刚体节点约束；若采用给定body-lift／消元，则仍需新增移动body与零支撑的区分、独立控制路径及body反力恢复。两种表述都不是原单mean controller的现有能力；本审计不编实现，也不放松原门来绕过缺口。

## 外载入口与可报告量

当前native task的严格字段表在native_project.py:34–43，没有工件外载；public签名亦无该参数。output/auxiliary spring在85–89行强制为零。底层通用controller虽含输出弹簧，实际残差（split_displacement.py:192–193）仍只有internal＋spring−b_in*R，没有独立工件external load项。

R_input是求得的机构反力，不是给定工件外载；当前holding是把工件固定的支撑反力，也不是用户已施加的拔出力。下一规格应区分：

- 给定body-q、读取导向刚体的抵抗反力：位移控制的功能探针。
- 给定工件外力、求body运动／平衡：外载控制任务，需要额外载荷向量／广义力及平衡口径。

不得把两者混称自由承载试验。不存在接触而仍承受非零外力的自由工件未必有静态平衡；不收敛、刚体零模或资源停止均不能直接标“释放”。

## 保存态restart边界

native_resume.py:183–184要求同一原task；195–201核grid/material/region boundary/counts和geometry身份；202–209核非clock设置／选项及force/tangent源码。229行还核saved lift／fixed DOF边界。append-only在82–86行仅准原任务追加targets（有限path/描述metadata例外），不是任意新physics restart。

因此旧fixed-body峰只作参照，不能借extend_path、新kind或改descriptor/hash来续成可动／外载任务。最小安全起点是显式新物理任务；若以后确需运输旧位移作初猜，须另行定义刚体映射／可行性、迁移来源、新任务平衡与反力复核，保旧祖先结果，不继承旧资格或旧矩阵。本阶段不做这种运输。

## 最小扩展顺序与对称要求

1. 先在物理规格固定guided body的方向／其余刚体约束、输入保持值、body-q或外载控制、加载顺序与成功／停止定义；本审计不选择新数值端点或阈值。
2. 对称相容的+x平移、uy与转角固定可作为最小候选；外载必须具有一致的y镜像口径。一般竖移／转动不保持当前半模型，需要先选完整模型；半／完整载荷单位与倍增条件必须显式定义，不能事后自动乘2。
3. 再单独提出opt-in刚体运动学、双控制／载荷残差、状态与真实位置／反力持久化的最小实现。可复用当前NumPy力／切线，不能重用fixed-body观察器作为移动坐标或新承载验收。
4. 对该新实现先作另行获批的有界小模型验证，再安排真实工件试算与实际运动图。当前没有新代码、数值预算或执行授权。

8份准确源码的SHA、逐条行文与结构化已有／缺口表见[API_CAPABILITY_AUDIT.json](API_CAPABILITY_AUDIT.json)。结论只覆盖这条真实native调用链，不声称扫描了全仓库其他项目或全部历史；没有打开任何保存数组、状态或媒体。
