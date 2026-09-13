# HF-2 implementation interface — frozen before new numerical runs

Authorized 2026-09-13 after HF-1. Limited source-numeric TMC code benchmark, CPU float64. Existing HF-1 inputs, geometry identity and linear solver semantics stay versioned and unchanged. Authoritative scientific definitions and thresholds are in the reviewed workspace HF2_PLAN.md. This interface records ownership, array layout and reproducibility conventions.

## Element kernel (tmc_kernel.py)

- `operators(hx, hy, thickness=1.0) -> dict`: `grad` (9,4,2), `hessian` (4,2,2), `weights` (9), `points` (9,2). Corner order BL,BR,TR,TL. Quadrature is xi slow, eta fast: (-1,-1),(-1,0),(-1,1),(0,-1),..., matching source MATLAB. Weights include hx*hy/4 and thickness; their sum is hx*hy*thickness. Mixed xy and yx Hessian terms both participate.
- `determinants(ue, ops)`: accepts (8,) or (ne,8), returns (9,) or (ne,9); computes no logarithm or inverse. Reject nonfinite displacement. F indices mean displacement component then physical reference derivative.
- `element_response(u, ops, lam, mu, kr, *, tangent=True) -> dict` and `batch_response(ue, ops, lam, mu, kr, *, tangent=True) -> dict`. Batch lam/mu are scalars or (ne,), kr scalar. Each public call checks positive finite J before evaluating any log/inverse and checks finite outputs. `tangent=False` skips Jacobian work for backtracking/postprocessing.
- Return keys: `residual` (...,8), `tangent` (...,8,8) when requested, `material_residual`, `regularization_residual`, `J` (...,9), `F` (...,9,2,2), `stress_second_piola` (...,9,2,2), `material_energy` (... scalar). NumPy arrays on return. Material energy includes all weights. JAX differentiates the **actual residual**, including deformation-dependent regularization; do not symmetrize or differentiate a substitute energy.
- `KernelError(ValueError)` carries `code` and `details`; invalid J code `invalid_J`, nonfinite code `nonfinite`. No state saved across solves. Only stateless compiled functions may cache.
- Import does not change global JAX configuration. Caller sets `JAX_ENABLE_X64=true`, `JAX_PLATFORMS=cpu` before first JAX use. Public calls require CPU and enabled float64. Tests and benchmark runner set these explicitly; failure is reported rather than silently using another dtype/device.

Kernel owner also writes test_tmc_kernel.py: operators, affine/rigid states, initial linear tangent, fixed nonaffine FD curves, invalid J, batch equality. No full C-shape run from kernel tests.

## Global assembly and path (tmc.py; root)

`TMCModel` holds physical coordinates (nn,2), connectivity (ne,4), lam/mu (ne), kr, cell sizes, thickness factor, solid flags and fixed DOFs. Canonical nodes are x-fast from bottom to top; cells same ordering; ux/uy interleaved. All cells/nodes, including third medium, remain. Standalone source_numeric profile is not passed through HF-1 geometry qualification or its mm/N result wrapper.

`assemble(model,u,tangent=True)` returns global sparse K when requested, internal residual and element fields. General sparse LU uses the unsymmetrized Jacobian. `solve_path(model,F0,targets,settings,on_accept)` starts from zero and records accepted steps, trials, rollback and timing. Failure returns last verified state plus null target metrics and actual reached multiplier. Each accepted step is persistable through the callback. A failed Newton step cannot mutate a previously accepted array.

Root writes benchmark preset/runner in tmc_benchmark.py and a CLI subcommand. Source model is full domain, force control, source_numeric units, thickness factor 1. Python source-routine implementation remains independent from MATLAB. Benchmark numbers bind to uploaded ZIP hash. Pure reference arrays may be loaded for exact source target multipliers and comparisons; MATLAB is never required at runtime.

## External reference and independent verification

Reference owner writes only reference_validation/matlab/ and generates small MAT/JSON/NPZ with coordinates, source/local and canonical permutations, inputs and numerical outputs. MATLAB source copies stay outside hf_repo and retain author notices. Reference decomposition uses unmodified assembly with kr=0 or zero material rather than subtracting nearly equal solid forces to expose a tiny regularization term. Export second Piola stress/J/material energy in a clearly labeled external postprocessor because original assembleKtFi does not return them.

Verification owner writes hf_repo/scripts/validate_hf2.py and tests/test_tmc_parity.py after numeric fixture schema is agreed with reference owner. Store exact case definitions, thresholds, error curves and failures. No selecting easier cases after results. Cross-language comparisons must explicitly reorder node/DOF/element indices.

## Budget and boundary

Small jobs max 300 s each and 20 min cumulative, compilation smoke max 10 min; each one-config C-shape attempt max 20 min, MATLAB then Python (not concurrent). Total numerical subprocess wall time max 60 min including compilation and failures. Installation time separately recorded. Each owner writes timing receipts and informs root before a full C-shape attempt. Root gates the full run on small-case results. Measure child working set/peak where possible; this is a 4 GiB soft monitored budget, not a hard OS sandbox. No HF-3 implementation.
