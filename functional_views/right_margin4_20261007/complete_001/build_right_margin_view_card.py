"""Freeze saved right-margin views only after both actual full-path references pass."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil

STAGE = "functional_views/right_margin4_20261007/complete_001"
BASE = "lf_data_preparation/native_workpiece_001/"
PREPS = {"right2col": BASE + "right_margin_preparation_001", "right4col": BASE + "right_margin4_preparation_001"}
CASES = {"right2col": BASE + "right_margin_cycle_001", "right4col": BASE + "right_margin4_cycle_001"}
DOMAINS = {
    "right2col": dict(shape_yx=[40,82],counts=dict(cells=3280,nodes=3403,dofs=6806,solid_cells=1086,medium_cells=2194,solid_incident_nodes=1337,fixed_dofs=450,free_dofs=6356)),
    "right4col": dict(shape_yx=[40,84],counts=dict(cells=3360,nodes=3485,dofs=6970,solid_cells=1086,medium_cells=2274,solid_incident_nodes=1337,fixed_dofs=452,free_dofs=6518))}
VIEWER_SHA = "761a9ffd1512233ce048be364c00a86882b69e2fb3e3fe81d7f79f74ad52b166"
LAUNCHER_SHA = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
read = lambda p: json.loads(p.read_text(encoding="utf-8"))
digest = lambda p: sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="actual Git repository root")
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    stage = root / STAGE
    assert not stage.exists(), "Fresh complete view stage required; no overwrite/retry"
    assert digest(author / "saved_right_margin_views.py") == VIEWER_SHA
    assert digest(author / "launch_view.py") == LAUNCHER_SHA
    bindings, counts, references, tasks = {}, {}, [], {}

    def bind(file, expected=None):
        pin = digest(file)
        assert expected is None or pin == expected
        bindings[file.relative_to(root).as_posix()] = pin

    def terminal(control, phase):
        file, protocol = control / (phase + "_launch.json"), control / (phase + "_protocol.json")
        row = read(file); bind(file); bind(protocol)
        assert row["invocations"] == 1 and row["status"] == "pass" and row["exit_code"] == 0
        assert row["stop_reason"] is None and row["all_bindings_unchanged"]
        assert row["protocol_sha256"] == digest(protocol)
        assert all(digest(root / p) == pin for p, pin in read(protocol)["bindings"].items())

    for label,name in CASES.items():
        control = root / name; directory = control / "run_001/result"
        result_file = directory / "result.json"
        result = read(result_file); bind(result_file)
        records = result["states"]
        assert result["accepted_states"] == len(records) and records
        assert result["status"] == "success" and all(result[k] for k in ("path_completed", "loading_peak_reached", "unload_endpoint_reached", "task_target_executed"))
        terminal(control, "production")
        execution_file = control / "run_001/execution_receipt.json"
        execution = read(execution_file); bind(execution_file)
        assert execution["status"] == "pass" and execution["accepted_states"] == len(records)
        assert execution["result_sha256"] == digest(result_file)
        for filename in ("input_inventory.json", "source_freeze.json", "task.json", "direction.npz"):
            bind(control / "run_001" / filename)
        model_file = directory / result["model"]["descriptor_path"]
        model = read(model_file); bind(model_file,result["model"]["descriptor_file_sha256"])
        bind(model_file.parent / model["arrays"]["path"],model["arrays"]["sha256"])
        assert model["task_sha256"] == result["task_sha256"]
        for value in model["source_geometry"]["snapshot"].values(): bind(model_file.parent / value)
        tasks[label] = model["task"]
        assert model["grid"]["shape_yx"] == DOMAINS[label]["shape_yx"]
        assert model["region_metadata"]["counts"] == DOMAINS[label]["counts"]
        for path in ("preparation_protocol.json", "prepare_launch.json", "run_001/preparation_receipt.json", "run_001/input_inventory.json", "run_001/model_comparison.json", "run_001/mapping.npz", "run_001/direction.npz"):
            bind(root / PREPS[label] / path)
        prep = read(root / PREPS[label] / "run_001/preparation_receipt.json")
        assert prep["status"] == "pass" and prep["model_comparison"]["parent_physical_subdomain_byte_exact"]
        for record in records:
            bind(directory / record["descriptor_path"],record["descriptor_file_sha256"])
            for key in ("state", "forces", "tangents", "matrix"):
                declaration = record[key]; bind(directory / declaration["path"],declaration["sha256"])
        reference_file = control / "reference/summary.json"
        reference = read(reference_file); bind(reference_file)
        terminal(control, "reference")
        assert reference["status"] == "pass" and reference["result_sha256"] == digest(result_file)
        assert reference["accepted_states"] == len(reference["states"]) == len(records)
        assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 2 * len(records)
        references.append(label + "=" + reference_file.relative_to(root).as_posix())
        counts[label] = dict(accepted_states=len(records),production_status=result["status"],complete=True,
            reference_available=True,qualification="same-result actualN full path and fresh2N HP; strain/pressure not newly qualified")
    old,new = tasks["right2col"],tasks["right4col"]
    assert old["third_medium"] == new["third_medium"] == {"gamma":1e-6}
    assert all(new[key] == value for key,value in old.items() if key not in {"geometry","background_symmetry","task_id","purpose","parameter_origin","description"})
    assert old["background_symmetry"]["points_mm"] == [[0.,40.],[82.,40.]]
    assert new["background_symmetry"] == {**old["background_symmetry"],"points_mm":[[0.,40.],[84.,40.]]}
    for name in ("src/hf_eval/__init__.py", "src/hf_eval/native_region_geometry.py", "src/hf_eval/boundary_geometry.py", "src/hf_eval/workpiece_nodal.py", "scripts/measure_native_workpiece_regions.py"):
        bind(root / "hf_repo" / name)
    selected = [author/name for name in ("build_right_margin_view_card.py","execute_right_margin_views.py","saved_right_margin_views.py","launch_view.py","README.md","author_note.json","viewer_author_note.json","viewer_delta.diff","wrapper_delta.diff","source_delta.diff","source_author_checks.json")]
    reviews = sorted(author.glob("*review*.json")); assert reviews, "Complete view peer review required"
    selected += reviews
    stage.mkdir(parents=True)
    for file in selected:
        shutil.copyfile(file,stage/file.name); assert digest(file)==digest(stage/file.name); bind(stage/file.name)
    argv = [STAGE+"/execute_right_margin_views.py","--repo","hf_repo","--protocol",STAGE+"/protocol.json",
        "--output",STAGE+"/view","--time-limit","180","--stop-file",STAGE+"/stop_requested.txt"]
    for label,name in CASES.items(): argv += ["--case",label+"="+name+"/run_001/result"]
    for specification in references: argv += ["--reference",specification]
    protocol = dict(schema_version="right-margin-saved-view-card-1.0",mode="complete",bindings=bindings,
        sampled_RSS_bytes=8*1024**3,phases=dict(view=dict(helper_seconds=180,outer_seconds=210,argv=argv)),
        cases=counts,expected_observations_each=sum(row["accepted_states"] for row in counts.values()),
        tip_selection=dict(reference_coordinates_mm=[80.,30.],method="unique exact saved coordinate per case"),
        scope="Raw761a9f saved viewer once, geometry/nodal once each per all actual accepted states; zero new F/T/model/solver/HP.",
        comparison_scope="gamma1e-6 2mm versus4mm right derived-domain margin; parent82 subdomain retained, top82 to84 only; all other physics retained; no pressure/free-body qualification",
        stop_policy="One view invocation; first error closes card, no retry/extension/force.")
    protocol_file = stage / "protocol.json"
    with protocol_file.open("x",encoding="utf-8") as handle:
        json.dump(protocol,handle,indent=2,ensure_ascii=False,allow_nan=False);handle.write("\n")
    print(json.dumps(dict(status="frozen_only_not_executed",protocol_sha256=digest(protocol_file),cases=counts,bindings=len(bindings))),flush=True)


if __name__ == "__main__":
    main()
