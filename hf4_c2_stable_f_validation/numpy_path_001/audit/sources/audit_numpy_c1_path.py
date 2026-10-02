"""Independent HP80/120 audit of the actual new NumPy C1 path arrays.

DecimalSplitQ1Reference remains unchanged and receives only saved primitive
arrays and the exact split state. New references are computed here; historical
HP references are not substituted. Identical two-array states reuse that new
reference, while each stage's boundary parameter is checked separately.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil

from hf4_split_precision_reference import DecimalSplitQ1Reference

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hf_eval import split_kernel_invariants_hu as force_kernel
from hf_eval.split_numpy_tangent import batch_tangent_components_split_numpy
from hf_eval.tmc import TMCModel

NAMES = ("total_force", "material_force", "regularization_force",
         "total_tangent", "material_tangent", "regularization_tangent")
HP_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal",
           "tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
LIMITS = dict(zip(NAMES, ("1e-11", "1e-9", "1e-9", "1e-10", "1e-9", "1e-9")))
LIMITS.update(hp80_hp120="1e-40", relative_residual="1e-9", relative_constraint="1e-10",
              relative_force_balance="1e-8")
HP_HASHES = {"hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
             "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False,
                               default=str) + "\n", encoding="utf-8")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def D(value):
    return Decimal.from_float(float(value))


def norm(vector):
    return sum((x*x for x in vector), Decimal(0)).sqrt()


def state_hash(arrays):
    digest = hashlib.sha256(b"split_displacement_v1")
    digest.update(np.asarray([len(arrays["u_lift"])], dtype="<i8").tobytes())
    for name in ("u_lift", "u_fluctuation"):
        digest.update(np.asarray(arrays[name], dtype="<f8").tobytes())
    return digest.hexdigest()


def check(rows, name, value, limit):
    value, limit = Decimal(value), Decimal(limit)
    rows.append(dict(name=name, value=value, limit=limit,
                     pass_gate=value.is_finite() and value <= limit))


def measurements(hp, model, base, direction, parameter):
    """Same SF/constraint/reaction rules as the unchanged C1 Decimal adapter."""
    internal = hp["internal_decimal"]
    dscale = max(abs(D(parameter)), Decimal("1e-6"))
    scale = max(norm([internal[i] for i in model.free]),
                norm([internal[i] for i in model.fixed_dofs]), Decimal("1e-8")*Decimal(100)*dscale)
    constraint = max((abs(hp["physical_displacement_decimal"][i]-D(base[i])-D(parameter)*D(direction[i]))
                      for i in model.fixed_dofs), default=Decimal(0))
    fixed = set(model.fixed_dofs)
    reactions = [internal[i] if i in fixed else Decimal(0) for i in range(model.ndof)]
    balance = [sum(reactions[i::2], Decimal(0)) for i in (0, 1)]
    return dict(force_scale_N=scale, relative_residual=norm([internal[i] for i in model.free])/scale,
                relative_constraint=constraint/dscale, relative_force_balance=norm(balance)/scale,
                constraint_error_mm=constraint, min_J=min(x for row in hp["J_decimal"] for x in row))


def candidate(model, state, direction):
    args = (state["u_lift"][model.edofs], state["u_fluctuation"][model.edofs],
            model.ops, model.lam, model.mu, model.kr)
    fields = force_kernel.batch_response_split_numpy(*args)
    tangent = batch_tangent_components_split_numpy(*args)
    assemble = lambda local: np.bincount(model.edofs.ravel(), weights=local.ravel(), minlength=model.ndof)
    values = dict(zip(NAMES[:3], [assemble(fields[key]) for key in
                                ("residual", "material_residual", "regularization_residual")]))
    values.update({key: assemble(np.einsum("eij,ej->ei", tangent[key], direction[model.edofs]))
                   for key in NAMES[3:]})
    values["J"] = fields["J"]
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--force-input", type=Path, required=True, help="NumPy saved C1 force output directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=300.)
    args = parser.parse_args()
    started = perf_counter()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs, sources = args.output / "inputs", args.output / "sources"
    inputs.mkdir(); sources.mkdir()
    bound = []
    def bind(path):
        bound.append(dict(path=path.as_posix(), sha256=sha(path), bytes=path.stat().st_size))
    for name, expected in HP_HASHES.items():
        path = Path(__file__).with_name(name)
        assert sha(path) == expected
        bind(path)
        shutil.copyfile(path, sources / name)
    from hf_eval import split_numpy_tangent
    for path in (Path(__file__), Path(force_kernel.__file__), Path(force_kernel.ci.__file__),
                 Path(split_numpy_tangent.__file__)):
        bind(path)
        shutil.copyfile(path, sources / path.name)
    model_source = args.force_input / "inputs/model.npz"
    bind(model_source)
    shutil.copyfile(model_source, inputs / "model.npz")
    fixture = npz(inputs / "model.npz")
    bind(args.force_input / "inputs/metadata.json")
    bind(args.force_input / "inputs/state.npz")
    metadata = read(args.force_input / "inputs/metadata.json")
    h = metadata["h"]
    model = TMCModel(fixture["coordinates"], fixture["connectivity"], fixture["lam"], fixture["mu"],
                     float(fixture["kr"]), h, h, 1., fixture["solid"], fixture["fixed_dofs"])
    for key in ("grad", "hessian", "weights"):
        assert np.array_equal(model.ops[key], fixture[key])
    direction = npz(args.force_input / "inputs/state.npz")["tangent_direction"]
    assert not np.any(direction[model.fixed_dofs])
    np.savez_compressed(inputs / "tangent_direction.npz", tangent_direction=direction)
    protocol_path = Path(__file__).resolve().parents[1] / "configs/contact_c1_v1.json"
    bind(protocol_path)
    protocol = read(protocol_path)
    shutil.copyfile(protocol_path, inputs / "contact_c1_v1.json")
    assert protocol["audit"]["relative_force_evaluation"] == 1e-11
    assert protocol["audit"]["relative_tangent_action"] == 1e-10
    assert protocol["audit"]["relative_component_evaluation"] == 1e-9
    refs, records = {}, []
    process = psutil.Process()
    def checkpoint():
        if perf_counter()-started > args.time_limit:
            raise RuntimeError("new numerical audit time limit reached")
    summary = dict(status="running", thresholds=LIMITS, precision_pair=[80, 120],
                   new_references_computed=True, historical_HP_substituted=False,
                   tangent_direction_semantics="saved unit direction perturbs fluctuation; lift fixed",
                   scope="new C1 numerical forces/Jv, positive J, residual/constraints/force balance; not HF5 admission",
                   unique_reference_states=0, accepted_records=0, records=records)
    try:
        for phase in ("approach", "compression"):
            stage = args.path / phase
            bind(stage / "summary.json"); bind(stage / "initial_state.npz")
            phase_summary = read(stage / "summary.json")
            assert phase_summary["target_reached"]
            initial = npz(stage / "initial_state.npz")
            base = np.zeros(model.ndof)
            base[model.fixed_dofs] = initial["u_lift"][model.fixed_dofs]
            for row in phase_summary["states"]:
                checkpoint()
                state_path = stage / row["path"]
                bind(state_path)
                state = npz(state_path)
                identity = state_hash(state)
                assert identity == row["state_sha256"]
                state_started = perf_counter()
                reused = identity in refs
                print(f"audit {phase}/{row['path']} physical_drive={row['physical_drive_mm']} reuse={reused}", flush=True)
                if not reused:
                    hp = {}
                    for precision in (80, 120):
                        checkpoint()
                        hp[precision] = DecimalSplitQ1Reference(fixture, precision=precision).evaluate(
                            state["u_lift"], state["u_fluctuation"], tangent_direction=direction)
                        print(f"HP{precision} ready after {perf_counter()-state_started:.3f}s", flush=True)
                    reference_name = f"reference_{len(refs):03d}.json.gz"
                    payload = dict(state_sha256=identity, precision_pair=[80, 120],
                                   state_file=state_path.as_posix(), generated_here=True,
                                   references={str(p): {key: hp[p][key] for key in
                                               (*HP_KEYS, "J_decimal", "physical_displacement_decimal")} for p in (80, 120)})
                    (args.output / reference_name).write_bytes(gzip.compress(
                        json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"), mtime=0))
                    refs[identity] = (hp, reference_name)
                hp, reference_name = refs[identity]
                values = candidate(model, state, direction)
                for name, saved_key in zip(NAMES[:3], ("internal_force", "material_internal_force", "regularization_internal_force")):
                    np.testing.assert_array_equal(values[name], state[saved_key])
                checks = []
                with localcontext() as context:
                    context.prec = 120
                    measured = {p: measurements(hp[p], model, base, fixture["direction"], row["parameter_s"]) for p in (80, 120)}
                    sf = measured[80]["force_scale_N"]
                    for p in (80, 120):
                        check(checks, f"HP{p}_positive_J", 0 if measured[p]["min_J"] > 0 else 1, "0")
                        for name in ("relative_residual", "relative_constraint", "relative_force_balance"):
                            check(checks, f"HP{p}_"+name, measured[p][name], LIMITS[name])
                    check(checks, "NumPy_positive_J", 0 if np.isfinite(values["J"]).all() and values["J"].min() > 0 else 1, "0")
                    for name, key in zip(NAMES, HP_KEYS, strict=True):
                        reference = hp[80][key]
                        denominator = (sf if name == "total_force" else
                                       max(norm(reference), Decimal("1e-12")*sf if "force" in name else Decimal("1e-10")))
                        error = norm([D(a)-b for a, b in zip(values[name], reference, strict=True)])/denominator
                        agreement = norm([a-b for a, b in zip(reference, hp[120][key], strict=True)])/denominator
                        check(checks, name, error, LIMITS[name])
                        checks[-1]["denominator"] = denominator
                        check(checks, "HP80_HP120_"+name, agreement, LIMITS["hp80_hp120"])
                    normal = -sum((D(a)*b for a, b in zip(fixture["group_top"], hp[80]["internal_decimal"], strict=True)), Decimal(0))
                    measurements_80 = measured[80]
                record = dict(phase=phase, state_file=state_path.as_posix(), state_sha256=identity,
                              parameter_s=row["parameter_s"], physical_drive_mm=row["physical_drive_mm"],
                              status="pass" if all(c["pass_gate"] for c in checks) else "fail",
                              reference_file=reference_name, reused_new_reference=reused, checks=checks,
                              HP80_measurements=measurements_80, HP80_normal_force_N=normal,
                              elapsed_seconds=perf_counter()-state_started)
                np.savez_compressed(args.output / f"candidate_{len(records):03d}.npz", **values)
                records.append(record)
                summary.update(unique_reference_states=len(refs), accepted_records=len(records),
                               elapsed_seconds=perf_counter()-started, inputs_and_sources=bound)
                write(args.output / "summary.json", summary)
                print(f"result {record['status']} elapsed={record['elapsed_seconds']:.3f}s total={summary['elapsed_seconds']:.3f}s", flush=True)
                if record["status"] != "pass":
                    raise ValueError("First new-state numerical gate failure; later states not audited")
        for row in bound:
            assert sha(Path(row["path"])) == row["sha256"]
        summary["status"] = "pass"
    except Exception as error:
        summary.update(status="stopped", error_type=type(error).__name__, error=str(error))
    finally:
        summary.update(elapsed_seconds=perf_counter()-started, unique_reference_states=len(refs),
                       accepted_records=len(records), inputs_and_sources=bound,
                       process_peak_working_set_bytes=getattr(process.memory_info(), "peak_wset", process.memory_info().rss))
        write(args.output / "summary.json", summary)
    print(json.dumps(dict(status=summary["status"], records=len(records), unique=len(refs),
                          elapsed_seconds=summary["elapsed_seconds"])), flush=True)
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
