# Saved workpiece nodal-force card: static readiness

Status: **ready for the declared sequential execution; no blocking bug found**. This review did not run the builder, pytest, observation, rendering, force/tangent kernels, solver or HP reference. At inspection, `square009_001` did not exist.

Reviewed final author sources:

| File | Lines | SHA256 |
|---|---:|---|
| build_nodal_card.py | 104 | e50353ec3e7824b75a7a1b60a7efeb2c08c988e109b5d8b4c127508e13232774 |
| tests_once.py | 42 | 74c5a0dccf429bd0b5a826789108348b7c3d4efd129baae0b93ccef49be12b0c |

Both sources passed AST parsing and `compile` without execution. The builder's actual HEAD prerequisite matches `3f0418490b3994ad0ef7c2881bc005d237cff8e1`. It copies the existing launcher bytes. For the planned layout `ROOT/functional_views/native_workpiece_nodal_20261004/square009_001`, the test worker's `STAGE.parents[2]` and launcher's `Path(__file__).parents[3]` both resolve to the formal Git root.

The passing prior region protocol supplies 654 preserved science/reference bindings. The builder rechecks those hashes and the genuine cycle009 production/reference terminal receipts, nine declared targets, nine accepted indexes and 18 completed fresh HP calls; it only reads their saved files. Its observation and render argv use the same result and reference summary. No force, tangent, solver or reference evaluation is added, and the old physical/HP gates are not overridden.

The installed analytic test source is the unchanged 122-line `6e6f3265699aa0a60105516dd94530eeb40ee9dc3223ebfd4981604bf89360b0`: four test functions / five parameter cases. The installed pure API source is `697e056fee1bddf4a611f2fc6e83de10747d923627b5f2d28c34eaf9a1d33ae9`. The test worker names only this test file, uses `-x` and disables the cache provider; its JUnit output will provide the actual count. There is no test-tree conftest, and the explicit import closure accepts only `hf_eval`, `workpiece_nodal`, and `boundary_geometry`. The worker does not claim hooked numerical-call telemetry: zero is based on literal cached vectors and this pure source/import closure.

Saved model metadata confirms **153 body nodes × nine actual states = 1377 CSV rows**. All body IDs are retained in source order, including interior and physical/cut shared nodes; initial zero and returned zero remain separate accepted indexes. The downstream CLI checks the saved state identities, complete global vectors, fixed body, original three cached body resultants, holding sign and disjoint partition. Its `8eps*sumabs` bound concerns the rounding of group sums only, not a replacement physical or HP tolerance. Moments use the explicit task center `(70,40) mm`; they and nodal forces remain derived weak-form observations, not pressure, face forces or clamping qualification.

Each of the **tests → observe → render** phases has helper **120 s**, outer **150 s**, sampled tree RSS **8 GiB**, and one invocation. Test failure returns a nonzero exit and `-x` stops further cases; observer/renderer failures preserve their failed output, and the reused launcher rejects a nonzero exit or resource stop. Sequential predecessor checking and closing the whole card on the first formal failure are the root executor's contract: the generic launcher itself has no cross-phase predecessor lock. Therefore the executor must inspect each real terminal result and must not launch a later phase after any failure. This is the planned execution and needs no new defensive framework or launcher change.

The stage uses fresh exclusive destinations and source snapshots, including this readiness note. All required author readiness files were present except this note before its creation. The builder does not launch any phase. No repair, retry, force termination, source promotion or new qualification occurred in this static review.
