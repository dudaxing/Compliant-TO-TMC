"""Display saved peak J/Hu samples from a complete, fresh-reference-checked cycle010.

Only saved arrays are reduced and formatted. No hf_eval module, mechanics,
reference evaluator, action consumer or geometry measurement is imported.
Install in the repository before use; the shared render card supplies --protocol.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm, Normalize
import numpy as np
import psutil

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"hf_repo").is_dir())
TARGETS = [0., .5, 1., 1.5, 1.75, 1.8, 1.75, 1.5, 1., .5, 0.]
TRACE = dict(mode="chunk256", element_block_size=256, global_selector_scope="full_batch")
AVAILABILITY = dict(response_mode="mechanical", response_contract="split-numpy-mechanical-1.0",
    force_kernel_version="p26_q1_split_mechanical_numpy_aux_omitted_candidate1",
    auxiliary_material_energy=dict(status="not_evaluated", qualified=False, field_present=False))


def require(condition, message):
    if not condition: raise RuntimeError(message)


def canonical(value):
    if isinstance(value, dict): return {k:canonical(v) for k,v in value.items()}
    if isinstance(value, list): return [canonical(v) for v in value]
    if isinstance(value, float):
        require(math.isfinite(value), "Non-finite descriptor value")
        return (0. if value == 0. else value).hex()
    return value


def semantic_hash(value):
    return sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stage", "output", "protocol", "reference"): parser.add_argument("--"+name, required=True, type=Path)
    args = parser.parse_args(); stage, output = args.stage.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    pins, peak_rss = {}, 0
    report = dict(status="running", scientific_requalification_performed=False,
        new_calls=dict(force=0, tangent=0, HP=0, solver=0, action_consumer=0,
                       assembly=0, geometry_measurement=0),
        zero_new_call_basis="Source imports only stdlib, NumPy, Matplotlib and psutil; saved-array formatting only")
    def checkpoint():
        nonlocal peak_rss
        info = psutil.Process().memory_info(); peak_rss = max(peak_rss, info.rss, getattr(info,"peak_wset",info.rss))
        require(perf_counter()-STARTED <= 120 and peak_rss <= 8*1024**3,
                "Saved-field view resource window closed; no retry")
        require(not any((p/"stop_requested.txt").exists() for p in (stage,output.parent)), "Stop requested")
    def bind(path, expected=None):
        path = path.resolve(); actual = sha256(path.read_bytes()).hexdigest()
        require(expected is None or actual == expected, "File SHA differs: "+path.name)
        pins[path] = actual; return actual
    def read(path, expected=None, descriptor=False):
        bind(path,expected); value = json.loads(path.read_text(encoding="utf-8"))
        if descriptor: require(semantic_hash({k:v for k,v in value.items() if k != "descriptor_sha256"})
                              == value["descriptor_sha256"], "Descriptor SHA differs: "+path.name)
        return value
    def archive(path, declaration):
        bind(path,declaration["sha256"])
        with np.load(path,allow_pickle=False) as data: arrays = {k:data[k].copy() for k in data.files}
        require(set(arrays) == set(declaration["fields"]), "Archive fields differ")
        for key,item in declaration["fields"].items():
            a = arrays[key]
            require(dict(dtype=a.dtype.name,shape=list(a.shape),sha256=sha256(a.tobytes()).hexdigest()) == item,
                    "Saved array identity differs: "+key)
        return arrays
    try:
        checkpoint(); protocol = read(args.protocol.resolve())
        for name,pin in protocol["bindings"].items(): bind(ROOT/name,pin)
        require(Path(__file__).resolve() in pins, "Viewer source is absent from protocol")
        receipt = read(stage/"execution_receipt.json")
        inventory = read(stage/"input_inventory.json",receipt["input_inventory_sha256"])
        require(stage.name == "coarse_square_cycle_010" and inventory["case"]["alias"] == "gripper_coarse_square", "Cycle identity differs")
        freeze = read(stage/"source_freeze.json",inventory["source_freeze_sha256"])
        require(receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"], "Source/input contract differs")
        for name,pin in freeze["sources"].items(): bind(stage/"sources"/Path(name).name,pin)
        for name,pin in inventory["input_bindings"].items(): bind(ROOT/name,pin)
        directory = stage/inventory["case"]["result_directory"]
        result_file = directory/"result.json"; result = read(result_file,receipt["result_sha256"],True)
        require(receipt["status"] == "pass" and result["schema_version"] == "hf-native-mean-result-1.2"
                and result["status"] == "success" and result["failure"] is None, "Complete production pass is required")
        require(all(result[k] is True for k in ("production_converged","target_reached","task_target_executed",
                "path_completed","loading_peak_reached","unload_endpoint_reached")), "Path is incomplete")
        require(result["path_kind"] == "ordered_cycle" and result["targets_mm"] == inventory["case"]["targets_mm"] == TARGETS, "Ordered targets differ")
        require(result["tangent_execution"] == TRACE and all(result[k] == v for k,v in AVAILABILITY.items()), "Mechanical availability differs")
        require(all(result[k] is False for k in ("independent_HP_qualified","equilibrium_qualified","HF_qualified")), "Raw production flags were changed")
        model_file = directory/result["model"]["descriptor_path"]
        metadata = read(model_file,result["model"]["descriptor_file_sha256"],True)
        model = archive(model_file.parent/metadata["arrays"]["path"],metadata["arrays"])
        require(len(model) == 27 and metadata["schema_version"] == "hf-native-project-model-1.1", "Model schema differs")
        require(metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"] and metadata["arrays"]["sha256"]
                == result["model"]["arrays_sha256"] == receipt["model_sha256"], "Model binding differs")
        task = metadata["task"]
        require(task["path"]["targets_mm"] == TARGETS and task["input"]["target_mm"] == max(TARGETS)
                and semantic_hash(task) == metadata["task_sha256"] == result["task_sha256"] == receipt["task_sha256"], "Task binding differs")
        require(task["case_family"] == "gripper" and task["workpiece"]["kind"] == "fixed_rigid"
                and task["workpiece"]["shape"] == "square", "Workpiece scope differs")
        states = result["states"]; n = len(states)
        require(n == result["accepted_states"] == receipt["accepted_states"] and n >= len(TARGETS), "Accepted count differs")
        originals = [row for row in states if row["is_original_target"]]
        require([r["original_target_index"] for r in originals] == list(range(len(TARGETS)))
                and [r["d"] for r in originals] == TARGETS and states[0]["d"] == states[-1]["d"] == 0., "Original path or zero return is incomplete")
        for row in states:
            stored = read(directory/row["descriptor_path"],row["descriptor_file_sha256"],True)
            require(stored == {k:v for k,v in row.items() if k not in ("descriptor_path","descriptor_file_sha256")}, "State record differs")
        reference_file = args.reference.resolve()
        require(reference_file.resolve() in pins, "Fresh reference summary is absent from protocol")
        reference = read(reference_file,pins[reference_file.resolve()])
        require(reference["schema_version"] == "native-workpiece-cycle-independent-audit-1.0" and reference["status"] == "pass"
                and reference["result_sha256"] == receipt["result_sha256"] and reference["audited_targets_mm"] == TARGETS, "Same-result fresh reference pass is required")
        require(reference["accepted_states"] == len(reference["states"]) == n
                and reference["HP_calls_started"] == reference["HP_calls_completed"] == 2*n, "Fresh HP coverage differs")
        require(reference["full_element_and_DOF_coverage"] is True and reference["HP_matrix_columns_exhaustively_checked"] is False
                and all(reference[k] is False for k in ("contact_qualified","clamp_qualified","pressure_qualified")), "Reference scope differs")
        require(reference["source_bindings"] == freeze["sources"] and reference["gates"] == inventory["gates"], "Reference contract differs")
        for index,(checked,row) in enumerate(zip(reference["states"],states)):
            require(checked["status"] == "pass" and checked["index"] == index and checked["HP_calls"] == 2
                    and checked["state_sha256"] == row["state_sha256"] and checked["target_mm"] == row["d"]
                    and all(checked[k] == row[k] for k in ("leg","original_target_index")), "Reference state identity differs")
        peak = max(range(n),key=lambda index:states[index]["d"]); row = states[peak]
        require(row["d"] == max(TARGETS) and row["tangent_execution"] == TRACE, "Actual peak differs")
        state = archive(directory/row["state"]["path"],row["state"])
        forces = archive(directory/row["forces"]["path"],row["forces"])
        coords,conn,solid = (model[k] for k in ("coordinates","connectivity","solid"))
        ne = len(conn); require(ne == 3200 and coords.shape == (3321,2) and conn.shape == (ne,4), "Native extent differs")
        require(set(state) == {"lift","fluctuation"} and len(forces) == 16 and "material_energy" not in forces, "Mechanical saved fields differ")
        identity = sha256(b"split_displacement_v1"+np.asarray(len(model["b_in"]),dtype="<i8").tobytes()
            +state["lift"].astype("<f8",copy=False).tobytes()+state["fluctuation"].astype("<f8",copy=False).tobytes()).hexdigest()
        require(identity == row["state_sha256"] == row["assembler_state_sha256"] and not np.any(state["lift"])
                and not np.any(state["fluctuation"][model["fixed_dofs"]]), "Peak state or fixed displacement differs")
        J,Hu = forces["J"],forces["Hu"]
        require(J.shape == (ne,9) and Hu.shape == (ne,2,2,2) and np.all(np.isfinite(J))
                and np.all(J > 0.) and np.all(np.isfinite(Hu)), "Saved J/Hu are invalid")
        body = model["workpiece_cells"]; body_mask = np.zeros(ne,dtype=bool); body_mask[body] = True
        require(not np.any(solid[body]), "Body overlay overlaps mechanism cells")
        medium = ~solid & ~body_mask; u = (state["lift"]+state["fluctuation"]).reshape(-1,2)
        require(np.all(u[model["workpiece_nodes"]] == 0.), "Fixed body moved")
        moved = coords+u; polygons = moved[conn]
        j_qp = np.argmin(J,axis=1); j_min = J[np.arange(ne),j_qp]
        hu_flat = Hu.reshape(ne,8); hu_comp = np.argmax(np.abs(hu_flat),axis=1)
        hu_signed = hu_flat[np.arange(ne),hu_comp]; hu_max = np.abs(hu_signed)
        def extrema(mask):
            ids = np.flatnonzero(mask); require(len(ids) > 0, "Empty source phase")
            ej = int(ids[np.argmin(j_min[ids])]); eh = int(ids[np.argmax(hu_max[ids])])
            return dict(elements=len(ids), minimum_saved_J=dict(value=float(j_min[ej]),element=ej,qp=int(j_qp[ej]),
                        natural_point=model["points"][j_qp[ej]].tolist()),
                        maximum_abs_saved_Hu_per_mm=dict(value=float(hu_max[eh]),signed_value=float(hu_signed[eh]),
                        element=eh,component=list(np.unravel_index(int(hu_comp[eh]),(2,2,2)))))
        phase_extrema = {name:extrema(mask) for name,mask in (("mechanism_solid",solid),("nonbody_medium",medium),("fixed_body_overlay",body_mask))}
        for item in phase_extrema.values(): item["maximum_abs_saved_Hu_per_mm"]["component"] = [int(x) for x in item["maximum_abs_saved_Hu_per_mm"]["component"]]
        checkpoint()
        csv_file = output/"peak_elements.csv"
        with csv_file.open("x",encoding="utf-8",newline="") as stream:
            writer = csv.writer(stream); writer.writerow(["element","source_phase","fixed_body_overlay","min_J_9_samples","min_J_qp",
                "max_abs_Hu_per_mm","signed_Hu_per_mm","Hu_i","Hu_J","Hu_K"])
            for e in range(ne): writer.writerow([e,"solid" if solid[e] else "medium",bool(body_mask[e]),repr(float(j_min[e])),int(j_qp[e]),
                repr(float(hu_max[e])),repr(float(hu_signed[e])),*np.unravel_index(int(hu_comp[e]),(2,2,2))])
        j_low,j_high = float(j_min.min()),float(j_min.max())
        j_norm = LogNorm(j_low,j_high if j_high > j_low else j_low*2.)
        hu_norm = Normalize(0.,max(float(hu_max.max()),1e-30))
        fig,axes = plt.subplots(2,2,figsize=(15,11)); fig.subplots_adjust(top=.86,bottom=.17,hspace=.28,wspace=.23)
        box = coords[model["workpiece_nodes"]]; local = (float(box[:,0].min()-4.),float(box[:,0].max()+4.),float(box[:,1].min()-4.),float(box[:,1].max()+2.))
        for column,(values,norm,cmap,title,units) in enumerate(((j_min,j_norm,"viridis","Minimum of 9 saved J samples","J (dimensionless; log color)"),
                (hu_max,hu_norm,"magma","Maximum absolute saved Hu[i,J,K]","|Hu| (1/mm)"))):
            for r in range(2):
                ax = axes[r,column]; collection = PolyCollection(polygons,cmap=cmap,norm=norm,edgecolors="none",rasterized=True)
                collection.set_array(values); ax.add_collection(collection)
                ax.add_collection(PolyCollection(polygons[body],facecolors="0.7",edgecolors="0.25",linewidths=.35))
                extreme = "minimum_saved_J" if column == 0 else "maximum_abs_saved_Hu_per_mm"
                for phase,color in (("mechanism_solid","deepskyblue"),("nonbody_medium","red")):
                    cell = polygons[phase_extrema[phase][extreme]["element"]]
                    closed = np.vstack((cell,cell[0]))
                    ax.plot(closed[:,0],closed[:,1],color=color,linewidth=1.1)
                ax.set_aspect("equal"); ax.set_title(("Full domain" if r == 0 else "Jaw/body window")+" · actual ×1\n"+title,fontsize=11)
                limits = (float(moved[:,0].min()-1.),float(moved[:,0].max()+1.),float(moved[:,1].min()-1.),float(moved[:,1].max()+1.)) if r == 0 else local
                ax.set_xlim(limits[:2]); ax.set_ylim(limits[2:]); ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
                fig.colorbar(collection,ax=ax,fraction=.037,pad=.02,label=units)
        fig.suptitle(f"Saved cycle010 peak: accepted index {peak}/{n-1} · mean input {row['d']:g} mm\nComplete path / same-result fresh {2*n} HP evaluations",fontsize=16)
        lines = []
        for name in ("mechanism_solid","nonbody_medium"):
            a,b = phase_extrema[name]["minimum_saved_J"],phase_extrema[name]["maximum_abs_saved_Hu_per_mm"]
            lines.append(f"{name}: min J={a['value']:.6g} at e{a['element']}/q{a['qp']}; max |Hu|={b['value']:.6g} 1/mm at e{b['element']}, component {tuple(b['component'])}")
        fig.text(.5,.105,"\n".join(lines),ha="center",fontsize=10)
        fig.text(.5,.047,"Grey: fixed body. Cell outlines: red = nonbody-medium extreme; cyan = mechanism-solid extreme (per column).\nJ: 9 saved reference samples, no continuous minimum. Hu[i,J,K]=u_i,JK: element-constant Q1 curvature. No contact/pressure inference.\nEnergy not evaluated. One PORT-direction HP scope, not all matrix columns.",ha="center",fontsize=9)
        image_file = output/"peak_saved_J_Hu.png"; fig.savefig(image_file,dpi=180,bbox_inches="tight"); plt.close(fig)
        checkpoint(); require(not any(k == "hf_eval" or k.startswith("hf_eval.") for k in sys.modules), "Unexpected mechanics module import")
        require(all(sha256(path.read_bytes()).hexdigest() == pin for path,pin in pins.items()), "Saved input changed")
        report.update(status="pass",source_sha256=pins[Path(__file__).resolve()],result_sha256=receipt["result_sha256"],
            reference_summary_sha256=pins[reference_file.resolve()],accepted_states=n,fresh_HP_calls=2*n,
            peak_accepted_index=peak,peak_original_target_index=row["original_target_index"],peak_d_mm=row["d"],peak_state_sha256=identity,
            raw_production_qualification={k:result[k] for k in ("independent_HP_qualified","equilibrium_qualified","HF_qualified")},
            external_reference_scope=reference["qualification"],phase_extrema=phase_extrema,csv_elements=ne,
            definitions=dict(J="minimum of the 9 saved J values per element; no continuous extreme",
                Hu="maximum absolute saved Hu[i,J,K]=u_i,JK component per element; no quadrature index",
                extrema_ties="first saved element, then first flattened sample/component",display="coordinates + saved lift + saved fluctuation, scale 1",
                outlines="saved polygons at each column's source-phase extrema; red nonbody medium, cyan mechanism solid",
                body="fixed overlay, excluded from nonbody-medium extrema, grey in display"),
            display_color_limits=dict(J=[j_low,j_high],Hu=[0.,float(hu_max.max())]),
            output_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in (csv_file,image_file)},
            input_files_sha256={p.relative_to(ROOT).as_posix():v for p,v in pins.items()},input_files_unchanged=True,
            no_new_energy_pressure_contact_clamping_or_all_columns_qualification=True,loaded_hf_eval_modules=[])
    except BaseException as error:
        report.update(status="fail",error_type=type(error).__name__,error=str(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,sampled_self_peak_RSS_bytes=peak_rss,
                      resource_scope="120 s helper / sampled self RSS 8 GiB; outer shared renderer controls whole tree")
        with (output/"peak_field_metadata.json").open("x",encoding="utf-8") as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write("\n")


if __name__ == "__main__": main()
