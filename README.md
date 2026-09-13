# Independent HF evaluator — HF-1

This standalone Python package reads immutable binary geometry packages and performs a **solid-only small-strain linear interface diagnostic**. It does not implement nonlinear TMC, contact, geometry generation, topology optimization, or research performance ranking.

Runtime: Python 3.13, NumPy, SciPy and Matplotlib. All exact runtime versions and hashes are in `requirements.lock`. No LF source, LF environment, MATLAB process, exporter, or external source path is required. The LF-specific one-time exporter is maintained outside this repository.

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

Developer validation: install `requirements-dev.txt` in the independent HF
environment, then run `python -m pytest`. Tests construct ordinary local fixtures
and do not need the LF preparation directory, uploaded archives, or source library.

The result has separate readability, geometry qualification, numerical convergence and functionality fields. Missing research criteria remain `pending`; a successful linear solve is not proof of nonlinear/contact fidelity. Output signs, reference thickness, mean-port weights and support selection are explicit. Every call starts from the undeformed state and generates a fresh evaluation ID.

Q1 plane-strain stiffness is independently implemented with 2×2 Gauss integration and assembled only over solid cells. Mean input displacement uses a Lagrange multiplier, rather than equal displacement at every port node. Optional output loading is one generalized rank-one spring. Symmetry and fixtures constrain only solid-incident nodes in this diagnostic; there is no third medium.

See `docs/DATA_FORMAT.md` for the frozen file contract, and `docs/HF1_VALIDATION.md` for measured validation and limitations. The initial implementation interface is preserved in `docs/IMPLEMENTATION_INTERFACE.md`. The input geometry remains unchanged; results store hashes, task and solver configurations, dependency versions, arrays and plotting data.
