"""Plot saved cycle010 regions and finite-face rays after a complete fresh audit.

No geometry, force, tangent, action, solver or HP evaluator is imported or called.
Install in the repository; every accepted index is retained, including repeats.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
from textwrap import fill
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
import psutil

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
sha = lambda p: sha256(p.read_bytes()).hexdigest()


def canonical(value):
    if isinstance(value, dict): return {k:canonical(v) for k,v in value.items()}
    if isinstance(value, list): return [canonical(v) for v in value]
    if isinstance(value, float):
        assert np.isfinite(value)
        return (0. if value == 0. else value).hex()
    return value


def semantic_sha(value):
    value = {k:v for k,v in value.items() if k != "descriptor_sha256"}
    return sha256(json.dumps(canonical(value),sort_keys=True,separators=(",", ":"),
                            ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "measurements", "output", "protocol", "reference"):
        parser.add_argument("--"+name, required=True, type=Path)
    args = parser.parse_args()
    stage, output = args.stage.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pins, peak_RSS, rows = {}, 0, []
    report = dict(status="running", new_calls=dict(force=0,tangent=0,solver=0,HP=0,consumer=0,geometry=0))

    def checkpoint():
        nonlocal peak_RSS
        memory = psutil.Process().memory_info()
        peak_RSS = max(peak_RSS,memory.rss,getattr(memory,"peak_wset",memory.rss))
        assert perf_counter()-STARTED <= 120 and peak_RSS <= 8*1024**3
        assert not any((p/"stop_requested.txt").exists() for p in (stage,output.parent))

    def bind(path, expected=None):
        checkpoint(); path = path.resolve(); actual = sha(path)
        assert expected is None or actual == expected, "Saved SHA differs: "+path.name
        assert path not in pins or actual == pins[path], "Saved input changed: "+path.name
        pins[path] = actual
        return actual

    def read(path, expected=None, descriptor=False):
        bind(path,expected); value = json.loads(path.read_text(encoding="utf-8"))
        if descriptor: assert semantic_sha(value) == value["descriptor_sha256"]
        return value

    def archive(path, declaration):
        bind(path,declaration["sha256"])
        with np.load(path,allow_pickle=False) as source: data = {k:source[k].copy() for k in source.files}
        assert set(data) == set(declaration["fields"])
        for name,a in data.items():
            assert dict(dtype=a.dtype.name,shape=list(a.shape),sha256=sha256(a.tobytes()).hexdigest()) == declaration["fields"][name]
        return data

    def bind_reference(value, directory):
        if isinstance(value,dict):
            if "path" in value and "sha256" in value: bind(directory/value["path"],value["sha256"])
            for item in value.values(): bind_reference(item,directory)
        elif isinstance(value,list):
            for item in value: bind_reference(item,directory)

    try:
        protocol_file = args.protocol.resolve(); protocol = read(protocol_file)
        for name,pin in protocol["bindings"].items(): bind(ROOT/name,pin)
        assert pins[Path(__file__).resolve()] == sha(Path(__file__))
        assert stage.name == "coarse_square_cycle_010"
        receipt = read(stage/"execution_receipt.json")
        inventory = read(stage/"input_inventory.json",receipt["input_inventory_sha256"])
        freeze = read(stage/"source_freeze.json",inventory["source_freeze_sha256"])
        assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
        for name,pin in freeze["sources"].items(): bind(stage/"sources"/Path(name).name,pin)
        directory = stage/inventory["case"]["result_directory"]
        result = read(directory/"result.json",receipt["result_sha256"],True)
        assert receipt["status"] == "pass" and result["status"] == "success" and result["failure"] is None
        assert result["schema_version"] == "hf-native-mean-result-1.2" and result["path_kind"] == "ordered_cycle"
        assert all(result[k] is True for k in ("path_completed","loading_peak_reached","unload_endpoint_reached","task_target_executed"))
        assert result["independent_HP_qualified"] is result["equilibrium_qualified"] is result["HF_qualified"] is False
        model_file = directory/result["model"]["descriptor_path"]
        metadata = read(model_file,result["model"]["descriptor_file_sha256"],True)
        model_path = model_file.parent/metadata["arrays"]["path"]
        model = archive(model_path,metadata["arrays"])
        assert len(model) == 27 and metadata["schema_version"] == "hf-native-project-model-1.1"
        assert metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
        assert metadata["arrays"]["sha256"] == result["model"]["arrays_sha256"] == receipt["model_sha256"]
        task = metadata["task"]
        assert semantic_sha(task) == metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"]
        assert task["path"]["targets_mm"] == result["targets_mm"] == inventory["case"]["targets_mm"] == TARGETS
        assert task["case_family"] == "gripper" and task["workpiece"]["kind"] == "fixed_rigid" and task["workpiece"]["shape"] == "square"
        reference_file = args.reference.resolve()
        reference = read(reference_file)
        assert reference["schema_version"] == "native-workpiece-cycle-independent-audit-1.0" and reference["status"] == "pass"
        assert reference["result_sha256"] == receipt["result_sha256"] and reference["audited_targets_mm"] == TARGETS
        assert reference["source_bindings"] == freeze["sources"] and reference["gates"] == inventory["gates"]
        assert reference["full_element_and_DOF_coverage"] is True and reference["HP_matrix_columns_exhaustively_checked"] is False
        assert all(reference[k] is False for k in ("contact_qualified","clamp_qualified","pressure_qualified"))
        measurements_file = args.measurements.resolve(); measurement = read(measurements_file)
        assert measurement["schema_version"] == "native-workpiece-region-path-1.0" and measurement["status"] == "pass"
        assert measurement["production_status"] == "success" and measurement["task_sha256"] == result["task_sha256"]
        assert measurement["inputs_and_sources_unchanged"] is True and measurement["failure"] is None
        assert all(measurement[k] == 0 for k in ("force_calls","tangent_calls","solver_calls","HP_calls","consumer_calls"))
        for item in measurement["sources"].values(): bind(measurements_file.parent/item["snapshot_path"],item["sha256"])
        expected_inputs = {"input/result.json","input/"+result["model"]["descriptor_path"],"input/"+model_path.relative_to(directory).as_posix()}
        for saved in result["states"]: expected_inputs.update(("input/"+saved["descriptor_path"],"input/"+saved["state"]["path"]))
        assert {k for k in measurement["input_files_sha256"] if k.startswith("input/")} == expected_inputs
        for role,pin in measurement["input_files_sha256"].items():
            if role.startswith("input/"): bind(directory/role.split("/",1)[1],pin)
            else:
                assert role == "comparison/boundary_measurements.json" and measurement["boundary_comparison"]["sha256"] == pin
                bind(measurements_file.parent/measurement["boundary_comparison"]["path"],pin)
        n = len(result["states"])
        assert n >= len(TARGETS) and n == result["accepted_states"] == receipt["accepted_states"] == reference["accepted_states"]
        assert n == len(reference["states"]) == measurement["declared_accepted_states"] == len(measurement["accepted_states"])
        assert measurement["geometry_calls_started"] == measurement["geometry_calls_completed"] == n
        assert reference["HP_calls_started"] == reference["HP_calls_completed"] == 2*n
        originals = [r for r in result["states"] if r["is_original_target"]]
        assert [r["original_target_index"] for r in originals] == list(range(len(TARGETS))) and [r["d"] for r in originals] == TARGETS
        states = []
        for index,(saved,checked,measured) in enumerate(zip(result["states"],reference["states"],measurement["accepted_states"])):
            assert checked["status"] == "pass" and checked["index"] == measured["accepted_index"] == index and checked["HP_calls"] == 2
            assert checked["state_sha256"] == measured["state_sha256"] == saved["state_sha256"]
            assert checked["target_mm"] == measured["d_mm"] == saved["d"]
            assert all(checked[k] == measured[k] == saved[k] for k in ("leg","original_target_index"))
            bind_reference(checked,reference_file.parent)
            stored = read(directory/saved["descriptor_path"],saved["descriptor_file_sha256"],True)
            assert stored == {k:v for k,v in saved.items() if k not in ("descriptor_path","descriptor_file_sha256")}
            state = archive(directory/saved["state"]["path"],saved["state"])
            assert set(state) == {"lift","fluctuation"}
            identity = sha256(b"split_displacement_v1"+np.asarray(len(model["b_in"]),dtype="<i8").tobytes()+state["lift"].astype("<f8",copy=False).tobytes()+state["fluctuation"].astype("<f8",copy=False).tobytes()).hexdigest()
            assert identity == saved["state_sha256"] and not np.any(state["lift"])
            assert not np.any(state["fluctuation"][model["fixed_dofs"]])
            geometry = measured["geometry"]; regions = geometry["regions"]
            assert geometry["geometry_valid"] is True and geometry["complete_fixed_half_square"] is True
            assert regions["geometry_valid"] is regions["region_overlap_tested"] is True
            assert regions["set_containment_tested"] is regions["mechanism_self_overlap_tested"] is False
            assert all(geometry[k] is False for k in ("set_containment_tested","signed_penetration_tested","contact_pressure_qualification","contact_or_clamping_qualification"))
            row = dict(accepted_index=index,original_target_index=saved["original_target_index"],leg=saved["leg"],d_mm=saved["d"],state_sha256=saved["state_sha256"],geometry_valid=geometry["geometry_valid"],raw_interior_overlap=regions["raw_interior_overlap"],strict_interior_overlap=regions["strict_interior_overlap"],roundoff_ambiguous=regions["roundoff_ambiguous"],candidate_cell_pairs=regions["candidate_cell_pairs"],closed_boundary_min_distance_mm=regions["boundary_intersections"]["minimum_boundary_distance_mm"],closed_boundary_intersects=regions["boundary_intersections"]["intersects"])
            for face in ("bottom","left"):
                values = geometry["faces"][face]; hit = values["closest_hit"]
                assert values["no_outward_ray_hit"] == (values["minimum_first_ray_hit_mm"] is None) == (hit is None)
                row.update({face+"_first_ray_mm":values["minimum_first_ray_hit_mm"],face+"_no_hit":values["no_outward_ray_hit"],face+"_minimum_hit_count":len(values["minimum_hits"]),face+"_near_minimum_hit_count":len(values["roundoff_near_minimum_hits"])})
                for key in ("corner_hit","near_corner_hit","witness_residual_mm","raw_reconstructed_normal_projection_mm","face_parameter"):
                    row[face+"_"+key] = None if hit is None else hit[key]
                for point in ("face","edge"):
                    for axis,component in enumerate("xy"): row[face+"_"+point+"_"+component+"_mm"] = None if hit is None else hit[point+"_point_mm"][axis]
            rows.append(row); states.append((saved,state,geometry))
        assert rows[0]["d_mm"] == rows[-1]["d_mm"] == 0. and rows[-1]["original_target_index"] == len(TARGETS)-1
        peak = max(range(n),key=lambda i:rows[i]["d_mm"]); selected = [0,peak,n-1]
        xy,conn,solid = (model[k] for k in ("coordinates","connectivity","solid"))
        body_cells = model["workpiece_cells"]; medium = ~solid.copy(); medium[body_cells] = False
        fig,axes = plt.subplots(2,3,figsize=(19,11),layout="constrained")
        for ax,index,label in zip(axes[0],selected,("ORIGIN","ACTUAL PEAK","RETURN ZERO")):
            saved,state,geometry = states[index]; moved = xy+(state["lift"]+state["fluctuation"]).reshape(-1,2)
            ax.add_collection(PolyCollection(moved[conn[medium]],facecolors="#fff2de",edgecolors="none"))
            ax.add_collection(PolyCollection(moved[conn[solid]],facecolors="#b9d1dc",edgecolors="#71909e",linewidths=.2))
            ax.add_collection(PolyCollection(xy[conn[body_cells]],facecolors="#d9dde2",edgecolors="#6b7785",linewidths=.2))
            for face,color in (("bottom","#008b91"),("left","#bc3b80")):
                hit = geometry["faces"][face]["closest_hit"]
                if hit is not None:
                    points = np.asarray([hit["face_point_mm"],hit["edge_point_mm"]])
                    ax.plot(*points.T,"--",color=color,lw=1.8)
                    ax.scatter(*points[0],marker="o",s=24,facecolor="white",edgecolor=color,zorder=5)
                    ax.scatter(*points[1],marker="x",s=30,color=color,zorder=5)
                distance = geometry["faces"][face]["minimum_first_ray_hit_mm"]
                text = "NO OUTWARD HIT" if distance is None else f"{distance:.7g} mm"
                ax.text(.02,.98 if face == "bottom" else .90,face+": "+text,transform=ax.transAxes,va="top",color=color,fontsize=10,bbox=dict(facecolor="white",alpha=.9,edgecolor="none"))
            ax.set(xlim=(54,82),ylim=(22,41),aspect="equal",xlabel="x [mm]",ylabel="y [mm]",title=f"{label} #{index}: {saved['leg']}, d={saved['d']:g} mm\nActual deformation x1 / local viewport")
        for ax,face,color in zip(axes[1,:2],("bottom","left"),("#008b91","#bc3b80")):
            values = [np.nan if r[face+"_first_ray_mm"] is None else r[face+"_first_ray_mm"] for r in rows]
            ax.plot(range(n),values,"o-",color=color); ax.grid(alpha=.2)
            ax.set(title=face.title()+" finite outward first-ray distance",xlabel="Actual accepted index (chronological)",ylabel="Saved distance [mm]")
        axes[1,2].axis("off")
        lines = [f"Complete cycle010: {n} actual accepted indices",f"Fresh reference: {reference['HP_calls_completed']} HP80/120 calls",f"Original targets: {TARGETS} mm","Initial and return zero remain separate records.","Circle=face point; cross=mechanism edge point.","Dashed segment is geometric face-to-edge direction, NOT force.","No-hit=null / blank CSV / NaN curve; never changed to zero.","Closed-region distance includes the mathematical symmetry cut; physical rays exclude it.","Cell-union cross-region overlap is tested; whole-set containment and mechanism self-overlap are NOT tested.","No signed penetration, pressure or contact/clamp qualification.","Mechanical reference scope is force/PORT-Jv/equilibrium/body projections only; raw producer qualification flags unchanged.","No new geometry or mechanics evaluated."]
        axes[1,2].text(0,1,"\n\n".join(fill(line,width=52) for line in lines),va="top",fontsize=10)
        fig.suptitle("Cycle010 SAVED regions / finite-face ray diagnostics\nPhysical geometry x1; unsigned directional lengths are not pressure or contact proof",fontsize=16)
        checkpoint(); fig.savefig(output/"cycle010_saved_regions.png",dpi=150); plt.close(fig)
        with (output/"accepted_regions.csv").open("x",encoding="utf-8",newline="") as stream:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        (output/"plot_saved_regions_frozen.py").write_bytes(Path(__file__).read_bytes())
        checkpoint(); assert all(sha(p) == pin for p,pin in pins.items())
        assert not any(n == "hf_eval" or n.startswith("hf_eval.") for n in sys.modules)
        report.update(status="rendered_saved_regions",accepted_states=n,actual_peak_index=peak,last_accepted_index=n-1,selected_indices=selected,requested_targets_mm=TARGETS,actual_d_mm=[r["d_mm"] for r in rows],deformation_scale=1,interpolated_states=0,reference_summary_sha256=pins[reference_file],geometry_measurement_sha256=pins[measurements_file],scope="Saved measured cell-union/ray data only; no new geometry, signed penetration, pressure, contact/clamp, containment or self-overlap qualification",inputs_unchanged=True,input_files_sha256={p.relative_to(ROOT).as_posix():pin for p,pin in pins.items()},source_sha256=sha(Path(__file__)),protocol_sha256=pins[protocol_file],mechanical_hooks_monitored=False)
    except BaseException as error:
        report.update(status="failed_saved_regions_view",error=repr(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak_RSS,outputs_sha256={p.name:sha(p) for p in output.iterdir() if p.is_file()})
        with (output/"view_metadata.json").open("x",encoding="utf-8") as stream: json.dump(report,stream,indent=2,allow_nan=False); stream.write("\n")


if __name__ == "__main__":
    main()
