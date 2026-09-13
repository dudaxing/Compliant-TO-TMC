# HF-1 measured validation

Status: completed on 2026-09-13. This release demonstrates portable geometry input and an independent solid-only, small-strain linear diagnostic. Nonlinear material response, third-medium contact, mesh convergence and final research performance have not been validated.

## Reproducible evidence

`validation/hf1/` contains the final JUnit test report, detached-run receipt and audit, and the three result directories A1 (inverter), B (gripper), A2 (inverter). Each result includes JSON, displacement/strain/stress and mesh arrays, plots and plotting metadata. Paths captured in those records document the original execution; the evaluator does not follow them when reading new data. The separate geometry dataset contains its own input manifest and source-to-import comparison evidence.

The complete test suite passed **88 tests**, with **one skipped**. The skipped test requires creating a real symbolic link, which this Windows account could not create (WinError 1314). The corresponding reader guard exists, but that operating-system operation was not exercised. No other tests failed or were skipped.

Tests use independent synthetic fixtures: binary and partition invariants, file and descriptor hashes, physical coordinates and identity, nonuniform/asymmetric examples, port weights, attachment and diagonal connectivity; rigid modes, affine strain stress/energy, analytical generalized constraints and springs, reaction signs; failure serialization and repeat-call behavior. They need neither the supplied dataset nor LF files. These are verification of this limited implementation, not measurements of contact fidelity.

## Diagnostic settings and results

The supplied pilots use Q1 plane strain, 2×2 Gauss integration, E = 1 MPa, ν = 0.3, thickness = 20 mm and mean input displacement +1e−6 mm along +x. There is no input spring, output spring, third medium or workpiece. Only solid cells and solid-incident support/symmetry nodes participate. A single Lagrange multiplier enforces the weighted port mean; it does not tie all port-node displacements together.

| Measured quantity | Inverter (A1) | Gripper (B) |
|---|---:|---:|
| Solid cells / area (mm²) | 1128 / 1128 | 1086 / 1086 |
| Active nodes | 1351 | 1337 |
| Design-region solid fraction | 0.3525 | 0.3533783784 |
| Weighted output displacement (mm) | 1.6021813118562742e−6 | 1.144145163539476e−6 |
| Input actuator force on modeled structure (N) | 1.6963023023863184e−7 | 2.0807466745143412e−7 |
| Normalized free-force residual | 1.5461712937e−14 | 1.1635582363e−14 |
| Absolute mean-input constraint error (mm) | 5.9292306308e−21 | 1.9905274260e−20 |

These are lower-half-model values. Inverter positive output points toward −x; gripper positive output points toward +y and represents the displacement of one modeled jaw. No implicit factor of two is applied to displacement or force. Plots explicitly state their display amplification. Force residual normalization uses the maximum of force terms and the nonzero E·t·d scale; the tolerance is 1e−9. Constraint tolerance is 1e−10 times max(|d|, 1e−6 mm).

Both geometries pass the measured connectivity and port-attachment checks, but overall geometry qualification remains `pending`: research volume thresholds are unset and a validated minimum-feature measurement is not implemented. Functionality is `not_assessed`. The diagnostic values must not be treated as nonlinear HF truth or used to claim a validated research ranking.

## Detached acceptance

A new temporary root received only the independent HF repository and the finalized data package. A new virtual environment installed the 12 pinned runtime distributions and the built HF wheel. The acceptance helper ran with Python 3.13.6 in isolated mode (`-I`), with no global/user site-packages, from a third working directory outside the copied repository.

The helper prohibited Python-level access to the original workspace and original source-material locations and blocked LF package imports. All 12 recorded checks passed: three packages readable, all three solves successful, A–B–A arrays bitwise equal, corresponding physical metrics equal, fresh evaluation IDs, isolated Python, no LF distribution/import, no forbidden source paths/access, no global site-packages, and all solves within the 300 s budget. All 395 dataset files were unchanged. This was an application-level access audit, not an operating-system sandbox; originals remained on the host and were not copied into the detached environment.

The three numerical analyses took approximately 0.0195 s, 0.0112 s and 0.0135 s. The full acceptance subprocess, including imports, inspections and plotting, took 22.887 s. These measurements are a small CPU diagnostic, not a GPU/JAX performance benchmark. Peak memory was not measured; the planned 4 GiB soft budget was not instrumented.

- Tested wheel SHA-256: `f46d09d24f49a27c0f7c69567cf5c4cf877ade47cbdb989e0f8f14f262e3b52f`.
- Runtime source-tree SHA-256 recorded by the evaluator: `4f2499dbcc571210329e47d30fa7dee066c2838a89138e853486c1072e42485f`.
- The final release integrity receipt confirms that all seven packaged Python source files match the tested wheel. Documentation was finalized after the numerical run. Git preserves exact file bytes via `.gitattributes` so a checkout does not silently alter recorded source hashes through line-ending conversion.

## Repeating the acceptance

Use the separately supplied `geometry_dataset`, with its `dataset_index.json`. Copy this repository and that data package to a new directory; create the independent environment and install the locked runtime and the wheel as described in the README. Choose an empty output path. For example, from an unrelated working directory:

```powershell
& 'C:\hf-copy\.venv\Scripts\python.exe' -I 'C:\hf-copy\hf_repo\scripts\run_isolated.py' --dataset 'C:\hf-copy\geometry_dataset' --output 'C:\hf-copy\acceptance' --forbid 'D:\original-workspace'
```

Replace the example paths with real locations. At least one nonempty `--forbid` is required; add it again for other original source locations. The helper calls the installed public API in one process so that A–B–A can expose leaked state. Normal use also has `python -m hf_eval inspect` and `evaluate` CLI commands. Dependencies can be installed from a compatible predownloaded wheelhouse; the evaluator itself makes no network requests. The final helper adds this argument guard to prevent vacuous acceptance; the recorded run already supplied all original source locations.
