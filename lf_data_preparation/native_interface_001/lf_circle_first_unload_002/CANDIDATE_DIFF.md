# L-CUNLOAD2 exact candidate delta

Author-only, AST/compile(source) checks; no HF import, test, solver, install or default change. The frozen001 source36761bytes SHA `184d3c55b23cd4e5d8155b93d0b888f865d416167ae72523091282ffd60945ab` and all old receipts remain unchanged. The new source SHA is `e168381228ea097a614df618946a06ad90ea43660047150e47764e09bb0a960e`.

Only two functional corrections are included: (1) explicit task targets for zero-start direct calls, None retained for saved mode; (2) distinct native API entry/return counters and accurate original-controller counters, with matching success assertions/report scope. The original controller is called once and its original return forwarded unchanged. No math, settings, gate, cache, negative list or scalar-output expression is replaced.

Static proof:7 of8 test-method ASTs exact; method08 differs only by the2 added native-entry count assertions. All9 literal transformations reverse exactly to the frozen001 source. The8 methods/25negative cases/6real/2linear and existing J/residual/constraint/global-balance/fixed-fsum/cache/source gates remain. Runtime result is still unknown.

```diff
--- frozen001/test_first_unload.py
+++ L-CUNLOAD2/test_first_unload.py
@@ -19,7 +19,8 @@
 WORK = STOP_FILE = STARTED = TIME_LIMIT = None
 RESULT = ACTIVE = LINEAR = None
 SCALARS, PATHS = [], []
-CALLS = dict(real_solver_invocations=0, real_solver_completed=0,
+CALLS = dict(native_entry_started=0, native_entry_completed=0,
+    real_solver_invocations=0, real_solver_completed=0,
     real_force_calls=0, real_force_calls_completed=0,
     real_tangent_calls=0, real_tangent_calls_completed=0,
     HP_calls=0, JIT_calls=0, linear_controller_paths=0,
@@ -64,7 +65,7 @@
         elapsed_seconds=perf_counter()-STARTED, time_limit_seconds=TIME_LIMIT,
         per_tiny_controller_seconds=30., work_directory=WORK.as_posix(),
         clock_scope="Shared import/tests/partial-record clock; external owner supervises process",
-        count_scope="Six actual native controller solves; two synthetic linear controller paths. Invalid pre-evaluation entries are separate.",
+        count_scope="native_entry_started/completed count native API entry/return; real_solver_invocations/completed count only the original native_mean controller boundary. Two synthetic linear paths and invalid pre-evaluation entries are separate.",
         scientific_scope="16 cells/50 DOF, no workpiece; no gripper/contact/HP qualification"))
 
 
@@ -177,6 +178,7 @@
 
 def tracking_hooks(stack):
     raw_solve = native_mean.solve_native_mean
+    raw_controller = native_mean.solve_split_displacement_path
     raw_force = native_mean._assemble_mechanical_force
     raw_tangent = native_mean._tangent_chunked
 
@@ -194,13 +196,19 @@
         CALLS["real_tangent_calls_completed"] += 1
         return value
 
+    def controller(*args, **kwargs):
+        CALLS["real_solver_invocations"] += 1
+        value = raw_controller(*args, **kwargs)
+        CALLS["real_solver_completed"] += 1
+        return value
+
     def solve(*args, **kwargs):
         checkpoint("before real solve")
         if ACTIVE is None:
             raise AssertionError("Unlabelled real solve")
-        CALLS["real_solver_invocations"] += 1
+        CALLS["native_entry_started"] += 1
         value = raw_solve(*args, **kwargs)
-        CALLS["real_solver_completed"] += 1
+        CALLS["native_entry_completed"] += 1
         ACTIVE["result"] = value
         for key in META_COUNTS:
             META_COUNTS[key] += value.metadata["call_counts"][key]
@@ -226,6 +234,7 @@
         report()
         return value
 
+    stack.enter_context(patch.object(native_mean, "solve_split_displacement_path", controller))
     stack.enter_context(patch.object(native_mean, "_assemble_mechanical_force", force))
     stack.enter_context(patch.object(native_mean, "_tangent_chunked", tangent))
     stack.enter_context(patch.object(native_mean, "_tangent", forbidden))
@@ -307,7 +316,8 @@
         global ACTIVE
         ACTIVE = dict(series=role, chain=chain, source_role=options.pop("source_role", "zero_start"), first_force=None)
         try:
-            value = native_mean.solve_native_mean(source, task, None, **options)
+            targets = task["path"]["targets_mm"] if options.get("saved_result") is None else None
+            value = native_mean.solve_native_mean(source, task, targets, **options)
             saved = self.write_cached(value, output)
             observed = ACTIVE
         finally:
@@ -567,6 +577,8 @@
         self.assertEqual(warm["u_lift"].tobytes(), state.lift.tobytes())
         self.assertEqual(warm["u_fluctuation"].tobytes(), state.fluctuation.tobytes())
         self.assertEqual(np.float64(warm["R_input"]).tobytes(), np.float64(old["R_input"]+1.).tobytes())
+        self.assertEqual(CALLS["native_entry_started"], 6)
+        self.assertEqual(CALLS["native_entry_completed"], 6)
         self.assertEqual(CALLS["real_solver_invocations"], 6)
         self.assertEqual(CALLS["real_solver_completed"], 6)
         self.assertEqual(CALLS["linear_controller_paths"], 2)
@@ -630,6 +642,7 @@
             RESULT = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=ProgressResult).run(
                 unittest.defaultTestLoader.loadTestsFromTestCase(FirstUnloadTests))
         success = (RESULT.wasSuccessful() and RESULT.testsRun == 8 and not RESULT.skipped
+            and CALLS["native_entry_started"] == CALLS["native_entry_completed"] == 6
             and CALLS["real_solver_invocations"] == CALLS["real_solver_completed"] == 6
             and CALLS["linear_controller_paths"] == 2 and CALLS["HP_calls"] == CALLS["JIT_calls"] == 0
             and not STOP_FILE.exists() and perf_counter()-STARTED <= TIME_LIMIT)
```
