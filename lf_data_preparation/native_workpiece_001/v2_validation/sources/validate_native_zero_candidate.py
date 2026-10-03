"""One captured near-zero force/tangent and two independent Decimal references.

Run candidate and reference in separate processes. This supplied-displacement
check qualifies only the recorded input and one direction, never equilibrium.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
from decimal import Decimal, localcontext
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ("total", "material", "regularization")
FORCE_KEYS = ("residual", "material_residual", "regularization_residual")
HP_FORCE_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")
HP_ACTION_KEYS = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
HP_HASHES = {
    "hf4_split_precision_reference.py": "308ff44131efebcaf779936779385cfad8fc0b57cb5fc015a3afc34d9adf06d2",
    "hf2_precision_reference.py": "97a9eb5f7dfe20704a4fd53cadba740903a68a05ad046d80ee85bf4340a93d55",
}
SOURCE_NAMES = ("split_kernel_invariants_hu.py", "split_numpy_tangent.py", "compensated_invariants.py",
                "compensated_kinematics.py", "split_kernel_compensated.py", "split_state.py", "tmc.py", "tmc_kernel.py")
PEAK_RSS = 0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checkpoint():
    global PEAK_RSS
    PEAK_RSS = max(PEAK_RSS, psutil.Process().memory_info().rss)
    require(PEAK_RSS <= 8*1024**3, "8 GiB RSS limit exceeded")
    require(perf_counter()-STARTED <= 60., "60 second phase limit exceeded")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def plain(value):
    if isinstance(value, dict):
        return {name: plain(part) for name, part in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(part) for part in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, Decimal):
        return str(value)
    return value.item() if isinstance(value, np.generic) else value


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(plain(value), stream, indent=2, allow_nan=False)
        stream.write("\n")


def write_gzip(path, value):
    with gzip.open(path, "xt", encoding="utf-8") as stream:
        json.dump(plain(value), stream, allow_nan=False)


def archive_record(path, arrays):
    return dict(path=path.name, sha256=sha(path), fields={name: dict(dtype=value.dtype.name,
        shape=list(value.shape), sha256=hashlib.sha256(value.tobytes(order="C")).hexdigest())
        for name, value in arrays.items()})


def same(left, right, label):
    require(left.dtype == right.dtype and left.shape == right.shape
            and left.tobytes(order="C") == right.tobytes(order="C"), label+" differs")


def candidate(input_file, directory, counts):
    captured = read_npz(input_file)
    model_file = input_file.parent.parent/"tiny_cycle_diagnostic_001/result/model/model.npz"
    model = read_npz(model_file)
    for name in ("edofs", "grad", "hessian", "weights", "lam", "mu", "kr"):
        same(captured[name], model[name], "Saved model "+name)
    require(captured["edofs"].shape == (16, 8) and captured["lift"].shape == (50,), "Captured case is not the recorded 16-cell case")
    same(captured["lift"], np.zeros(50), "Captured zero lift")
    direction = np.linspace(-.3, .4, len(captured["lift"]))
    fixture = dict(captured, points=model["points"], direction=direction,
                   local_direction=direction[captured["edofs"]])
    shutil.copyfile(input_file, directory/"input_state.npz")
    shutil.copyfile(model_file, directory/"model_snapshot.npz")
    np.savez_compressed(directory/"fixture.npz", **fixture)
    source_dir = directory/"sources"
    source_dir.mkdir()
    source_bindings = {}
    for path in [ROOT/"hf_repo/src/hf_eval"/name for name in SOURCE_NAMES] + [Path(__file__)] + [Path(__file__).with_name(name) for name in HP_HASHES]:
        digest = sha(path)
        if path.name in HP_HASHES:
            require(digest == HP_HASHES[path.name], "Frozen Decimal helper changed")
        shutil.copyfile(path, source_dir/path.name)
        source_bindings[path.name] = digest
    checkpoint()
    sys.path.insert(0, str(ROOT/"hf_repo/src"))
    from hf_eval.split_kernel_invariants_hu import batch_response_split_numpy
    from hf_eval.split_numpy_tangent import _tangent
    operators = {name: fixture[name] for name in ("grad", "hessian", "weights", "points")}
    counts["force_started"] += 1
    fields = batch_response_split_numpy(captured["lift"][captured["edofs"]],
        captured["fluctuation"][captured["edofs"]], operators, captured["lam"], captured["mu"], float(captured["kr"]))
    counts["force_completed"] += 1
    checkpoint()
    counts["tangent_started"] += 1
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        tensors = _tangent(fields, operators, captured["lam"], captured["mu"], float(captured["kr"]))
    counts["tangent_completed"] += 1
    arrays = dict(fields, **tensors, direction=direction, local_direction=fixture["local_direction"])
    for component in COMPONENTS:
        arrays[component+"_action"] = np.einsum("eij,ej->ei", tensors[component+"_tangent"], fixture["local_direction"])
    require(all(value.dtype == np.float64 and np.isfinite(value).all() for value in arrays.values()), "Candidate arrays must be finite float64")
    np.savez_compressed(directory/"arrays.npz", **arrays)
    checkpoint()
    require(all(sha(source_dir/name) == digest for name, digest in source_bindings.items()), "Source capsule changed")
    return dict(status="pass", input_sha256=sha(input_file), model_source_sha256=sha(model_file),
        fixture=archive_record(directory/"fixture.npz", fixture), arrays=archive_record(directory/"arrays.npz", arrays),
        source_bindings=source_bindings, direction_definition="np.linspace(-.3,.4,50), dimensionless full-DOF direction; local scatter by original edofs",
        elements=16, original_dofs=50, force_units="N", tangent_action_units="N/mm")


def norm(values):
    return sum((value*value for value in values), Decimal(0)).sqrt()


def compare(actual, reference, other, denominator, limit):
    differences = [Decimal.from_float(float(a))-b for a, b in zip(actual, reference, strict=True)]
    error = norm(differences)/denominator
    agreement = norm([a-b for a, b in zip(reference, other, strict=True)])/denominator
    return dict(normalized_error=str(error), hp80_hp120_error=str(agreement), denominator=str(denominator),
        limit=str(limit), reference_limit="1e-40", pass_gate=error <= limit and agreement <= Decimal("1e-40")), differences


def reference(input_file, directory, counts):
    candidate_dir = directory.parent/"candidate"
    metadata = json.loads((candidate_dir/"result.json").read_text(encoding="utf-8"))
    require(metadata["status"] == "pass" and sha(input_file) == metadata["input_sha256"], "Passing candidate input identity differs")
    require(sha(candidate_dir/"input_state.npz") == metadata["input_sha256"], "Captured input snapshot differs")
    require(sha(candidate_dir/"model_snapshot.npz") == metadata["model_source_sha256"], "Saved model snapshot differs")
    for name, expected in metadata["source_bindings"].items():
        require(sha(candidate_dir/"sources"/name) == expected, "Candidate source capsule differs")
    for name in ("fixture", "arrays"):
        require(sha(candidate_dir/metadata[name]["path"]) == metadata[name]["sha256"], name+" archive differs")
    fixture, actual = read_npz(candidate_dir/"fixture.npz"), read_npz(candidate_dir/"arrays.npz")
    original = read_npz(input_file)
    for name, value in original.items():
        same(fixture[name], value, "Fixture raw captured "+name)
    same(fixture["direction"], np.linspace(-.3, .4, 50), "Declared direction")
    same(fixture["local_direction"], fixture["direction"][fixture["edofs"]], "Direction scatter")
    helper_dir = directory/"sources"
    helper_dir.mkdir()
    for name, digest in HP_HASHES.items():
        require(sha(candidate_dir/"sources"/name) == digest, "Frozen Decimal helper identity differs")
        shutil.copyfile(candidate_dir/"sources"/name, helper_dir/name)
    spec = importlib.util.spec_from_file_location("decimal_zero_candidate", helper_dir/"hf4_split_precision_reference.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Disjoint nodes retain each local weak force in a single full 16-cell HP
    # evaluation. The physical direction remains the recorded global50 scatter.
    hp_fixture = {name: fixture[name] for name in ("grad", "hessian", "weights", "lam", "mu", "kr")}
    hp_fixture.update(connectivity=np.arange(64, dtype=np.int64).reshape(16, 4),
                      F0=np.zeros(128), fixed_dofs=np.empty(0, dtype=np.int64))
    hp = []
    for precision in (80, 120):
        checkpoint()
        counts["HP_started"] += 1
        values = module.DecimalSplitQ1Reference(hp_fixture, precision=precision).evaluate(
            fixture["lift"][fixture["edofs"]].ravel(), fixture["fluctuation"][fixture["edofs"]].ravel(),
            tangent_direction=fixture["local_direction"].ravel(), derivative=True)
        counts["HP_completed"] += 1
        write_gzip(directory/f"hp{precision}.json.gz", values)
        hp.append(values)
        checkpoint()
    checks, differences = [], []
    with localcontext() as context:
        context.prec = 120
        for element in range(16):
            indices = slice(8*element, 8*element+8)
            scale = max(norm(hp[1][HP_FORCE_KEYS[0]][indices]), Decimal("2e-14"))
            for i, component in enumerate(COMPONENTS):
                for kind, key, candidate_key, limit in (
                    ("force", HP_FORCE_KEYS[i], FORCE_KEYS[i], Decimal("1e-11" if i == 0 else "1e-9")),
                    ("action", HP_ACTION_KEYS[i], component+"_action", Decimal("1e-10" if i == 0 else "1e-9"))):
                    expected, other = hp[1][key][indices], hp[0][key][indices]
                    denominator = (scale if i == 0 else max(norm(expected), Decimal("1e-12")*scale)) if kind == "force" else max(norm(expected), Decimal("1e-10"))
                    record, delta = compare(actual[candidate_key][element], expected, other, denominator, limit)
                    checks.append(dict(element=element, component=component, kind=kind, **record))
                    differences.append(dict(element=element, component=component, kind=kind, values=list(map(str, delta))))
                    if not record["pass_gate"]:
                        write_json(directory/"checks_until_failure.json", checks)
                        write_gzip(directory/"differences.json.gz", differences)
                        raise ValueError(f"First reference gate failed: element {element}, {component} {kind}")
    write_gzip(directory/"differences.json.gz", differences)
    worst = {kind: {component: max((row for row in checks if row["kind"] == kind and row["component"] == component),
        key=lambda row: Decimal(row["normalized_error"])) for component in COMPONENTS} for kind in ("force", "action")}
    return dict(status="pass" if all(row["pass_gate"] for row in checks) else "fail",
        candidate_result_sha256=sha(candidate_dir/"result.json"), input_sha256=sha(input_file),
        elements_compared=16, local_force_entries_compared=384, local_action_entries_compared=384,
        checks=checks, worst=worst, files={path.name: sha(path) for path in directory.glob("*.gz")},
        force_scale_floor_N="2e-14", action_scale_floor_N_per_mm="1e-10", HP_source_bindings=HP_HASHES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("candidate", "reference"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    directory = args.output/args.mode
    directory.mkdir()  # Exclusive phase; no retry or replacement of evidence.
    counts = dict(force_started=0, force_completed=0, tangent_started=0, tangent_completed=0,
                  HP_started=0, HP_completed=0, solver_calls=0, JIT_calls=0)
    try:
        report = (candidate if args.mode == "candidate" else reference)(args.input.resolve(), directory, counts)
    except Exception as error:
        report = dict(status="fail", error=dict(type=type(error).__name__, message=str(error),
                      code=getattr(error, "code", None), details=getattr(error, "details", {})))
    report.update(schema_version="native-zero-candidate-validation-1.0", mode=args.mode, call_counts=counts,
        elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=PEAK_RSS,
        script_sha256=sha(Path(__file__)), scope="Recorded rejected split state and one declared direction only",
        equilibrium_qualified=False, contact_qualified=False, full_tangent_columns_HP_checked=False)
    write_json(directory/"result.json", report)
    print(json.dumps(plain(report), indent=2, allow_nan=False), flush=True)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
