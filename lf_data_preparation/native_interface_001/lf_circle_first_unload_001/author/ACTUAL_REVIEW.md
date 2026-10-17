# L-CUNLOAD1 actual finite review

Review status: **pass_actual_finite_review**. Execution status: **NOT_PASS**. These statuses describe different things: the actual failed run is consistently recorded; the unloading feature has not passed validation.

The sole helper installed `native_resume.py` from `e8162964487df510a608a980feb1a03b3ac36e97a55452fac9e342274cfee2d1` to `68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798`. All 78 current ordinary source bindings match the frozen protocol; this reader is the only baseline source transition. The existing native_mean task-path caller gate remains unchanged (`76fd9917...fd6e4`).

The first test errored at `test_first_unload.py:310`: its zero-start `direct()` passed `targets=None`. Unchanged `native_mean.py:178–179` requires explicit zero-start targets to equal the declared task path and raised `TMCError(code="invalid_input")`, before the controller call at line249. One method began, zero methods passed; the other seven did not run. No saved first-unload branch was reached.

Actual accounting is **native entry started1 / returned0; equilibrium controller0; accepted states0; F0 / T0 / HP0 / JIT0; plots0**. The report field `real_solver_invocations=1` increments in a wrapper before calling native_mean and therefore does not establish an equilibrium-controller invocation. Its `count_scope` sentence describes six planned solves, not completed work. Likewise `completed_methods` records unittest's stop event, not a passing method.

The helper sealed five actual partial outputs inside its original window. Four ordinary JSON/log files were checked by SHA and size. The sole scientific payload, `t/01/source/geometry.npz` (805bytes), was checked only against its existing producer seal and filesystem size; this review did not open, rehash or decode it. No result/accepted-state output, scalar observations, path observations or PNG exists. The partial seal covers every run file except the receipt itself.

The launcher records one invocation, exit1, 5.1718436s and verified CPU-CLEAN1 cleanup. Helper elapsed was 3.1484738s, with no following plot stage. The actual reader installation is retained, without rollback.

The smallest next correction is only in the test zero-start caller: pass `task["path"]["targets_mm"]` explicitly in `direct()`. Saved-continuation calls should retain their existing behavior. A future execution card must also distinguish native-entry attempts from actual equilibrium-controller calls in its reporting. No repair, test, scientific run or default-source change was made during this review.

Blocking findings in the consistency of this actual record: `[]`. A passing finite record review does not reverse the failed execution, validate first unload or grant circle/HP/pressure/whole-path qualification.
