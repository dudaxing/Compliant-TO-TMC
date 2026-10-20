# L-CTIPALPHA1 实际记录有限独立审阅

2026-10-20（Asia/Seoul）；结论：**10/10 PASS，无阻断**。运行/绘图已经关闭，未重启或修复重跑。

- **unique_terminal_and_source_identity：** PASS: launch685586/session21276, terminal598586 exit0, one invocation, frozen protocol identity and owned cleanup verified; no restart.
- **fresh_alpha_model_and_original_task：** PASS: zero-start true, parent/state/extend false, no continuation; actual model alpha2.5e-7/Lr80,14720cells/29970DOF. Original13 load_only targets0→1.06 complete, origin/loading legs retained; no unloading claim.
- **original_settings_and_production_gates：** PASS: all actual settings match protocol, nonclock unchanged. Actual max residual4.83494e-10, max balance8.41383e-12, fixed split0, native constraint bounds pass, minJ4.658789e-4>0; original globalbalance1e-6 gate retained.
- **real_solver_work_and_internal_rejects：** PASS:70 Newton checks,59 trials=57 accepted+2 invalid_J rejects at1.05/1.06;0 failed attempts/0 bisection,69 linear solves. Force129 attempted/127 completed, tangent70/70,one solver,JIT/HP0; bounded internal rejects are not external retries.
- **complete_saved_rows_and_raw_history：** PASS:13 result/view/convergence rows match identities and original R/q/body force vectors; every diagnostic field and complete original newton/trial/failed/linear history retained; source SHA/leg/order preserved.
- **same_definition_thirteen_pair_comparison：** PASS:pinned historical baseline13 origin/loading rows,13 new original targets and23 metrics each; exact original index/d, original values and signed new-minus-baseline differences match. No interpolation, source-leg rewrite, clipping or cost/alpha independence gate.
- **actual_parameter_response_and_limits：** PASS as faithful observation:peakR0.1952230415N,Fy0.01237252461N=material0.00931815203+Hu0.00305437258N; unsigned tip/Q1distance0.008227522523mm. Net Fy stays close while component and medium-field changes are substantial; no alpha-independent or pressure conclusion.
- **six_new_views_and_one_actual_GIF：** PASS:original pure viewer13 geometry/nodal/boundary/region observations,27 archives/261 fields,4PNG+13-frameGIF; convergence+comparison add2PNG. No fresh F/T/solver/HP in viewer; original producer flags/reference remain unqualified.
- **resource_seals_and_single_visual_QA：** PASS:helper6622.9072332s/outer6625.1352186s,treeRSS1468190720B,shared display31.8649741s;129 outputs367934417B original-window sealed/stat matched. Root sixPNG each once QA721b1c passed with documented visibility limits; no reviewer media read.
- **qualification_scope_and_next_step：** PASS: no old-alpha HP transfer, full-cycle/unloading/pressure/effective grip/release/stability/alpha-convergence/HF5 upgrade. Existing segmented baseline vs fresh run is not a pure-alpha CPU comparison; next selected new-peak HP requires a new card.

峰值同输入：总Fy从0.01259251473277105 N变为0.012372524610902783 N，材料分量增加0.0012847397684314175 N、Hu分量减少0.0015047298902996814 N。净合力接近掩盖了分量和场的变化，不能据此称正则独立。全介质minJ从0.0009015839179744192降至0.00046587891715793817，而右条带minJ升高；不把这概称为全部介质改善。

下步先对新alpha真正峰值保存态做HP80/120、原15门独立参考。当前不继续加载/降alpha、不改变物理条件、不把旧alpha通过迁移给新参数。审阅只读普通记录与原seal/stat，六张新图由root各检查一次。
