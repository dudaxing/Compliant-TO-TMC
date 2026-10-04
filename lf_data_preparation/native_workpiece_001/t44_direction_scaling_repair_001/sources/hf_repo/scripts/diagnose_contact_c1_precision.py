"""Fixed saved-state 50/80/120-digit diagnostic; no FE solve or gate change."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import platform

import numpy as np

from hf4_split_precision_reference import evaluate_split_prescribed_state


PRECISIONS = (50, 80, 120)
CONSISTENCY_LIMIT = Decimal("1e-40")
FORCE_FLOOR_RELATIVE_TO_SF = Decimal("1e-12")
TANGENT_FLOOR = Decimal("1e-10")
REPO = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def norm(values):
    return sum((v*v for v in values), Decimal(0)).sqrt()


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def diagnose(run, phase_id, index):
    run = Path(run).resolve()
    if phase_id not in ("uniform_precontact", "uniform_closed", "uniform_tmc", "perturbation"):
        raise ValueError("unknown phase")
    stage = run/"stages"/phase_id
    meta = read_json(stage/"metadata.json")
    entries = read_json(stage/"steps/index.json")["steps"]
    entry = entries[index]
    if entry["index"] != index or Path(entry["file"]).name != entry["file"]:
        raise ValueError("invalid saved state identity")
    state_path = stage/"steps"/entry["file"]
    if sha(state_path) != entry["sha256"] or sha(stage/"model.npz") != meta["model_sha256"]:
        raise ValueError("saved-state or model binding mismatch")
    with np.load(stage/"model.npz", allow_pickle=False) as archive:
        model = {k: archive[k] for k in archive.files}
    with np.load(state_path, allow_pickle=False) as archive:
        arrays = {k: archive[k] for k in archive.files}
    if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in (*model.values(), *arrays.values())):
        raise ValueError("only ordinary finite real arrays accepted")
    groups = {k[6:]: v for k, v in model.items() if k.startswith("group_") and np.any(v != 0)}
    hp = {p: evaluate_split_prescribed_state(model, arrays["u_lift"], arrays["u_fluctuation"],
          entry["d"], model["base"], model["direction"], groups, meta["force_scale_per_length"],
          precision=p, tangent_direction=arrays["tangent_direction"], fluctuation_offset=0.) for p in PRECISIONS}
    with localcontext() as context:
        context.prec = 120
        sf = hp[80]["force_scale_decimal"]
        components = {}
        mapping = (("total_force", "internal_force", "internal_decimal", Decimal("1e-11")),
                   ("material_force", "material_internal_force", "material_internal_decimal", Decimal("1e-9")),
                   ("regularization_force", "regularization_internal_force", "regularization_internal_decimal", Decimal("1e-9")),
                   ("total_tangent", "production_tangent_action", "tangent_action_decimal", Decimal("1e-10")),
                   ("material_tangent", "material_tangent_action", "material_tangent_action_decimal", Decimal("1e-9")),
                   ("regularization_tangent", "regularization_tangent_action", "regularization_tangent_action_decimal", Decimal("1e-9")))
        for name, archive_key, hp_key, evaluation_limit in mapping:
            floor = FORCE_FLOOR_RELATIVE_TO_SF*sf if name.endswith("force") else TANGENT_FLOOR
            scale = sf if name == "total_force" else max(norm(hp[80][hp_key]), floor)
            pairs = {}
            for a, b in ((50, 80), (80, 120), (50, 120)):
                absolute = norm([x-y for x, y in zip(hp[a][hp_key], hp[b][hp_key])])
                relative = absolute/scale
                pairs[f"{a}_vs_{b}"] = dict(absolute_error=absolute, relative_error=relative,
                                             limit=CONSISTENCY_LIMIT, passed=relative <= CONSISTENCY_LIMIT)
            production = norm([Decimal.from_float(float(a))-b for a, b in zip(arrays[archive_key], hp[80][hp_key])])/scale
            components[name] = dict(common_comparison_scale_from_hp80=scale,
                hp80_component_norm=norm(hp[80][hp_key]), floor=floor, pairs=pairs,
                production_vs_hp80=dict(relative_error=production, limit=evaluation_limit, passed=production <= evaluation_limit),
                raw_decimal={str(p): hp[p][hp_key] for p in PRECISIONS})
        physical_checks = {str(p): {key: hp[p][key] for key in ("force_scale_decimal", "relative_residual_decimal",
                          "relative_constraint_decimal", "relative_force_balance_decimal", "minimum_J_decimal")} for p in PRECISIONS}
        raw_valid = {str(p): hp[p]["relative_residual_decimal"] <= Decimal("1e-9") and
                     hp[p]["relative_constraint_decimal"] <= Decimal("1e-10") and
                     hp[p]["relative_force_balance_decimal"] <= Decimal("1e-8") and hp[p]["minimum_J_decimal"] > 0 for p in PRECISIONS}
    files = [Path(__file__).resolve(), REPO/"configs/contact_c1_v1.json", REPO/"scripts/hf4_split_precision_reference.py",
             REPO/"scripts/hf2_precision_reference.py", run/"metadata.json", stage/"metadata.json",
             stage/"model.npz", stage/"steps/index.json", stage/"result.json", stage/"completion.json", state_path]
    bindings = {Path(os.path.relpath(p, run)).as_posix(): sha(p) for p in files}
    return plain(dict(schema_version="contact-c1-fixed-state-precision-diagnostic-1.0",
        created_utc=datetime.now(timezone.utc).isoformat(), run=str(run), phase_id=phase_id,
        index=index, parameter_s=entry["d"], state_sha256=sha(state_path), precision_digits=PRECISIONS,
        interpretation="additional higher precision diagnostic; original 50/80 failure is retained; no FE state or threshold changed",
        status="pass_80_vs_120" if all(v["pairs"]["80_vs_120"]["passed"] for v in components.values()) else "not_pass_80_vs_120",
        original_50_vs_80_passed=all(v["pairs"]["50_vs_80"]["passed"] for v in components.values()),
        production_vs_hp80_passed=all(v["production_vs_hp80"]["passed"] for v in components.values()),
        hp_numerical_gates_passed=raw_valid, hp_numerical_metrics=physical_checks, components=components,
        input_and_helper_sha256=bindings, environment=dict(python=platform.python_version(), numpy=np.__version__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; preserve earlier diagnostic evidence")
    result = diagnose(args.run, args.phase, args.index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "original_50_vs_80_passed", "production_vs_hp80_passed", "hp_numerical_gates_passed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
