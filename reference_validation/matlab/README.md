# HF-2 MATLAB development references

This directory is external to the independent HF package. The eight files in `source/` are byte-identical copies of the supplied archive, retain the authors' notices, and are read-only. `source_manifest.json` records their source members and hashes. Neither source optimizers nor MATLAB are production runtime dependencies.

## Small reference result

`small_001/index.json` indexes 16 ordinary numerical NPZ files: two rectangular Q1 cells × three frozen nonaffine fields × two material multipliers, followed by four small meshes over the fixed 2 × 1 domain with field 0 and alternating canonical cell multipliers. `validation_spec.json` is the exact frozen specification. MAT files and unmodified source remain here; independent production tests use only copied JSON/NPZ.

The source global node order runs top to bottom inside successive x columns. Canonical nodes run x-fast from the bottom row. All source-to-canonical and inverse maps are explicit zero-based permutations, while raw `connectivity_source` and `dof_connectivity_source` retain MATLAB one-based indices. Source element corners already have physical BL, BR, TR, TL order. Mapping does not negate displacement components or reflect geometry. Canonical cell order is also x-fast, bottom to top.

The local residual/tangent are obtained by calling the unchanged source assembly and selecting its local corner DOFs. A one-element caller must explicitly supply an 8 × 1 displacement array, because the source solver's indexed transpose loses the intended shape for that special case. This is a calling-shape accommodation in the external reference driver; source functions are not patched. Material-only terms come from the original assembly with `kr=0`; regularization-only terms come from the original assembly with material multiplier zero. They are not computed by subtracting nearly equal totals.

F, J, second Piola stress and quadrature-weighted material energy are external mathematical postprocessing. The source assembly returns Kt/Fint only. The stored material energy includes physical integration weights; it is not the source's unused unweighted Psi sum. J and tensor outputs preserve an explicit element axis even for one cell.

`wrapper_equivalence.npz/json` compares the source two-increment solve against repeated source calls at precisely the same two targets, carrying the previous U. Both final arrays are bitwise identical (zero difference), and the final relative free residual is 1.276471934199801e-10. Source graphics are still called, with figures invisible. There is no persistent numerical state in `solveIncrIter` beyond U; its iteration counter and target construction restart locally. This small check supports the checkpoint wrapper, not the full nonlinear C-shape result by itself.

## C-shape setup and path

`setup_002/cshape_setup.npz/json` preserves the source-generated physical setup and exact 100 MATLAB `linspace` targets. The external helper evaluates verbatim the setup block of `cshapeTMC.m` between its setup/analysis markers. No solve is performed by the setup driver. It contains 1,860 cells: 828 solid and 1,032 third-medium cells; 62 fixed DOFs; six loaded nodes with total Fy = -3 in source numeric units. Canonical loaded node IDs are 1945 through 1950.

`setup_001` is an intentionally retained failed development attempt: MATLAB's static handling of eval-defined names `fix` and `alpha` selected built-ins. The external helper now predeclares these two variables before evaluating the unchanged setup substring. The failure did not execute a nonlinear solve and did not change source files.

`generate_cshape_reference.m` runs each original target through unchanged `solveIncrIter`, carries accepted U, and checkpoints each result. It checks real/finite displacement, positive finite J, the frozen relative free-residual criterion, fixed displacements and global force balance. Failure stops the original-source reference without parameter changes or a restart. Original solver console text is captured even when it throws. `convert_cshape_reference.py` only permutes and serializes accepted numerical states; it never solves or repairs them.

Original source timings cannot separate internal assembly from sparse solves without instrumentation. The reference reports the combined source solver time (including its original invisible plotting), plus independent postprocessing time and outer process wall time. No local-kernel speedup claim follows from those timings.

## Resources and reproducibility

`run_reference.py` launches MATLAB R2023b as a hidden process, samples process-tree RSS every 0.5 seconds, records all samples, and stops at the specified wall limit or 4 GiB sampled-tree RSS soft limit. Each run has `process_record.json` and `console.log`, including failed attempts. Python conversion uses the HF-2 development environment only for NumPy/SciPy serialization, not HF mechanics.

The small reference process took 108.5620384 s; failed setup took 15.7116426 s; successful setup took 12.4983296 s. Their total is 136.7720106 s, including startup. Full-reference timing is recorded separately in its run receipt; the coordinating task also accounts for independent Python numerical jobs against the shared budget.

These are implementation-agreement references for this uploaded source version and its source numeric units. They do not establish independent contact accuracy, mesh convergence, physical stability or the fidelity of the project's LF candidates.

## Completed full reference

The single authorized `cshape_001` attempt completed all 100 original targets through lambda = 1. The outer MATLAB process took 64.3522573 s, with peak sampled tree RSS 1,570,394,112 bytes. Total MATLAB process time including small references and the failed setup attempt is 201.1242679 s. `cshape_001/cshape_path.npz` stores canonical arrays; `cshape_path.json` stores per-target diagnostics, status, hashes and provenance; `step_001.mat` through `step_100.mat` retain source-order accepted states and individual console logs. The final minimum J is 4.84742971922e-5, and the final relative free residual is approximately 8.6285e-9. `reference_summary.json` records whole-path extrema and source integrity. Cross-language acceptance is reported by the independent validator, not inferred from source convergence.
