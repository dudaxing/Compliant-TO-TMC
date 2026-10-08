"""One explicit nested-geometry/model preparation; no force, tangent or solve."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    protocol_file = (root / args.protocol).resolve()
    protocol = json.loads(protocol_file.read_bytes())
    stage = protocol_file.parent
    output = stage / "run_001"
    assert not output.exists()
    sha = lambda p: sha256(p.read_bytes()).hexdigest()
    assert all(sha(root / name) == pin for name, pin in protocol["bindings"].items())
    output.mkdir()
    started = perf_counter()
    phase = dict(status="running", started_utc=datetime.now(timezone.utc).isoformat(),
                 geometry_writes_started=0, geometry_writes_completed=0,
                 model_builds_started=0, model_builds_completed=0,
                 model_saves_started=0, model_saves_completed=0,
                 renders_started=0, renders_completed=0)
    checks = {}

    def write(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    def checkpoint():
        phase["elapsed_seconds"] = perf_counter() - started
        phase["sampled_peak_helper_RSS_bytes"] = max(phase.get("sampled_peak_helper_RSS_bytes", 0), process.memory_info().rss)
        write(output / "phase.json", phase)
        assert not (stage / "stop_requested.txt").exists(), "Outer stop requested"
        assert phase["elapsed_seconds"] < protocol["phases"]["prepare"]["helper_seconds"], "Helper time exceeded"
        assert phase["sampled_peak_helper_RSS_bytes"] < protocol["sampled_RSS_bytes"], "Helper RSS exceeded"

    def check(name, condition):
        assert bool(condition), name
        checks[name] = True

    # These imports prepare operators and geometry only; no response entry is called.
    import psutil
    process = psutil.Process()
    try:
        checkpoint()
        sys.path.insert(0, str(root / "hf_repo/src"))
        import numpy as np
        from hf_eval.data import ARRAY_NAMES, load_geometry
        from hf_eval.nested_geometry import write_nested_geometry_2x2
        from hf_eval.native_project import build_native_project, write_native_project
        parent_file = root / protocol["parent_geometry"]
        parent = load_geometry(parent_file)
        old = json.loads((root / protocol["parent_model"]).read_bytes())
        check("parent_h1_84x40", parent.grid["shape_yx"] == [40, 84] and parent.grid["cell_size_mm"] == [1., 1.])
        check("parent_model_bound", old["source_geometry"]["geometry_id"] == parent.geometry_id and
              old["source_geometry"]["descriptor_sha256"] == parent.metadata["descriptor_sha256"])
        phase["geometry_writes_started"] = 1
        checkpoint()
        geometry_file = write_nested_geometry_2x2(parent_file, output / "geometry")
        phase["geometry_writes_completed"] = 1
        fine = load_geometry(geometry_file)
        check("fine_h05_168x80", fine.grid["shape_yx"] == [80, 168] and fine.grid["cell_size_mm"] == [.5, .5])
        for key in ("origin_mm", "extent_mm", "axes", "array_order", "value_location"):
            check("same_grid_" + key, fine.grid[key] == parent.grid[key])
        for key in ("region_tags", "thickness_mm", "model_extent", "source_record_ids"):
            check("same_" + key, fine.metadata[key] == parent.metadata[key])
        areas = {}
        for name in ARRAY_NAMES:
            for a in (0, 1):
                for b in (0, 1):
                    check(f"{name}_child_{a}{b}", np.array_equal(fine.arrays[name][a::2, b::2], parent.arrays[name]))
            areas[name] = dict(parent_mm2=int(parent.arrays[name].sum()), fine_mm2=float(fine.arrays[name].sum()) / 4)
            check(name + "_area", areas[name]["parent_mm2"] == areas[name]["fine_mm2"])
        check("new_geometry_identity", fine.geometry_id != parent.geometry_id)
        check("explicit_HF_derived_not_LF_native", fine.metadata["processing"]["whole_grid_is_LF_native"] is False)
        derivation = fine.metadata["provenance"]["hf_nested_mesh_derivations"][-1]
        check("parent_provenance_hashes", derivation["parent_hf_geometry"]["geometry_json_sha256"] == sha(parent_file)
              and derivation["parent_hf_geometry"]["geometry_npz_sha256"] == parent.metadata["arrays"]["sha256"])
        task = deepcopy(old["task"])
        task.update(task_id=old["task"]["task_id"] + "__HF_nested_h05",
                    geometry=dict(geometry_id=fine.geometry_id, descriptor_sha256=fine.metadata["descriptor_sha256"]),
                    purpose="same_design_nested_mesh_preparation",
                    parameter_origin="Exact 2x2 HF subdivision of the preserved W-API1 h1 supplied geometry; derived h0.5 grid, no LF optimization.",
                    description="Same 84x40mm domain, square center(71,40)/side18, original physical tags, material and 24-target path; native selects the supplied HF-derived h0.5 grid. Construction only; path not executed.")
        nonphysical = {"task_id", "geometry", "purpose", "parameter_origin", "description"}
        check("all_physical_task_fields_unchanged", {k:v for k,v in task.items() if k not in nonphysical} ==
              {k:v for k,v in old["task"].items() if k not in nonphysical})
        write(output / "task.json", task)
        phase["model_builds_started"] = 1
        checkpoint()
        project = build_native_project(geometry_file, task)
        phase["model_builds_completed"] = 1
        model = project.model
        regions = project.region_metadata
        check("fine_element_node_dof_counts", model.ne == 13440 and len(model.coordinates) == 13689 and model.ndof == 27378)
        check("same_material_constants", project.material == old["material"])
        check("same_qualification_status", project.qualification["status"] == old["qualification"]["status"])
        body = regions["workpiece"]
        check("aligned_square_counts", len(body["cells"]) == 648 and len(body["nodes"]) == 703 and len(body["dofs"]) == 1406)
        xy = model.coordinates
        check("physical_node_lattice", np.array_equal(xy.reshape(81, 169, 2)[:, :, 0],
              np.broadcast_to(np.arange(169) * .5, (81, 169))) and
              np.array_equal(xy.reshape(81, 169, 2)[:, :, 1], np.broadcast_to(np.arange(81)[:, None] * .5, (81, 169))))
        corners = xy[model.connectivity]
        check("physical_BL_BR_TR_TL_cells", np.array_equal(corners - corners[:, :1],
              np.broadcast_to([[0, 0], [.5, 0], [.5, .5], [0, .5]], corners.shape)))
        body_nodes = np.flatnonzero((xy[:, 0] >= 62) & (xy[:, 0] <= 80) & (xy[:, 1] >= 31) & (xy[:, 1] <= 40))
        check("square_nodes_from_physical_bounds", np.array_equal(body["nodes"], body_nodes))
        cell_centres = corners.mean(axis=1)
        body_cells = np.flatnonzero((cell_centres[:, 0] > 62) & (cell_centres[:, 0] < 80) &
                                   (cell_centres[:, 1] > 31) & (cell_centres[:, 1] < 40))
        check("square_cells_from_physical_bounds", np.array_equal(body["cells"], body_cells))
        check("body_cells_passive_void_only", np.all(fine.arrays["passive_void"].ravel()[body["cells"]] == 1))
        check("body_cells_no_solid_overlap", not np.any(model.solid[body["cells"]]))
        check("all_body_dofs_fixed", np.all(np.isin(body["dofs"], model.fixed_dofs)))
        check("fixed_free_disjoint_and_cover", len(np.intersect1d(model.fixed_dofs, model.free)) == 0 and
              np.array_equal(np.union1d(model.fixed_dofs, model.free), np.arange(model.ndof)))
        check("all_background_nodes_top_edge", np.array_equal(regions["background_symmetry"]["selected_nodes"], np.flatnonzero(xy[:, 1] == 40)))
        incident_nodes = np.unique(model.connectivity[model.solid])
        support_nodes = np.intersect1d(incident_nodes, np.flatnonzero((xy[:, 0] == 0) & (xy[:, 1] <= 8)))
        check("support_from_physical_attachment", np.array_equal(regions["support"]["attached_nodes"], support_nodes))
        symmetry_nodes = np.intersect1d(incident_nodes, np.flatnonzero((xy[:, 1] == 40) & (xy[:, 0] <= 60)))
        check("entity_symmetry_from_physical_attachment", np.array_equal(regions["entity_symmetry"]["attached_nodes"], symmetry_nodes))
        expected_fixed = np.unique(np.concatenate(((2 * support_nodes[:, None] + [0, 1]).ravel(),
              2 * np.flatnonzero(xy[:, 1] == 40) + 1, (2 * body_nodes[:, None] + [0, 1]).ravel())))
        check("merged_fixed_from_physical_boundaries", np.array_equal(model.fixed_dofs, expected_fixed))
        # Independent affine-field mean: exact normalized integral over each physical segment.
        u = np.column_stack((1 + 2 * xy[:, 0] + 3 * xy[:, 1], -2 + 4 * xy[:, 0] - xy[:, 1])).ravel()
        for name, vector in (("input", project.bin), ("output", project.bout)):
            port = regions["ports"][name]
            check(name + "_same_physical_segment", port["points_mm"] == old["region_metadata"]["ports"][name]["points_mm"])
            check(name + "_five_weights", np.array_equal(port["weights"], [.125, .25, .25, .25, .125]))
            check(name + "_no_fixed_direction", not np.any(vector[model.fixed_dofs]))
            centre = np.asarray(port["points_mm"]).mean(axis=0)
            mean = np.dot([1 + 2 * centre[0] + 3 * centre[1], -2 + 4 * centre[0] - centre[1]], port["direction"])
            check(name + "_affine_mean_integral", abs(float(vector @ u) - mean) <= 1e-12)
        check("cell_quadrature_measure", abs(float(model.ops["weights"].sum()) - .5 * .5 * 20) <= 1e-12)
        with np.load(root / protocol["parent_model_arrays"], allow_pickle=False) as saved:
            check("coarse_nodes_embedded_exactly", np.array_equal(xy.reshape(81, 169, 2)[::2, ::2].reshape(-1, 2), saved["coordinates"]))
            for name, factor in (("grad", 2), ("hessian", 4), ("weights", .25), ("points", 1)):
                check(name + "_physical_scaling", np.array_equal(model.ops[name], saved[name] * factor))
            check("kr_not_scaled_with_h", model.kr == float(saved["kr"]))
            for name in ("lam", "mu", "gamma"):
                parent_field = saved[name].reshape(40, 84)
                fine_field = getattr(model, name) if name != "gamma" else project.gamma
                fine_field = fine_field.reshape(80, 168)
                check(name + "_parent_child_values", all(np.array_equal(fine_field[a::2, b::2], parent_field)
                      for a in (0, 1) for b in (0, 1)))
        phase["model_saves_started"] = 1
        checkpoint()
        model_file = write_native_project(project, output / "model")
        phase["model_saves_completed"] = 1
        stored = json.loads(model_file.read_bytes())
        check("saved_model_archive_hash", sha(model_file.with_name(stored["arrays"]["path"])) == stored["arrays"]["sha256"])
        check("saved_model_no_response", stored["response_evaluated"] is False)
        check("saved_supplied_grid_native_only", stored["analysis_grid_policy"] == "native" and
              fine.metadata["processing"]["whole_grid_is_LF_native"] is False)
        # Read and validate the saved fields without constructing a second model.
        with np.load(model_file.with_name(stored["arrays"]["path"]), allow_pickle=False) as saved:
            for name, field in stored["arrays"]["fields"].items():
                array = saved[name]
                check("saved_field_" + name, list(array.shape) == field["shape"] and array.dtype.name == field["dtype"]
                      and sha256(array.tobytes(order="C")).hexdigest() == field["sha256"])
        phase["renders_started"] = 1
        checkpoint()
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        fig, axes = plt.subplots(1, 3, figsize=(14, 5), layout="constrained")
        for ax, geometry, title in zip(axes[:2], (parent, fine), ("Parent h=1 mm", "Derived h=0.5 mm")):
            ax.imshow(geometry.solid, origin="lower", extent=(0, 84, 0, 40), cmap="Blues", vmin=0, vmax=1, interpolation="nearest")
            ax.add_patch(Rectangle((62, 31), 18, 9, facecolor="0.75", edgecolor="black"))
            for name, colour in (("input", "orange"), ("output", "red")):
                p = np.asarray(geometry.metadata["region_tags"][name]["points_mm"])
                ax.plot(p[:, 0], p[:, 1], color=colour, linewidth=3, label=name)
            for name, colour in (("support", "green"), ("symmetry", "purple")):
                p = np.asarray(geometry.metadata["region_tags"][name]["points_mm"])
                ax.plot(p[:, 0], p[:, 1], color=colour, linewidth=2, label=name)
            ax.plot([0, 84], [40, 40], color="purple", linestyle=":", linewidth=1, label="background symmetry")
            ax.set(title=title, xlabel="x [mm]", ylabel="y [mm]", aspect="equal")
            ax.legend(fontsize=8)
        ax = axes[2]
        ax.imshow(fine.solid, origin="lower", extent=(0, 84, 0, 40), cmap="Blues", vmin=0, vmax=1, interpolation="nearest")
        ax.add_patch(Rectangle((62, 31), 18, 9, facecolor="0.75", edgecolor="black"))
        for h, colour, alpha in ((.5, "0.6", .5), (1., "black", .7)):
            for x in np.arange(76, 84 + h, h): ax.axvline(x, color=colour, alpha=alpha, linewidth=.5)
            for y in np.arange(27, 35 + h, h): ax.axhline(y, color=colour, alpha=alpha, linewidth=.5)
        port_nodes = xy[regions["ports"]["output"]["nodes"]]
        ax.scatter(port_nodes[:, 0], port_nodes[:, 1], c="red", s=20, zorder=4, label="5 output nodes")
        ax.set(xlim=(76, 84), ylim=(27, 35), aspect="equal", title="Same boundary / nested cells", xlabel="x [mm]", ylabel="y [mm]")
        ax.legend(fontsize=8)
        fig.suptitle("Undeformed geometry only — no force, displacement or contact result")
        fig.savefig(output / "nested_geometry.png", dpi=160)
        plt.close(fig)
        phase["renders_completed"] = 1
        checkpoint()
        check("all_bound_inputs_unchanged", all(sha(root / name) == pin for name, pin in protocol["bindings"].items()))
        outputs = {p.relative_to(stage).as_posix(): sha(p) for p in output.rglob("*") if p.is_file() and p.name != "phase.json"}
        report = dict(status="pass", checks=checks, physical_areas=areas, counts=regions["counts"],
                      ports=regions["ports"], material=project.material, task_sha256=project.task_hash,
                      parent_geometry_id=parent.geometry_id, derived_geometry_id=fine.geometry_id,
                      grid_ownership="native means this supplied HF-derived grid; not the original LF grid",
                      path_executed=False, mechanical_qualification=False, new_F_T_solver_HP_JIT_LF_calls=0,
                      output_files=outputs)
        write(output / "checks.json", report)
        checkpoint()
        phase["status"] = "pass"
    except Exception as error:
        phase.update(status="not_pass", failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        phase.update(completed_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=perf_counter() - started,
                     completed_checks=len(checks), new_F_T_solver_HP_JIT_LF_calls=0)
        write(output / "phase.json", phase)
        print(json.dumps(phase), flush=True)


if __name__ == "__main__":
    main()
