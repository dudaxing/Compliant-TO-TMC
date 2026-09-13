# HF-2 validation scope and evidence

Final stage status: **partially complete**. Source path agreement passed; strict independent equilibrium did not pass at three states. Original tolerances and states are retained; no corrected full path has been run.

The 0.2.0 implementation adds the specified uploaded C-shape source-code benchmark. It does not establish independent contact accuracy, mesh independence, material calibration, stability or performance ranking. HF-1 geometry qualification and unit semantics remain unchanged. Numerical reports distinguish the frozen source agreement checks from additional arithmetic-sensitivity diagnostics.

## Fixed numerical model

Full domain 100×50, 62×30 Q1 cells, 828 solid and 1032 third-medium cells; all 3906 DOFs retained before fixing the left edge. Nine Gauss–Lobatto points per cell. E=100, nu=0.3, kv=1e−6, alpha=1e−6, thickness factor 1, six upper-edge nodal forces totaling −3. Units are `source_numeric`; no inferred mm/N or thickness correction. The package validates the ordinary exported source setup against its independent preset and preserves the source's 100 target multiplier values exactly.

The kernel uses float64 CPU JAX to differentiate the actual residual, retaining the deformation-dependent, nonsymmetric HuHu Jacobian. General sparse LU solves the Newton system. Invalid J and nonfinite values are rejected. Residual Armijo backtracking and bounded increment bisection save states accepted by the production binary64 residual criterion; failures retain the last state accepted by that criterion and null target metrics. Independent postprocessing can reject such a stored state, as documented below. This is a nonconservative regularized weak form, so no fabricated total-energy balance is used as a nonlinear acceptance criterion.

## Measured verification

- Complete regression: **185 passed, one skipped**. The skip remains the HF-1 Windows symbolic-link creation restriction. Tests include 16 independent direct-Piola postprocessor checks, as well as kernel, assembly, path, rollback, zero-load, port, setup and data guards. Full C-shape solves are excluded from pytest.
- Small MATLAB reference comparison: **16 cases, 976 checks and 160 finite-difference points passed**. Material and regularization residuals/tangents are checked separately; node/DOF/element permutations and sparse/dense assembly are explicit. All tolerance and case definitions were frozen before new mechanics runs in `validation/hf2/validation_spec.json`.
- MATLAB and Python each completed their single full C-shape attempt through all **100 targets to lambda=1**. Source MATLAB process wall time was 64.35 s; Python process wall time was 53.17 s. These different process scopes and solver strategies are not a speedup benchmark. Python's path computation took approximately 46.26 s including cold-kernel work and checkpoint callbacks; no bisections occurred.

| Maximum error over all 100 common targets | Measured | Frozen tolerance |
|---|---:|---:|
| Global displacement, relative | 7.95e−10 | 1e−5 |
| Twelve loaded-node displacement components, vector relative | 1.86e−10 | 1e−5 |
| Fixed-DOF reaction vector, relative | 2.71e−10 | 1e−4 |
| Solid material energy, relative | 3.50e−10 | 1e−4 |
| Third-medium material energy, relative | 3.48e−9 | 1e−4 |
| Full J field, relative | 1.42e−9 | 1e−5 |
| Minimum J, absolute | 7.22e−10 | 1e−6 |

The final minimum J is approximately 4.84743e−5. At this high compression, an additional independent direct-Piola residual recomputation exceeded 1e−8 at three stored states (Python lambda .73; MATLAB lambda .76 and .99), although the original solver residuals and every source-agreement quantity above passed. The original comparison output preserves those three flags. They are examined separately as arithmetic sensitivity and are not erased or used to relax tolerances. Consult the final stage report and sensitivity evidence before interpreting numerical convergence more broadly.

## Portable evidence

Fifty-digit Decimal evaluation of the three frozen discrete states confirms relative residuals 1.0644451e−8, 1.0751390e−8 and 1.0444353e−8. Cancellation in det(C) explains source-arithmetic sensitivity; it does not turn these failed states into passes.

Detached installed-wheel replay passed all 17 checks, including the 976 small-reference checks, HF-1 and TMC A–B–A, source setup agreement, and no LF/MATLAB access. All 395 input files were unchanged. After an online CDN timeout, exact locked versions were installed from the local uv cache; 4511 installed RECORD file hashes passed. The original third-party wheel archives were not reverified against the lock hashes during this offline replay. The HF wheel itself is hashed and its 10 Python files match the full-path source tree.

`validation/hf2/reference/cshape_setup.npz` contains ordinary reference data, not MATLAB code. The tiny numeric reference fixtures used by tests are in `tests/fixtures/hf2/`, protected by hashes. Original source files, MAT generation drivers, source archives and MATLAB installation are outside the HF repository. Compact verdicts and receipts are committed under `validation/hf2/records/`. The release ZIP additionally preserves `hf2_results/` and numeric `reference_validation/matlab/` paths, including full-path arrays, comparison details, arithmetic-sensitivity evidence and detached-run evidence. The ZIP's `EVIDENCE_README.md` identifies the replay inputs; full paths need no MATLAB process.

The first kernel-only monitor measured the Windows launcher and did not capture the child interpreter; that limited receipt is not peak-job memory evidence. Subsequent process-tree monitoring measured approximately 1.463 GiB for MATLAB C-shape and 323 MiB for Python C-shape. These are sampled working-set peaks, not an operating-system sandbox or guaranteed instantaneous maxima. The shared numerical budget includes failed setup work, compilation and independent replay; installation is counted separately.
