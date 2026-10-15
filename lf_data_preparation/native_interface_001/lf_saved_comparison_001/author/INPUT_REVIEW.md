# L-COMP1 precise ordinary-input preparation review

2026-10-15 (Asia/Seoul). Status: pass_input_source_review_only. No blocking findings. This is static ordinary JSON/source preparation, not execution of L-COMP1, its tests, mechanics, HP or plots. No scientific arrays or media were read.

## Minimal runtime input set

24 ordinary JSON files suffice for the planned provenance-complete comparison: composed_path (1), M original results/models/view summaries (15), LF table/view summary/original result/model (4), and the three M plus one LF reference summaries (4). The companion path_index is reviewed and pinned too, making 25 files if retained by the candidate as the plan requests. It duplicates the raw/unique/alias mapping already present in composed_path and is optional for a direct implementation. No separate task files, state descriptors, view descriptors, CSV, arrays, prior PNG/GIF contents or current mechanics imports are needed.

| Role | Ordinary JSON path |
|---|---|
| M canonical composed observations and raw/source/alias ledger | `functional_views/native_alpha_composed_20261013/complete_001/run_001/composed_path.json` |
| Optional companion M explicit path index; redundant if composed source_occurrences used directly | `functional_views/native_alpha_composed_20261013/complete_001/run_001/path_index.json` |
| LF L-USE1 25 original numeric rows and reference/physics identity | `lf_data_preparation/native_interface_001/lf_saved_consumer_001/run_001/states_table.json` |
| LF saved scalar geometry and phase field observations | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/view/lf_fine_forward/summary.json` |
| LF original result status/settings/source versions and accepted identities | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/result.json` |
| LF model task/material/grid/ports/support and region contract | `lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/model/model.json` |
| M-ALPHA1 original result status/settings/version/child states | `lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json` |
| M-ALPHA1 original model/task/grid/material/region ports | `lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/model/model.json` |
| M-ALPHA1 original saved scalar observations | `functional_views/native_alpha_partial_20261011/complete_001/run_001/view/alpha_half/summary.json` |
| M-RESUME1 original result status/settings/version/child states | `lf_data_preparation/native_interface_001/saved_continuation_001/run_001/resumed_alpha_half/result.json` |
| M-RESUME1 original model/task/grid/material/region ports | `lf_data_preparation/native_interface_001/saved_continuation_001/run_001/resumed_alpha_half/model/model.json` |
| M-RESUME1 original saved scalar observations | `lf_data_preparation/native_interface_001/saved_continuation_001/run_001/view/resumed_alpha_half/summary.json` |
| M-EXTEND2 original result status/settings/version/child states | `lf_data_preparation/native_interface_001/saved_extension_002/run_001/extended_alpha_half/result.json` |
| M-EXTEND2 original model/task/grid/material/region ports | `lf_data_preparation/native_interface_001/saved_extension_002/run_001/extended_alpha_half/model/model.json` |
| M-EXTEND2 original saved scalar observations | `lf_data_preparation/native_interface_001/saved_extension_002/run_001/view/extended_alpha_half/summary.json` |
| M-UNLOAD1 original result status/settings/version/child states | `lf_data_preparation/native_interface_001/saved_extension_003/run_001/unloaded_alpha_half/result.json` |
| M-UNLOAD1 original model/task/grid/material/region ports | `lf_data_preparation/native_interface_001/saved_extension_003/run_001/unloaded_alpha_half/model/model.json` |
| M-UNLOAD1 original saved scalar observations | `lf_data_preparation/native_interface_001/saved_extension_003/run_001/view/unloaded_alpha_half/summary.json` |
| M-UNLOAD2 original result status/settings/version/child states | `lf_data_preparation/native_interface_001/saved_extension_004/run_001/unloaded_alpha_half/result.json` |
| M-UNLOAD2 original model/task/grid/material/region ports | `lf_data_preparation/native_interface_001/saved_extension_004/run_001/unloaded_alpha_half/model/model.json` |
| M-UNLOAD2 original saved scalar observations | `lf_data_preparation/native_interface_001/saved_extension_004/run_001/view/unloaded_alpha_half/summary.json` |
| M-AREF1 original already-completed selected reference summary; no HP recomputation | `lf_data_preparation/native_interface_001/alpha_reference_001/run_001/reference/summary.json` |
| M-EREF1 original already-completed selected reference summary; no HP recomputation | `lf_data_preparation/native_interface_001/extension_reference_001/run_001/reference/summary.json` |
| M-PREF1 original already-completed selected reference summary; no HP recomputation | `lf_data_preparation/native_interface_001/unload_reference_001/run_001/reference/summary.json` |
| L-REF1 original already-completed selected reference summary; no HP recomputation | `lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference/summary.json` |

## Actual structure and exact fields

M composed_path has sources, raw_rows, unique_rows and anchor_join_ledger. Its 29 raw rows retain source.segment/result/accepted_index, result_state and observations. Each unique row has unique_index and source_occurrences containing raw row numbers; it is not a list of source records. There are 25 unique rows and four boundary joins. The current five raw result/summary payloads match those stored rows and all 25 canonical targets/legs match LF. Origin and return-to-zero are separate, as are equal d on different legs.

M values come from unique_rows[i].result_state and its exact source result state; M saved observations come from unique_rows[i].observations plus the exact original viewer row. LF numeric fields come from states_table.rows[i] and phase/geometry observations from LF viewer.rows[i]. Original R_input maps to R_input_N, d to d_mm, q_in/q_out to their mm names. Material, regularization and total remain full signed two-component lower-body weak-force vectors. Global minimum_J is retained separately from solid_min_J and medium_min_J.

Use bottom_first_ray_mm for both new distance curves. It is the analytic first outward boundary hit over the finite bottom face, not a pressure, arbitrary nearest distance, node-window clearance or signed penetration. tip_to_bottom_mm is a different point-to-segment quantity even when peak values coincide. Free-medium min J excludes the fixed body overlay, as the existing viewer source does. Existing solid Green principal bounds remain saved binary64 observations, not new strain computation or qualification.

## Common contract and retained differences

The six original model JSON files have equal grid, material, model_extent and full region_metadata.ports. The latter is the exact metadata authority for directions, node sets, nonzero DOFs, weights and averaging; task.input.control alone is insufficient. Input runs along x+ over (0,38)-(0,40); output along y+ over (80,28)-(80,30). Both have five nodes and weights [0.125,0.25,0.25,0.25,0.125], averaging normalized_reference_arclength_trapezoid. Task input is average_displacement and output spring is zero.

The declared support/entity-symmetry/background-symmetry points, components and selection rules agree. Effective attached nodes/counts are geometry-specific: M has 4344 solid cells and 1548 fixed DOFs; LF has 4358 and 1546. Do not require the full region_metadata or all fixed-DOF sets to be identical across designs. All non-clock settings agree; only time_limit_seconds differs (LF 18000; M 9000/1800/1800/1800/9000). Task paths grow by segments, and task/geometry hashes are not equality criteria across designs.

M-ALPHA1 remains failed/time_limit, with 14 accepted loading observations. Subsequent segments remain their actual source successes, not a rewritten single-path producer PASS. M-ALPHA1 and M-RESUME1 have earlier recorded source hashes; M-EXTEND2/UNLOAD1/UNLOAD2 share the four relevant mechanics hashes with LF. Never label all 50 observations same-code or a one-factor experiment. Source model byte pins also change with task extensions while the physical contract remains the same.

## Reference-source binding

| Summary | Exact source child | Display global | Source leg | Alias restriction |
|---|---|---:|---|---|
| M-AREF1 | M-RESUME1:0 | 13 | resume_origin | Displayed ALPHA loading anchor only; source is RESUME resume_origin and does not transfer qualification |
| M-AREF1 | M-RESUME1:1 | 14 | unloading | Only the exact source result/state, not the whole path |
| M-EREF1 | M-EXTEND2:1 | 15 | unloading | Only the exact source result/state, not the whole path |
| M-PREF1 | M-UNLOAD2:2 | 18 | unloading | Only the exact source result/state, not the whole path |
| M-PREF1 | M-UNLOAD2:3 | 19 | unloading | Only the exact source result/state, not the whole path |
| L-REF1 | L-FWD1:13 | 13 | loading | Only the exact source result/state, not the whole path |
| L-REF1 | L-FWD1:16 | 16 | unloading | Only the exact source result/state, not the whole path |

M-PREF1 is later than M-PATH1 and therefore absent from its original reference_coverage. Its summary result_sha256 binds M-UNLOAD2; states[].index is child 2/3, while original_target_index and reference_execution_index are 18/19. Match child identity first, then map the source raw row to unique global position.

M-AREF1 child0 is resume_origin at 1.20 and matches the ALPHA global13 physical state SHA. That is a display alias, not ALPHA source-result HP qualification; do not demand the displayed loading leg equal the source resume_origin leg and do not rewrite either. Child1/global14 and EREF child1/global15 have exact canonical source identity. LF existing matched reference remains only 13/16. All original full-path/all-columns/pressure/clamp/HF5 qualifications stay unchanged. This preparation performed zero new HP or reference-source scientific byte verification.

Existing media can be linked from M sources[].gif.repo_relative_path and LF table.existing_media. Those are historical declarations only in this review; no new media-byte or pixel verification is claimed. Complete deformed mechanism coordinates are not present in these ordinary payloads, so the two proposed scalar PNGs must use old deformation links instead of rebuilding snapshots.

Exact 25 input SHA/byte bindings, source versions, port contract, selected reference aliases and field map are in input_review.json. Execution remains pending its own fixed candidate and direct authorization.

## Candidate wrapper source-only supplement

Current candidate source and specification were read and four Python ASTs parsed; no module was imported and no test or candidate call was executed. The current comparison_spec has exactly the same 25 ordinary input paths/pins reviewed above, so this candidate retains the optional path_index. The card's geometry declarations are carried by these model JSON payloads; no geometry arrays are read.

The helper checks authorization before tests/comparison and the launcher reads the direct-authorization record and protocol identity before creating a cwd/log/receipt or spawning its only helper. Missing authorization therefore cannot start tests, comparison or plots. The launcher compares actual HEAD to auth.authorized_execution_source_commit; it does not force the inherited 5b84495 baseline as execution HEAD. The eventual recorder must bind the actual published candidate commit and direct human reply; no such authorization or successful publication is inferred here.

The helper runs one failfast suite containing exactly three prepared metadata methods. Started/finished method counters are updated per actual method and retained even if a resource checkpoint interrupts the suite; successful-suite count is separate. It then makes exactly one example.main call. The renderer uses existing scalar observations only and imports Matplotlib at rendering. Current source declares exactly the two prescribed PNG outputs, separate phase-J and bottom_first_ray_mm, and the frozen source-aware reference-alias rule. This is static control-flow evidence, not three passed tests or two produced plots.

Clocks start at entry. Helper 180 s, outer 240 s and sampled tree 1 GiB are cooperative checkpoint/sampling contracts. Before/after ordinary input/source binding checks are included in that window. seal reads only the four new outputs (including new PNG raw bytes) inside the helper window; no old media bytes are opened. A first terminal error stops subsequent work, preserves partial output and permits only a partial seal while the original helper window remains open and no stop was requested. The outer requests cooperative stop and waits for the original child; no force, retry, repair rerun, rollback or deletion occurs. Actual receipts and pixels remain future evidence.

## Final whole-candidate static review

The current example main/compare/contract/reference/renderer/Markdown and metadata suite, helper and launcher have now been reviewed together against the real ordinary input structure. All required accessed state/view/model/port and index-alias fields exist. The spec retains exactly the 25 reviewed input identities. Runtime example JSON events therefore cover one spec plus 25 cached inputs (26), while helper binding SHA byte reads and ordinary authorization/receipt reads are separately described. No source function, suite or renderer was run by this reviewer.

The reference code first checks each original summary's producer SHA and source child state/target/leg. M-AREF child0 keeps resume_origin; global13 keeps ALPHA loading and its recorded alias, with applies_to_primary_source=false. PREF child2/3 map through original target indices18/19; full original summary scope is preserved. The latest full M task defines the common full target list, while each earlier original task is checked as a chronological prefix before comparing its other fields and non-clock settings. Counts and complete original boundary attachments remain per-source records rather than forced cross-design equality.

The exact current plot source uses one fixed color per design, solid loading and dashed unloading, scalar values in original sample order and signed Hu on its own linear panel. The last real loading peak is reused only as the unloading display start, so the existing 1.20-to-1.15 interval appears; no saved row or pair is appended. Markdown explicitly explains this display reuse, the partial references, source-version difference and all link-only old media. Source has two named PNG iterations and one plot_started/plot_completed checkpoint pair per iteration. Actual 26 reads, 3 metadata methods, 1 comparison and 2 plot completions remain unexecuted expectations, not observations.

Static review has no blocking findings. Current source SHA map is recorded in input_review.json; root will freeze the final protocol and published execution-source identity afterward. If source changes after these hashes, this supplement does not silently cover the replacement. No production code, input, existing result or media was modified; only these two preparation-review documents were updated.
