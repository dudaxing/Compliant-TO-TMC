# L-CTIPSTEP1 independent requirements audit

This is a source and ordinary-metadata review, not an execution or a final byte-bound candidate approval. The user explicitly authorized this stage on 2026-10-19. No new approval is required for the specified work.

## Required numerical operation

Use the installed public `evaluate_native` exactly once with an explicit new task, the parent result `lf_circle_tip_pilot_001/run_001/wave_circle_tip_pilot/result.json`, selected accepted index 2, and `extend_path=True`. Prefer `geometry_path=None` so the installed interface inherits the parent's original source-geometry snapshot. The complete new task is `[0, 0.25, 0.50, 0.75]` mm; the actual child suffix is `[0.50, 0.75]` mm. Do not replay the original zero-start prefix.

The selected anchor has global target index 2, semantic split-state SHA256 `c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392`, and signed actuator reaction 0.08602790333542189 N. Its raw state archive SHA256 is `38c7eaedf7b356a5a699742cb9f9c529310db1348425b14f5f9d67db8fabf06a`; its ordinary state descriptor file SHA256 is `4b7594a039018e8cf8e7801cad072a9cd2a89820f7fb75e0ac6e40a02a4131b4`. These are three different identities and must not be interchanged.

## Installed interface findings

- `native_resume._extension_targets` requires a successful completed terminal original source target and an exact retained full task prefix. For a load-only extension, only the appended targets, declared input peak, and four explanatory metadata fields may change.
- `saved_resume_defaults` inherits the original geometry, options, and all settings except the new explicit controller time limit. `read_native_resume` independently compares geometry, grid, material, region and boundary metadata, options, settings, force/tangent source identities, and ordinary parent/selected-state descriptors.
- The saved-state reader decodes only the selected archive's `lift` and `fluctuation`, verifies raw and field hashes, checks semantic split hash, zero lift, and fixed fluctuations. It does not read old force, tangent, or matrix payloads. Model reconstruction reads the original four source-geometry authority masks.
- `solve_native_mean` passes this original split state and signed reaction into the original controller with a fresh force and tangent. A nonconverged saved anchor raises a typed anchor failure rather than repairing it. A successful child first state must preserve the split-state SHA and exact binary64 signed reaction.
- Child global original indices are the source global index plus child-local original indices. Bisection can add accepted states. Do not assume that the number of accepted states or GIF frames is exactly two.
- A successful suffix does not execute the whole original or extended path. Preserve `task_target_executed=False`, `full_original_path_completed=False`, `full_extended_path_completed=False`, `target_response=None`, and the parent's historical success. New success is represented by `new_peak_reached`, `extended_segment_completed`, and the requested endpoint response.

## Invariant physics and gates

Retain the circle radius 9 mm, center (80,40) mm, right domain boundary 92 mm, regularization length 80 mm, half-model grid 184 by 80 at 0.5 mm spacing, thickness 20 mm, E=1 MPa, nu=0.3, plane strain, gamma=1e-6, alpha=5e-7, and every material/boundary/port task field. The saved parent has 14720 cells and 29970 DOFs. The upper background symmetry condition applies through x=92 mm; free right-boundary components remain unchanged.

Retain relative residual 1e-9, original average-constraint coefficient 1e-10 with the original displacement scaling, relative global force balance 1e-6, fixed split displacement limit 8e-11 mm, and positive saved J. Retain mechanical response, chunk256 tangent, port_projection initialization, checks 25, backtracks 12, bisections 4, and minimum increment 0.00625 mm.

## Resources, reads and display

One controller 1800 s, shared display 600 s, helper 2700 s, outer 2760 s; sampled tree 64 GiB; four library thread caps 16 before numerical imports; original pure viewer 8 GiB cap. First terminal error stops later science/display. No tests, HP, default installation, external retry, repair rerun, force, budget extension, rollback or deletion.

Before execution, scientific payloads may be checked only by original producer seals plus stat. Inside the unique helper, the old source-geometry NPZ and selected original split-state NPZ are the necessary old payloads. Never decode old model, forces, tangents, matrices or media. The pure viewer observes only the new saved result: 1+2N NPZ archives and 27+18N fields, actual N accepted states. Produce four viewer PNGs plus one convergence PNG and an actual N-frame GIF. Each new PNG is available for at most one root pixel inspection; no GIF decode is needed after closure.

The unique reference tip is selected by (80,30) mm and verified solid/output membership, not by an inherited numeric node ID. Right-medium observations cover the fixed reference x=89..92 mm six-column, 80-row, 480-cell strip. Keep actual split displacement distinct from displayed coordinate subtraction; cellwise Hu is not nine independent samples. Report global-boundary and tip unsigned distances, their witnesses and exact ties, J/Green/Hu/displacement extrema with locations, signed material/Hu/total weak body resultants, and actual convergence events. Geometric separation and these weak forces do not earn pressure or effective-grip qualification.

## Review method

Read current `native_evaluate.py`, `native_resume.py`, `native_mean.py`, relevant `split_displacement.py` and `native_response.py`, ordinary parent result/protocol, and prior load-only extension source. The previous `lf_circle_extension_001` wrapper is the correct first-extension contract template; the subsequent `lf_circle_step_001` has a different already-extended parent and must not be copied without adapting its parent flags and indices. No scientific payload or media was opened or hashed during this audit.

Final candidate source, protocol, authorization and frozen byte binding remain to be reviewed once root assembly is ready.
