# HF-2 arithmetic repair in version 0.2.1

Version 0.2.1 keeps the source-numeric C-shape model and replaces the material-force evaluation with the equivalent direct first Piola form. It avoids cancellation in det(F.T @ F), including in the auxiliary second Piola output. The actual residual still contains the full nonconservative HuHu contribution and is differentiated without symmetrization.

The generic Newton tolerance remains 1e-8. The explicit `hf2_precision_v2` C-shape profile uses an internal 1e-9 stopping tolerance; independent external equilibrium still requires 1e-8. The kernel ID is `p26_q1_direct_piola_huhu_v2`. Each new path archives its actual primitive operators and material coefficients, full internal forces, reactions, J and material energies. Linear-solve backward errors are diagnostic and do not change the acceptance algorithm.

## Evidence and interpretation

The repair first passed 199 regression tests (one pre-existing Windows symlink-permission skip), all 976 original small-reference checks, and all 192 frozen strong-state checks. The strong-state checks use the actual binary64 primitive inputs, two predefined directions and five domain-bounded perturbations. Independent Decimal arithmetic starts at the input displacement and operators, not at precomputed float64 F or J.

The strongest observed force-evaluation error in the three archived states is 1.175e-11 times the external-force norm, below the 1e-9 budget. Material, regularization and total Jacobian actions are checked separately; the largest relative directional error is 7.786e-12. Both ideal Decimal differences and actual rounded binary64 differences are retained. The finest binary64 step can be worse because of roundoff; the predefined best-of-five criterion was not changed.

The corrected path completed 100 original targets without bisection. Its 100 states passed independent 50-digit equilibrium and evaluation-error checks: maximum normalized residual 9.6983e-10 and maximum full-force evaluation error 3.5467e-11. All 300 new/historical states were audited, all three 50/80-digit crosschecks passed, and the installed wheel passed 24 detached checks with the 395 dataset files unchanged. Consult the packaged `hf2_repair_results/release_integrity.json` and stage report for the combined decision; the production solver's own `success` is not the independent verdict.

The first offline audit stopped at its internal deadline after 299 states. A prospective resource amendment allowed one bounded continuation while preserving the frozen scientific specification and total numerical budget. It inherited 290 complete raw states, recomputed the final ten MATLAB states, and required exact agreement with the nine existing rows except for timing. The initial timeout and a pre-child Windows executable-path launch failure remain in the evidence. Neither was a repeated nonlinear solve.

The old 0.2.0 states and wheel are retained. Three previously identified old states (Python .73, MATLAB .76/.99) remain failures under strict equilibrium. Recomputing an old displacement more accurately does not solve it. Source-response agreement and the corrected evaluator's equilibrium certification are separate from the old MATLAB path's own balance status. The unchanged legacy comparison can therefore retain `not_pass` while a corrected evaluator passes its own independent certification.

## Portable inputs and tools

- `validation/hf2_repair/precision_spec.json`: numerical requirements frozen before new calculations.
- `validation/hf2_repair/strong_inputs.npz`: exact primitive arrays and three fixed states; no source code or object arrays.
- `scripts/hf2_precision_reference.py`: independent Decimal residual and analytic directional derivative.
- `scripts/validate_hf2_precision.py`: bounded fixed-state precision/derivative gate.
- `scripts/validate_hf2_repaired_path.py`: whole-path certification and separate historical audits, using only ordinary arrays.
- `scripts/resume_hf2_repaired_path.py`: content-bound recovery of the preserved incomplete audit, without changing scientific criteria.
- `scripts/run_hf2_repair_isolated.py`: new installed-wheel replay with explicit original-workspace/LF/MATLAB access denial.
- `validation/hf2_repair/records/`: compact release evidence; full arrays are in the release ZIP.

The standalone precision reference is a development verification tool, not a new runtime dependency. No MATLAB engine, LF generator or original archive is needed by the package or the new validators. The release includes the old and corrected ordinary paths for offline comparison. It does not establish physical contact accuracy, mesh convergence, stability, material calibration or actual mechanism performance. HF-3 was not executed as part of this repair.
