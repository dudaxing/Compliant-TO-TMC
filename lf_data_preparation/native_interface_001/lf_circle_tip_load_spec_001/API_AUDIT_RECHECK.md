# L-CTIPLOADSPEC1：接口审计复核与最小扩展边界

2026-10-22 Asia/Seoul；只读源码／普通元数据复核，未调用或 import HF、F/T/HP、平衡、测试或 Git 修改。

**结论：原审计关键结论准确。最小候选应选独立给定工件 +x 位移 q、机构输入保持 d=1.06 mm；body DOF 消元，保留原单输入 KKT。当前接口不能直接完成。**

## 必须澄清的原门层级

- `split_displacement.py:150–160、189–207、270–273`：有限场、J>0、自由力残差相对门及平均位移门由 controller 执行。
- `lf_circle_tip_alpha_001/execute_step.py:217–227`：global balance≤1e−6 与固定拆分位移≤8e−11 mm，加上原 residual／mean／J，在研究 wrapper 做实际拒绝验收。不能声称默认 evaluate_native 自动强制了全部五门。
- `protocol.json:29–51`：真实原设置为 residual1e−9；mean bound=1e−10×max(|d|,1e−6 mm)；force floor factor1e−8；25检查／12回溯／4二分；minimum_increment=.00625 mm。`DisplacementSettings` 类默认 min increment不同，后续不得误用类默认替换此真实任务值。

## 最小实现边界

新增 opt-in prescribed guided body：固定参考成员，所有 body ux=q、uy=0，波动在 body DOF 为零；原支撑仍为零。以 q 推进路径，机构 mean target 独立恒定1.06 mm。未知量仍为非 body 自由波动与 R_input；KKT仍一列。

当前同一个 s 同时控制 lift 和 d0+s（`split_displacement.py:61–69`），且 fixed DOF 非零 lift 被拒（116–117行）。只放宽 parser 或 fixed guard 均不足；不可让 q 顺便增加机构位移。prescribed body DOF消元无需第二平均约束，也无需先开发通用 force-control／MPC 框架。

## 新任务必须明确检查


- **legacy_unchanged**：Default fixed_rigid construction, parser rejection, old zero-fixed guard and strict resume retain old behavior; new mode is explicit and cannot enter via old extend_path.
- **disjoint_sets**：Fix body membership once from the reference overlay; no support/port/body conflict, body-y/background-y overlap deduplicated. Distinguish all prescribed DOFs from zero-only DOFs.
- **rigidity**：Every body ux uses identical stored q lift and zero fluctuation; every body uy remains zero. Check each compensated physical ux-q and uy, not just a nodal average; maximum error<=8e-11 mm. Do not release individual body nodes.
- **zero_support**：Every original zero support/entity/background component remains compensated physical zero<=8e-11 mm; do not apply the old zero target to moving body ux.
- **input_hold**：Compensated b_in dot(lift+w)-d_hold <=1e-10*max(abs(d_hold),1e-6 mm) at every accepted q. q never replaces or increments d_hold.
- **free_equilibrium**：Non-body free residual r=fint-b_in*R (k_out=0) normalized exactly as original, using d_hold in the force floor, <=1e-9; all J>0 and all recorded fields finite. Individual constrained body force need not vanish.
- **reaction_sign**：A_half_x=sum body r_x is actuator-on-body generalized force; model-on-body Fx=-sum body fint_x. With no other body external load they cancel. No nodal averaging or extra thickness factor.
- **accounting**：Whole-domain force balance uses zero-support/guide/body-actuator/input exactly once and remains <=1e-6 under the original balance scale. Preserve total/material/Hu summaries and signed half-body reports; guide reaction is not free-body load support.
- **anchor**：Explicit new-task q=0 start admits only pinned old split components and multiplier as a candidate; preserves body/source IDs and settings; independently checks body/mean constraints, performs fresh F/T, and passes gates before q advances. No old tangent or inherited qualification. Admission absent => do not pretend ordinary saved resume works.
- **jacobian**：For prescribed q eliminate body correction DOFs; predictor includes -(K deltaL)_free and constant-input constraint correction. The force tangent stays nonsymmetric. Small-model finite directional residual comparison should inspect the actual residual Jacobian, not an energy Hessian.
- **failure_state**：Any terminal error retains accepted q states and reason; timeout/zero mode/nonconvergence never classified release or capacity limit.
- **positions**：Observer stores reference and actual x=X+q, y=Y for body and actual split deformation for mechanism/medium; no remasking/rebuilding the body by moved center; old fixed-only observer cannot be silently reused.

## 真实风险与解释边界

原固定 peak 不是新运动任务的自动 resume；`native_resume.py:183–209、229–230`故意核同任务／边界／零 lift。显式新任务的 q=0 数据准入需要另行实现与新鲜力学核查，不得改旧 hash 或绕过原门。

工件导向反力可含第三介质材料及 Hu 贡献、竖向导轨反力与对称约束。位移控制得到的是轴向驱动力—位移曲线，既不是给定外力的自由承载任务，也不自动产生拔出承载上限。非收敛不等于释放。

## 读取范围偏差记录

本复核有一次过宽递归 rg，扫描了 alpha／STEP10 文本子树，输出至少一条既有 nodes.csv 行及普通 JSON/jsonl；可能扫描多份 CSV，数量／字节未知。此为只读范围偏差，未对 CSV 做数值处理。未读 NPZ/gzip payload 或旧媒体，未新增科学计算／测试；不能将本次CSV读取宣称为0。后续已限精确文件。

精确 source SHA、行号和检查条目见 [API_AUDIT_RECHECK.json](API_AUDIT_RECHECK.json)。
