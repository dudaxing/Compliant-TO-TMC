# HF4-C1 evidence

**Current outcome (2026-09-20): all ten selected paths passed the explicitly amended 80/120-digit audit: 80 formal states and 2516 state gates.** The original aborted run retains a separately validated four-state prefix and remains `not_pass`; it is not an eleventh admitted path. Related tests: 173 passed. Start with the [final report](../docs/HF4_C1_FINAL_REPORT.md), [final summary](summary_v2/summary.json) and [independent final review](independent_final_review.json).

The original initialization failure, original 50/80-digit not-pass audits, [activation diagnosis](activation_diagnostic.json), [precision diagnosis](precision_diagnostic_v1.json), [execution amendment](execution_amendment_v1.json), [precision amendment](../hf_repo/configs/contact_c1_precision_r2.json), explicit [path selection](selection_v1.json), and superseded `summary_v1` are preserved. `summary_v2` fixes only undefined relative differences against the nominal zero-force reference and the corresponding plot presentation; raw forces are unchanged.

Numerical admission is not general contact validation. TMC has signed local nodal reactions, and net-force agreement does not establish unilateral local contact. See the final report before choosing new experiments.

The completed [local reaction diagnosis](local_reaction_diagnostic.json) and [plot](local_reaction_diagnostic.png) read four saved TMC endpoints without new FE: 18 negative nodes are outside the initial solid x-span, a reference-position classification only. Material and regularization contributions and positive/negative sums are retained. The `local_reaction_diagnostic_pre_plot.json` file is an intermediate visualization draft with the same case values; use the final diagnostic and its matching script hash.

This directory contains new matched positive-gap contact experiments. The frozen protocol is [contact_c1_v1.json](../hf_repo/configs/contact_c1_v1.json); its scope and rationale are in [HF4_C1_PROTOCOL.md](../docs/HF4_C1_PROTOCOL.md).

Prospective order: A0 and TMC uniform paths at h=0.25 and 0.125 mm; only after all four independent audits pass, A0/Aalpha/TMC perturbation paths at both meshes. Aalpha uses the corresponding A0 preload as a cross-model warm start and must re-equilibrate. Stop dependent work on failure. Ten paths are a maximum, not a promised pass count.

Each run contains run metadata and completion bindings, a `stages/index.json`, and stage directories with their own model, explicit two-array initial state, accepted-state inventory, full controller result and completion bindings. Source inheritance uses relative paths. Local stage parameter is **not always physical mean displacement**: closed-stage d is additional compression above the 0.25 mm gap; perturbation d is zero-mean amplitude about a fixed 0.375 mm preload.

The `*.solve.log` / `*.audit.log` files and immutable receipts record external process budgets and failures. `audit.json` is authoritative only when its bound inputs still match. Do not count a solver success as independent numerical or physical admission. A failed run may contain an independently valid prefix without being an admitted path.

Reproduction uses the independent HF environment and scripts under `../hf_repo/scripts/`. The current solver entry is `run_contact_c1_r2_isolated.py --action solve --run <new-evidence-directory> --kind A0 --h 0.25 --mode uniform`. Current audit entry is `audit_contact_c1_isolated.py --run <same-directory> --precision-amendment <hf_repo/configs/contact_c1_precision_r2.json>`. Use absolute script/input paths when working outside the clone. Existing directories are never overwritten. Perturbation also requires `--mode perturbation --preload-run <matching-audited-uniform-run>` and the documented four-path admission decision. No LF directory or research ZIP is a runtime dependency.

To verify saved data without a new FE solve, use `audit_contact_c1.py --run <saved-run> --output <new-audit-json> --precision-amendment <precision-amendment-json>`. Omitting the amendment intentionally reproduces the original 50/80 policy and its recorded near-zero reference precision failure. Preserve the complete relative bundle, including sibling preload runs, source files, and configs. The original machine directory is not needed; splitting the source and evidence across Windows drives is outside this relative-path contract.

Final plots: [force comparison](summary_v2/c1_force_comparison.png), [precision and components](summary_v2/c1_precision_and_components.png), [deformation](summary_v2/c1_last_accepted_deformation.png). SVG versions are alongside the PNGs. The plots use rounded coordinates only for display; exact geometry checks do not.

Status at protocol creation: implementation/preflight only; no C1 FE paths executed. Later results and decisions must be recorded separately without rewriting failed raw evidence.
