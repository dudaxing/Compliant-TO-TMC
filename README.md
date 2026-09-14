# Independent HF evaluator — HF-1 through HF-4-A/B

Version **0.5.0** adds explicit two-component displacement storage and prescribed-motion evaluation. The physical state is the exact sum of the saved binary64 `u_lift` and `u_fluctuation` arrays; `u_display` is a rounded plotting view. Four frozen uniform normal-contact combinations have passed their production, independent precision and reference audits with the original material parameters and thresholds. See [split-state implementation](docs/HF4_SPLIT_IMPLEMENTATION.md). General nonuniform contact, cylinder gripping and real mechanism performance remain outside this validation.

Use `hf_eval.split_state.SplitDisplacement`, `hf_eval.split_kernel.assemble_split`, and `hf_eval.split_prescribed.solve_split_prescribed_path` for this explicit state interface. The synthetic geometry still comes from `hf_eval.normal_contact.build_normal_contact`. For ordinary NPZ/JSON evidence, run:

```powershell
python scripts/run_hf4_split_normal.py --spec configs/hf4/validation_spec.json --gamma-index 1 --mesh-index 1 --output ../new-split-result
```

The split interface has no automatic conversion of the geometry-file `evaluate` dispatcher below. Each state, reaction and gap must use the declared representation. The independent audit is `scripts/audit_hf4_split_normal.py`; a run-specific frozen source manifest binds its evidence. Reuse no output directory from a prior run.

Historical **0.4.0** added the normal-contact task and U-only affine prescribed-motion interface, with **3 of 4 paths** completing. The fine gamma=1e-7 case stalled because free-node updates were lost in the absolute binary64 state. Its failed path, null target metrics and [original implementation](docs/HF4_IMPLEMENTATION.md) remain historical evidence. The old `solve_prescribed_path` and U-only kernel retain their original semantics; the split interface is explicit.

This standalone Python package provides immutable geometry input, the HF-1 **solid-only small-strain linear diagnostic**, and the HF-2 **finite-deformation Q1 third-medium source-code benchmark**. The latter is one uploaded C-shape configuration, in explicitly labeled source numeric units. It is not a validation of contact accuracy or a research performance ranking; geometry generation and topology optimization are outside this package.

Version **0.3.0** adds explicit project mapping and average-displacement control for the native inverter/gripper pilot tasks, plus stable near-zero material arithmetic. See [HF3 implementation](docs/HF3_IMPLEMENTATION.md) and [HF3 validation](docs/HF3_VALIDATION.md) for the recorded evidence and its limits. Readability, research qualification, numerical completion and functionality remain distinct.

The historical **0.2.1** C-shape path passed independent high-precision equilibrium at all 100 targets under the unchanged external 1e-8 threshold. See [repair validation](docs/HF2_REPAIR_VALIDATION.md). That full-path evidence remains tied to version 0.2.1; version 0.3.0 separately reruns the original small and fixed strong-state regressions. The original 0.2.0 run remains [partially complete](docs/HF2_VALIDATION.md), with its failed states preserved.

Runtime: Python 3.13, NumPy, SciPy, Matplotlib, JAX and jaxlib. All exact runtime versions and hashes are in `requirements.lock`. No LF source, LF environment, MATLAB process, exporter, or external source path is required. MATLAB and LF-specific preparation scripts are maintained outside this repository.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements.lock
.venv\Scripts\python -m pip install --no-deps .
.venv\Scripts\python -m hf_eval inspect <geometry.json>
.venv\Scripts\python -m hf_eval evaluate <geometry.json> --task <task.json> --solver <solver.json> --output <new-result-directory>
```

The release ZIP also contains the tested wheel in `dist/`; it can replace the
source installation step above (`pip install --no-deps <wheel>`). A Git checkout
does not need that ignored build artifact: the source installation uses only this
repository and its pinned build backend, never an LF checkout.

For the supplied data package, use `canonical/inverter/geometry.json` with
`tasks/inverter_linear_interface_smoke.json`, or the corresponding `gripper`
files, and `solvers/hf1_q1_solid_linear_v1.json`. Paths are relative to the
data package, not hardcoded by the evaluator. See `dataset_index.json` there.

Developer validation: after installing the locked runtime, install `requirements-dev.txt` in the independent HF
environment, then run `python -m pytest`. Tests construct ordinary local fixtures
and small ordinary numeric fixtures. They do not need the LF preparation directory, uploaded archives, or source library. Full C-shape paths are excluded from routine pytest.

The result has separate readability, geometry qualification, numerical convergence and functionality fields. Missing research criteria remain `pending`; a successful linear solve is not proof of nonlinear/contact fidelity. Output signs, reference thickness, mean-port weights and support selection are explicit. Every call starts from the undeformed state and generates a fresh evaluation ID.

Q1 plane-strain stiffness is independently implemented with 2×2 Gauss integration and assembled only over solid cells. Mean input displacement uses a Lagrange multiplier, rather than equal displacement at every port node. Optional output loading is one generalized rank-one spring. Symmetry and fixtures constrain only solid-incident nodes in this diagnostic; there is no third medium.

See `docs/DATA_FORMAT.md` for the frozen file contract and `docs/HF1_VALIDATION.md` for the historical 0.1.0 validation. The input geometry remains unchanged; results store hashes, configurations, dependency versions, arrays and plotting data.

HF-2 keeps all solid/third-medium nodes, uses 3×3 Gauss–Lobatto integration,
and differentiates the actual nonconservative residual with JAX float64 on CPU.
The Jacobian is not symmetrized. Newton trials check positive J and finite values;
bounded residual-based backtracking and bisection preserve the last verified state.
For exactly the archived source target multipliers, run from this repository:

```powershell
.venv\Scripts\python -m hf_eval tmc-cshape --source-setup validation/hf2/reference/cshape_setup.npz --output new-cshape-result --time-limit 1200
```

The source setup is ordinary data and is checked against the independent preset.
The preset has E=100, nu=0.3, kv=1e-6, alpha=1e-6, thickness factor 1 and total
y-force −3 in source numeric units. It does not inherit HF-1's MPa/mm/thickness
choices. For direct Python API use, set `JAX_ENABLE_X64=true` and
`JAX_PLATFORMS=cpu` before the first JAX use; the CLI sets them explicitly.
Every call begins from zero. Accepted steps are saved incrementally; failed
targets have null metrics and the last reached multiplier. Hard process termination
may leave only checkpoints and the external resource receipt.

See `docs/HF2_IMPLEMENTATION.md` for the new interface and `docs/HF2_VALIDATION.md`
for validation scope and evidence. The original HF-1 release ZIP remains unchanged.
