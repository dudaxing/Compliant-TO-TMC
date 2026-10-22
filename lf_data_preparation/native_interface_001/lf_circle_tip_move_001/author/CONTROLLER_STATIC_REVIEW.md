# L-CTIPMOVE1 controller 独立静审

2026-10-22；审阅者 move_probe_impl（非 controller 作者）。仅全文件和 no-index diff 静读，无 HF 导入、测试、F/T 或 HP。

结论：12/12 项通过，无当前阻断。此为源码静审，不是数值通过。

|项|内容|结论|
|---|---|---|
|C1|default offsets arithmetic|PASS：Default _dot receives separate -target_origin and -s; same rounded mean_target only where original used sum.|
|C2|opt-in isolation|PASS：prescribed_body=None retains default fixed lift guard and prior signatures/options; body scope is explicit.|
|C3|rigid prescribed map|PASS：Body xy remain model.fixed_dofs; body x shape is exactly one; body y and all other zero supports stay zero.|
|C4|DOF conflict contract|PASS：Exact union is C; body port components rejected; zero/body overlap only declared background body-uy.|
|C5|independent q and held mean|PASS：Projection, measure, predictor RHS, force floor and constraint bound all use held mean in probe branch.|
|C6|fresh q0 ordering|PASS：q=old_s=0 bypasses predictor/feasible; evaluates fresh F/T and measures original split/R before a corrector.|
|C7|wrong q0 no correction|PASS：fresh_anchor_required forces failure immediately when force or mean gates fail, before linear solve.|
|C8|any typed anchor terminal|PASS：advance catches KernelError/TMCError and blocks bisection for first probe anchor regardless of failure code.|
|C9|non-symmetric solver retained|PASS：Original tangent force predictor, bordered KKT and general sparse LU are unchanged; no symmetrization.|
|C10|state and rollback retained|PASS：Original copies/rollback byte checks remain; opt-in accepted row declares body q and input mean separately.|
|C11|legacy scope retained|PASS：No force kernel, tangent, resume or fixed native entry source edits are needed by this controller diff.|
|C12|interpretation|PASS：Stage d in raw history is q; accepted probe fields and viewer must label q and input mean distinctly; no bearing/release qualification.|

绑定文件：

- `D:/hmv1_001/candidate/hf_repo/src/hf_eval/split_displacement.py`，27062 bytes，SHA256 `65e5cb15a54b53978abb744ee7e99928cadfffefb9afb71fdc6dcfcd139e295e`。
- `D:/hmv1_001/candidate/hf_repo/src/hf_eval/native_probe.py`，19317 bytes，SHA256 `93667361fcb8168d800833a849d411a669b576b11c565cdbfc534bd3457ae8b3`。
