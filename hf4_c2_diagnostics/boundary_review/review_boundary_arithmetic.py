"""Read-only C1 boundary arithmetic and candidate geometry; no FE/HP solve."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("boundary_arithmetic.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def exact(value):
    return F.from_float(float(value))


def q(x):
    return -x-1 if x < 0 else x-3 if x > 2 else 1-2*abs(x-1)


def grid(a, b, h):
    count = (b-a)/h
    assert count.denominator == 1
    return [a+i*h for i in range(count.numerator+1)]


def trapezoid_mean(xs, ys):
    return sum(((xs[i+1]-xs[i])*(ys[i]+ys[i+1])/2
                for i in range(len(xs)-1)), F(0))/(xs[-1]-xs[0])


def fraction_record(value):
    return dict(exact=str(value), display=float(value))


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior boundary review")
    diagnostic_path = ROOT / "hf4_c1_results/local_reaction_diagnostic.json"
    diagnostic = read(diagnostic_path)
    bindings = {}
    for name, expected in diagnostic["input_sha256"].items():
        path = ROOT / "hf4_c1_results" / name
        assert sha(path) == expected, name
        bindings[path.relative_to(ROOT).as_posix()] = expected
    for name in ("hf_repo/src/hf_eval/contact_c1.py", "hf_repo/configs/contact_c1_v1.json",
                 "hf_repo/configs/contact_c1_precision_r2.json", "hf_repo/scripts/run_contact_c1_r2.py",
                 "hf_repo/scripts/audit_contact_c1.py", "hf4_c1_results/local_reaction_diagnostic.json"):
        bindings[name] = sha(ROOT/name)
    cases = []
    for case in diagnostic["cases"]:
        run = ROOT / "hf4_c1_results" / case["run"]
        phase = case["state_id"].split(":")[0]
        stage = run / "stages" / phase
        entries = read(stage / "steps/index.json")["steps"]
        entry, = [row for row in entries if row["index"] == int(case["state_id"].split(":")[1])]
        with np.load(stage / "model.npz", allow_pickle=False) as archive:
            model = {key: archive[key].copy() for key in archive.files}
        with np.load(stage / "steps" / entry["file"], allow_pickle=False) as archive:
            state = {key: archive[key].copy() for key in ("u_lift", "u_fluctuation")}
        h = exact(case["h_mm"])
        coordinates = model["coordinates"]
        xmin, xmax = map(exact, (coordinates[:, 0].min(), coordinates[:, 0].max()))
        assert (xmin, xmax) == (F(-2), F(4))
        expected_fixed = np.sort(np.r_[2*model["bottom_nodes"]+1, 2*model["top_nodes"]+1,
                                    2*np.flatnonzero(np.all(coordinates == [1., 0.], axis=1))])
        assert np.array_equal(expected_fixed, model["fixed_dofs"])
        bottom = model["bottom_nodes"]
        xs = [exact(coordinates[n, 0]) for n in bottom]
        drive = [exact(state["u_lift"][2*n+1])+exact(state["u_fluctuation"][2*n+1]) for n in bottom]
        expected = [F(1, 2) if phase == "uniform_tmc" else F(3, 8)+F(1, 16)*q(x) for x in xs]
        assert drive == expected
        body = [i for i, x in enumerate(xs) if 0 <= x <= 2]
        body_mean = trapezoid_mean([xs[i] for i in body], [drive[i] for i in body])
        whole_mean = trapezoid_mean(xs, drive)
        nodes = []
        for node in case["negative_nodes"]:
            x = exact(node["reference_x_mm"])
            node_id = node["node_id"]
            current = x+exact(state["u_lift"][2*node_id])+exact(state["u_fluctuation"][2*node_id])
            assert str(current) == str(F(node["current_x_exact_split_fraction"]))
            body_distance = -x if x < 0 else x-2
            side_distance = min(x-xmin, xmax-x)
            adjacent = np.flatnonzero(np.any(model["connectivity"] == node_id, axis=1))
            assert not any(model["solid"][adjacent])
            nodes.append(dict(node_id=node_id, reference_x=fraction_record(x),
                              current_x=fraction_record(current),
                              distance_to_initial_body_edge_mm=fraction_record(body_distance),
                              distance_to_numerical_side_mm=fraction_record(side_distance),
                              body_edge_distance_in_cells=fraction_record(body_distance/h),
                              side_distance_in_cells=fraction_record(side_distance/h),
                              adjacent_elements=adjacent.tolist(), adjacent_elements_all_medium=True,
                              total_N=node["total_N"], material_N=node["material_N"],
                              regularization_N=node["regularization_N"]))
        with localcontext() as context:
            context.prec = 120
            aggregate = case["aggregate"]
            negative = abs(Decimal(aggregate["negative_total_N"]))
            material = abs(Decimal(aggregate["negative_set_material_N"]))
            regularization = abs(Decimal(aggregate["negative_set_regularization_N"]))
            ratio = str(regularization/negative)
        cases.append(dict(run=case["run"], mode=case["mode"], h_mm=case["h_mm"],
                          old_fixed_count=len(expected_fixed), kr_exact_binary64=str(exact(model["kr"])),
                          body_bottom_mean_mm=fraction_record(body_mean), whole_bottom_mean_mm=fraction_record(whole_mean),
                          body_trace_matches_frozen_task_exactly=True, negative_nodes=nodes,
                          absolute_negative_total_N=str(negative),
                          negative_set_material_magnitude_N=str(material),
                          negative_set_regularization_magnitude_N=str(regularization),
                          negative_set_regularization_magnitude_fraction=ratio))
    profile_cases = []
    for b in (F(1), F(2), F(5, 2), F(3)):
        for h in (F(1, 4), F(1, 8), F(1, 16)):
            xs = grid(-b, 2+b, h)
            mean = trapezoid_mean(xs, list(map(q, xs)))
            formula = b*(b-2)/(2+2*b)
            assert mean == formula
            body = grid(F(0), F(2), h)
            assert trapezoid_mean(body, list(map(q, body))) == 0
            profile_cases.append(dict(padding_mm=float(b), h_mm=float(h),
                unmodified_profile_whole_mean=fraction_record(mean), body_profile_mean="0",
                whole_mean_drive_shift_at_amplitude_00625_mm=fraction_record(mean/F(16))))
    candidates = []
    for name, b, h, outer_free in (("existing_C1_baseline", F(2), F(1, 8), False),
             ("mesh_only", F(2), F(1, 16), False), ("padding_only", F(5, 2), F(1, 8), False),
             ("outer_bottom_free_only", F(2), F(1, 8), True)):
        nx, ny = int((2+2*b)/h), int(F(5, 4)/h)
        bottom_fixed = int(2/h)+1 if outer_free else nx+1
        fixed = (nx+1)+bottom_fixed+1
        candidates.append(dict(name=name, h_mm=float(h), padding_mm=float(b),
            domain_mm=[float(-b), float(2+b), 0., 1.25], elements=nx*ny,
            solid_elements=int(2/h)*int(1/h), ndof=2*(nx+1)*(ny+1), fixed_dofs=fixed,
            nominal_plane_lateral_margin_mm=float(4-b),
            nominal_margin_is_not_deformed_coverage=True,
            prescribed_bottom="body [0,2] only" if outer_free else "whole bottom",
            Lref_mm=2., same_material_and_kr=True, uniform_only=True))
    ratios = {}
    for mode in ("uniform", "perturbation"):
        pair = {c["h_mm"]: Decimal(c["absolute_negative_total_N"]) for c in cases if c["mode"] == mode}
        with localcontext() as context:
            context.prec = 80
            ratios[mode] = str(pair[.25]/pair[.125])
    payload = dict(schema="c2_boundary_arithmetic_review_v1", created_utc=datetime.now(timezone.utc).isoformat(),
        scope="saved-file identity and exact boundary arithmetic only; no FE or new HP evaluation",
        input_sha256=bindings, script_sha256=sha(Path(__file__)), source_cases=cases,
        unchanged_outer_profile_domain_width_checks=profile_cases,
        whole_profile_mean_formula="b*(b-2)/(2+2*b) for domain [-b,2+b] with original exterior q",
        candidate_uniform_mesh_inventory=candidates, coarse_to_fine_negative_magnitude_ratio=ratios,
        interpretation="two-mesh ratios are observations, not convergence orders or pressure evidence")
    with OUT.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(dict(status="pass", cases=len(cases), negative_nodes=sum(len(c["negative_nodes"]) for c in cases),
                         profile_checks=len(profile_cases), candidates=candidates, output_sha256=sha(OUT)), indent=2))


if __name__ == "__main__":
    main()
