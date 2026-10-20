# L-CTIPAUNLOAD1：新 α 峰值后的首次小回程（候选，待批准）

本卡仅完成外部候选准备与有限静审；未冻结到正式仓库，未启动平衡、显示或测试。`authorization.proposed.json` 的 `authorized=false`。L-CTIPAREF1 已关闭，其批准不延续为本卡的执行许可。

## 目标、依据与当前判断

整体目标是：HF 独立读取 LF 的普通几何，在明确一致的任务下计算非线性响应及接触相关量，供外部研究层比较。HF 不执行 LF 优化。本轮最近的功能目标是继续新 α 的加载／卸载路径，并显示真实变形、力与介质状态。

L-CTIPALPHA1 已从零完成 α=2.5e−7 的原 13 个加载目标，0→1.06 mm；峰值最小 J=0.00046587891715793817。L-CTIPAREF1 已对该峰值完成 HP80/120：原 15 项门均通过；全局总力归一误差 1.4373270987530929e−15（门 1e−11），PORT 总切线 8.349328803857869e−17（门 1e−10），HP120 自由残差 1.1974830748218591e−12（门 1e−8）。这支持继续一个小回程，尚不能推断卸载、释放、压力或有效夹持力已合格。

最近一步仅执行 1.06→1.05 mm，不继续加载。与同一 α 的原加载 1.05 mm 作同位移描述性对照，以观察回程响应和介质恢复情况；不预设两态必须相等，也不新设归零、单调性或滞回门。

## 来源、输入与固定物理

- 正式 Git 根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`。
- 基线 main：`eecd5c6ddfcfe01da46a37d0d0b980068eb930ec`；origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。
- 外部候选：`D:/hf-native-workpiece-api-author-20261020/L_CTIPAUNLOAD1_preparation_001`；批准后新增阶段 `lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001`。
- 父结果：`lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/result.json`（上级均为 `lf_data_preparation/native_interface_001/`）。父为从零成功的 13 态，非旧分段续算结果。
- 只恢复 accepted012/global12，d=1.06 mm，split 状态身份 `e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68`，原有符号输入反力 R=0.19522304147728387 N。
- 原加载对照仅用父 viewer 的普通 `summary.json` 第 11 行：global11、raw leg=`loading`、d=1.05 mm，状态身份 `0f2605abda45ff6a96d90b7c97d5dc26e430e2fb80ef1427c275f04e39a4385e`。
- 仅两份旧科学输入：父 `model/source_geometry/geometry.npz` 的四个 mask，以及 accepted012 的 `state.npz` 中 lift/fluctuation 两字段；准备时仅继承原 helper 的 SHA/大小封条并 stat，不读取或重新 hash 旧 NPZ。获批后由唯一 helper 做身份核查及必要解码。旧 model/force/tangent/matrix 数组和旧媒体不读取。

固定工件 r9 mm、圆心(80,40) mm、右域界92 mm、Lr80 mm；0.5 mm 网格、14720 单元／29970 DOF；E=1 MPa、ν=0.3、plane strain、厚度20 mm、γ=1e−6、α=2.5e−7，以及其余材料、约束和支撑均保持。

任务仅将父 `path.kind` 从 `load_only` 改为 `ordered_cycle`，原 13 目标完整前缀后追加 1.05 mm；`input.target_mm` 仍为1.06。四项父任务 metadata 原值照存（其文字描述父加载实验，本卡及 continuation 明确子段身份）；其余所有任务字段完全相同。默认 API 支持此路径提升，不修改默认源码。

## 最小实施步骤

1. 完成候选包装、任务／protocol 绑定与独立有限静审；仅 AST、源码差异及普通元数据核对。取得本卡明确批准后才将独立真实授权记录设为 true，并冻结已审候选；不伪造授权。
2. 唯一调用现有 `evaluate_native` 保存态延伸入口：恢复父 split 和有符号 R，重新计算／核查 1.06 mm 锚点，再首次回到1.05 mm。实际请求 suffix 为 `[1.06,1.05]`，不重放前13加载目标，不复用旧力、矩阵或切线。
3. 原生产门全部保持：平衡相对残差≤1e−9；平均位移约束按原原生尺度门（constraint_tolerance=1e−10）；全局力平衡≤1e−6；固定 split 位移≤8e−11 mm；原正 J、Armijo、回溯与内部二分规则保持。原 max_checks25、max_backtracks12、max_bisections4、minimum_increment0.00625 mm，除新 clock 外设置完全相同。
4. 成功后仅运行一次纯保存态 viewer 与收敛投影。生成5张 PNG、实际 N 帧 GIF、状态表、普通 JSON 和人工页：实际×1变形／原点锚与真实LAST对照、R/q／工件 total-material-Hu 弱力、LAST场量、右侧介质与尖端距离、Newton残差／线搜／二分 chronology。实际文件名以绑定源码为准。
5. 使用原加载1.05 mm普通摘要与新卸载1.05 mm的13项既定标量，输出原值与有符号差。保存 raw leg、global index 和 SHA。仅描述，不新增相等或滞回门；q 是端口位移，不是间隙；无符号边界距离与交叉／重叠标识分别保留。
6. 原窗口内封存实际输出；五张新 PNG 各最多一次像素检查，GIF不另解码。数值通过和显示检查分别记录。实际结果独审后关闭本卡，更新既有7份前置说明并原样保留旧后缀；普通 main 提交推送、同机异路径 local-Git 对象 fetch＋ff-only 恢复与远端身份核对、一次发布归档。不得称为另一机器的独立复现。

## 资源与停止条件

| 项目 | 唯一窗口／限制 |
|---|---:|
| Controller | 1800 秒 |
| 显示共享（含 viewer／收敛／表页） | 600 秒 |
| Helper（含核查、科学、显示和封存） | 2700 秒 |
| Outer（含清理） | 2760 秒，最多46分钟 |
| 采样进程树 RSS | 64 GiB |
| OMP／MKL／OpenBLAS／NumExpr | 各上限16线程 |
| 原纯 viewer 内部限制 | 8 GiB，不修改 |

CPU线程上限沿用已批准的本机资源政策；不新增 GPU 路径、JIT 或依赖变化。窗口非累加延期许可。原 SUP2 同实例终止／成员覆盖／句柄释放合同保持。

唯一启动；首个终端错误停止后续科学与显示，保真实 partial。仅原 helper 窗口仍开放时允许一次实际部分证据封存，不重启 helper。原内部回溯／二分允许；首次 −0.01 mm 失败时，半步 −0.005 小于原 0.00625 mm 下限，按原规则终止。

无外部重试、修复重跑、延期、force、删除、回滚、新 HP、新测试、默认 HF 改动或 API 摘要关联。源码／输入绑定不符也停止；不得临时调 α、门、软硬度、工件位置或步长下限来获得通过。失败后另据实际证据计划，不能续用旧窗口。

## 完成定义、资格与后续分支

本卡成功仅指首次小回程与其显示／记录完成。父峰值的 HP 资格保持在父峰值；新卸载态不继承 HP。不得提升整条路径、α独立性、压力、有效夹持、释放、稳定性、网格／域宽收敛或 HF5 资格。节点 weak force 仍分 total／material／Hu；保持 ON-body 力与保持反力的反号关系，不称为接触压力。

若生产及显示通过，再据实际反力、J/Hu、距离与收敛决定是否较粗推进至1.00 mm，或先定位异常／核新卸载态独立参考；不预先授权后续目标。若失败，先看真实 partial 与失败类型，不修改原失败历史或自动补跑。

## 对照代码与审查材料

外部 `execute_step.py`、`launch_step.py` 是旧 L-CTIPUNLOAD1 的薄包装适配；`circle_saved_views.py`、`plot_convergence.py` 继承已有 LAST 语义，只调整 α／身份文字。默认入口 `hf_repo/src/hf_eval/native_resume.py`、`native_evaluate.py`、`split_displacement.py` 保持原字节。`assemble_step.py` 仅生成外部 task／protocol／false授权／准备回执；`freeze_step.py` 在真实授权缺失时拒绝冻结。

待完成的 `SOURCE_REVIEW.json/md` 逐项绑定4份运行源码、支持脚本和候选 protocol／task；不将静审称作运行验证。`preparation_receipt.json` 记录0旧科学读取、0新科学调用、0测试及0正式阶段写入。
