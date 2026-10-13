"""Compose explicitly named saved JSON observations; never read scientific/media bytes."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import argparse
import json


SCHEMA = "mpath1-composed-observations-1.0"
STATUS_FIELDS = ("status", "failure", "production_converged", "target_reached",
                 "task_target_executed", "path_completed", "loading_peak_reached",
                 "unload_endpoint_reached", "full_original_path_completed",
                 "full_extended_path_completed", "independent_HP_qualified",
                 "equilibrium_qualified", "HF_qualified", "qualification_scope")


def _path(repo, name, suffix):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix.lower() != suffix:
        raise ValueError("Require an explicit repo-relative " + suffix + " path: " + str(name))
    path = (repo / relative).resolve()
    if not path.is_relative_to(repo):
        raise ValueError("Input escapes the supplied repository")
    return path


def _read(repo, name, checkpoint):
    checkpoint()
    raw = _path(repo, name, ".json").read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object: " + name)
    checkpoint()
    return value, sha256(raw).hexdigest()


def _same(left, right):
    # JSON spelling preserves signed zero; no tolerance, rounding or derived physics.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def compose_path(repo: Path, spec: dict, checkpoint=lambda: None) -> dict:
    """Return observations/provenance only; the caller owns output and its clock."""
    repo = Path(repo).resolve()
    if spec["schema_version"] != "mpath1-compose-spec-1.0" or not spec["segments"]:
        raise ValueError("Require the explicit ordered segment spec")
    sources, raw_rows, unique_rows, joins, loaded = [], [], [], [], {}
    previous = None
    for item in spec["segments"]:
        checkpoint()
        label = item["label"]
        if label in loaded:
            raise ValueError("Duplicate source label: " + label)
        result, result_pin = _read(repo, item["result"], checkpoint)
        summary, summary_pin = _read(repo, item["viewer_summary"], checkpoint)
        model, model_pin = _read(repo, item["model"], checkpoint)
        view, view_pin = _read(repo, item["view_descriptor"], checkpoint)
        descriptor = (_path(repo, item["result"], ".json").parent / result["model"]["descriptor_path"]).resolve()
        assert descriptor == _path(repo, item["model"], ".json")
        assert model_pin == result["model"]["descriptor_file_sha256"]
        assert model["task_sha256"] == result["task_sha256"]
        states, visible = result["states"], summary["rows"]
        assert states and len(states) == result["accepted_states"] == summary["accepted_states"] == len(visible)
        assert summary["production_status"] == result["status"]
        assert view["status"] == "pass" and view["new_F_T_model_solver_HP_calls"] == 0
        assert view["mechanical_hooks_monitored"] is False and view["contact_pressure_clamping_qualified"] is False
        assert len(view["cases"]) == 1
        case = view["cases"][0]
        view_file = _path(repo, item["view_descriptor"], ".json")
        assert _path(repo, item["viewer_summary"], ".json") == view_file.parent / case["label"] / "summary.json"
        assert _path(repo, item["gif"], ".gif") == view_file.parent / case["label"] / "actual_states.gif"
        assert case["label"] == _path(repo, item["result"], ".json").parent.name
        assert case["production_status"] == result["status"] and case["production_path_completed"] == result["path_completed"]
        assert case["unload_endpoint_reached"] == result["unload_endpoint_reached"]
        assert case["saved_accepted_states"] == case["observed_states"] == len(states)
        assert case["reference_available"] == summary["reference_available"]
        assert case["task"] == model["task"] and case["model_sha256"] == model["arrays"]["sha256"]
        assert view["input_source_bindings"][item["result"]] == result_pin
        assert view["input_source_bindings"][item["model"]] == model_pin
        assert case["label"] + "/summary.json" in view["outputs"] and case["label"] + "/actual_states.gif" in view["outputs"]
        assert all(view[key] == len(states) for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed"))
        options = dict(response_mode=result["response_mode"], tangent_mode=result["tangent_execution"]["mode"], initial_guess=result["initial_guess"])
        task = model["task"]
        if previous is not None:
            old_task = previous["model"]["task"]
            assert task["path"]["targets_mm"][:len(old_task["path"]["targets_mm"])] == old_task["path"]["targets_mm"]
            expected = deepcopy(task); expected["path"]["targets_mm"] = old_task["path"]["targets_mm"]
            assert expected == old_task and model["material"] == previous["model"]["material"]
            assert result["source_geometry"] == previous["result"]["source_geometry"]
            assert options == previous["source"]["options"]
            assert {k:v for k,v in result["settings"].items() if k != "time_limit_seconds"} == {k:v for k,v in previous["result"]["settings"].items() if k != "time_limit_seconds"}
            continuation = result["continuation"]
            assert continuation["parent_result"]["sha256"] == previous["source"]["result_SHA256"]
            assert continuation["parent_model"]["sha256"] == previous["source"]["model_SHA256"]
            assert continuation["parent_result"]["path"].replace("\\", "/").endswith("/" + previous["source"]["result"])
            assert continuation["parent_status"] == previous["result"]["status"] and continuation["parent_failure"] == previous["result"]["failure"]
            assert continuation.get("parent_continuation") == previous["result"].get("continuation")
            selected = continuation["selected_state"]
            assert selected["accepted_index"] == len(previous["result"]["states"]) - 1
            assert selected["state_sha256"] == states[0]["state_sha256"]
            assert states[0]["continuation_anchor"] is True and continuation["anchor_identity_preserved"] is True
            assert _same(selected["R_input_N"], states[0]["R_input"]) and _same(selected["d_mm"], states[0]["d"])
            assert selected["original_target_index"] == states[0]["original_target_index"]
        gif = _path(repo, item["gif"], ".gif")
        source = dict(label=label, result=item["result"], result_SHA256=result_pin,
                      viewer_summary=item["viewer_summary"], viewer_summary_SHA256=summary_pin,
                      view_descriptor=item["view_descriptor"], view_descriptor_SHA256=view_pin,
                      viewer_provenance=dict(case=deepcopy(case), status=view["status"], failure=deepcopy(view["failure"]),
                          original_result_pin=view["input_source_bindings"][item["result"]],
                          original_model_pin=view["input_source_bindings"][item["model"]],
                          mechanical_hooks_monitored=view["mechanical_hooks_monitored"],
                          zero_mechanics_basis=view["zero_mechanics_basis"],
                          contact_pressure_clamping_qualified=view["contact_pressure_clamping_qualified"]),
                      model=item["model"], model_SHA256=model_pin, accepted_states=len(states),
                      status={k:deepcopy(result[k]) for k in STATUS_FIELDS if k in result},
                      task=deepcopy(task), task_sha256=result["task_sha256"], settings=deepcopy(result["settings"]),
                      options=options, source_geometry=deepcopy(result["source_geometry"]),
                      source_version_metadata={k:deepcopy(result[k]) for k in ("mechanics_source_sha256", "source_binding_scope", "backend", "response_contract", "force_kernel_version", "tangent_version") if k in result},
                      model_source_metadata={k:deepcopy(model[k]) for k in ("reference_source_manifest", "source_provenance_path_context") if k in model},
                      continuation=deepcopy(result.get("continuation")),
                      viewer_reference_available=summary["reference_available"],
                      gif=dict(repo_relative_path=item["gif"], exists_stat_only=gif.is_file(),
                               link_from_run_001="../../../../" + item["gif"], decoded_or_hashed=False))
        sources.append(source)
        local_raw = []
        for index, (state, row) in enumerate(zip(states, visible)):
            checkpoint()
            assert row["index"] == index and row["state_sha256"] == state["state_sha256"]
            assert row["original_target_index"] == state["original_target_index"] and row["leg"] == state["leg"]
            assert _same([row["d_mm"], row["R_input_N"], row["q_out_mm"]], [state["d"], state["R_input"], state["q_out"]])
            entry = dict(raw_index=len(raw_rows), source=dict(segment=label, accepted_index=index,
                         result=item["result"], source_result_SHA256=result_pin, viewer_summary=item["viewer_summary"]),
                         result_state=deepcopy(state), observations=deepcopy(row), q_in_mm=state["q_in"])
            raw_rows.append(entry); local_raw.append(entry)
            if previous is not None and index == 0:
                left = previous["last_raw"]
                fields = ("state_sha256", "d", "original_target_index", "R_input", "q_in", "q_out", "is_original_target")
                assert _same({k:left["result_state"][k] for k in fields}, {k:state[k] for k in fields})
                assert _same({k:v for k,v in left["observations"].items() if k not in ("index", "leg")}, {k:v for k,v in row.items() if k not in ("index", "leg")})
                unique_rows[-1]["source_occurrences"].append(entry["raw_index"])
                joins.append(dict(left_raw_index=left["raw_index"], right_raw_index=entry["raw_index"],
                                  unique_index=unique_rows[-1]["unique_index"], state_sha256=state["state_sha256"],
                                  original_target_index=state["original_target_index"], d_mm=state["d"],
                                  identity_fields=list(fields), all_visible_observations_equal_except=["index", "leg"]))
            else:
                unique_rows.append(dict(deepcopy(entry), unique_index=len(unique_rows), source_occurrences=[entry["raw_index"]]))
        previous = dict(source=source, result=result, model=model, last_raw=local_raw[-1])
        loaded[label] = dict(source=source, result=result, model=model, raw=local_raw)
    originals = [row for row in unique_rows if row["result_state"]["is_original_target"]]
    final_targets = sources[-1]["task"]["path"]["targets_mm"]
    assert [row["result_state"]["original_target_index"] for row in originals] == list(range(len(final_targets)))
    assert _same([row["result_state"]["d"] for row in originals], final_targets)
    for key, observed in (("expected_raw_rows", len(raw_rows)), ("expected_unique_rows", len(unique_rows))):
        if key in spec: assert spec[key] == observed
    references, coverage = [], []
    for item in spec.get("references", []):
        # Ordinary summary identity only; never read/hash its scientific reference sources.
        ref, summary_pin = _read(repo, item["summary"], checkpoint)
        assert ref["accepted_states"] == len(ref["states"])
        origin = loaded[item["source_segment"]]
        assert ref["result_sha256"] == origin["source"]["result_SHA256"]
        metadata = {k:deepcopy(v) for k,v in ref.items() if k != "states"}
        states_metadata = []
        for state in ref["states"]:
            checkpoint()
            child_index = state["child_accepted_index"]
            occurrence = origin["raw"][child_index]
            actual = occurrence["result_state"]
            assert state["index"] == child_index and state["state_sha256"] == actual["state_sha256"]
            assert state["original_target_index"] == actual["original_target_index"] and state["leg"] == actual["leg"]
            assert _same(state["target_mm"], actual["d"])
            fields = ("status", "index", "child_accepted_index", "child_original_target_index", "original_target_index", "state_sha256", "target_mm", "leg", "continuation_anchor", "reference_execution_index", "descriptor_file_sha256", "references", "global_references")
            states_metadata.append({k:deepcopy(state[k]) for k in fields if k in state})
            unique = next(row for row in unique_rows if occurrence["raw_index"] in row["source_occurrences"])
            coverage.append(dict(reference_label=item["label"], summary=item["summary"], source_segment=item["source_segment"],
                                 source_result=origin["source"]["result"], source_result_SHA256=ref["result_sha256"],
                                 source_child_index=child_index, source_raw_index=occurrence["raw_index"], unique_index=unique["unique_index"],
                                 state_sha256=actual["state_sha256"], original_target_index=actual["original_target_index"],
                                 target_mm=state["target_mm"], reference_state_status=state["status"],
                                 displayed_same_identity_raw_indices=deepcopy(unique["source_occurrences"]),
                                 qualification_scope="Exact original source result/state only; same-state display duplicates do not acquire HP qualification"))
        references.append(dict(label=item["label"], summary=item["summary"], summary_SHA256=summary_pin, source_segment=item["source_segment"],
                               summary_metadata=metadata, state_metadata=states_metadata, scientific_reference_core_bytes_rehashed=False))
    checkpoint()
    return dict(schema_version=SCHEMA, status="composed_saved_observations", sources=sources,
                raw_rows=raw_rows, unique_rows=unique_rows, anchor_join_ledger=joins,
                counts=dict(source_segments=len(sources), raw_rows=len(raw_rows), unique_rows=len(unique_rows), shared_anchors=len(joins)),
                original_target_coverage=dict(indices=[r["result_state"]["original_target_index"] for r in originals], targets_mm=deepcopy(final_targets)),
                references=references, reference_coverage=coverage,
                composition_claims=dict(single_full_path_producer_run=False, full_path_reference_qualified=False,
                                        pressure_qualified=False, effective_clamp_qualified=False, stability_qualified=False, HF5_qualified=False),
                scientific_calls=0, scientific_or_media_bytes_read_or_hashed=0,
                scope="Chronological saved observations across separately executed sources; original failure/status/task/qualification records retained")


def build_index(data: dict) -> dict:
    return {"schema_version": "mpath1-path-index-1.0", "counts": deepcopy(data["counts"]),
            "sources": deepcopy(data["sources"]), "anchor_join_ledger": deepcopy(data["anchor_join_ledger"]),
            "references": deepcopy(data["references"]),
            "reference_coverage": deepcopy(data["reference_coverage"]), "composition_claims": deepcopy(data["composition_claims"]),
            "rows": [{"unique_index":r["unique_index"], "global_target_index":r["result_state"]["original_target_index"],
                      "d_mm":r["observations"]["d_mm"], "state_sha256":r["observations"]["state_sha256"],
                      "primary_source":deepcopy(r["source"]),
                      "source_aliases":[deepcopy(data["raw_rows"][i]["source"]) for i in r["source_occurrences"]],
                      "source_occurrences":deepcopy(r["source_occurrences"])} for r in data["unique_rows"]]}


def markdown(data: dict) -> str:
    def show(value):
        if isinstance(value, float): return format(value, ".12g")
        return str(value).replace("|", "\\|").replace("\n", " ")
    counts = data["counts"]
    lines = ["# Saved path observations", "",
             f"{counts['source_segments']} separately executed sources: {counts['raw_rows']} original rows retained; {counts['shared_anchors']} identical boundary anchors; {counts['unique_rows']} chronological display rows.", "",
             "Source statuses and task identities remain separate. This display does not turn the failed initial run or the separate children into one full-path producer/reference PASS.", "",
             "Recorded mechanics versions span different source eras; their original dictionaries remain in each JSON source entry. Shared-state observation identity does not assert identical mechanics source bytes.", "",
             "| Source | Original status | Saved rows | Original task targets | Existing GIF (repo root relative) |",
             "| --- | --- | --- | --- | --- |"]
    for source in data["sources"]:
        gif = source["gif"]
        link = f"[{source['label']}]({gif['link_from_run_001']})" if gif["exists_stat_only"] else "Absent (stat only)"
        lines.append(f"| {source['label']} | {source['status']['status']} | {source['accepted_states']} | {len(source['task']['path']['targets_mm'])} | {link} |")
    lines += ["", "GIFs are linked only: no concatenation, frame decoding, hashing or deformation replot.", "",
              "| Unique/global | Original leg | d mm | qin mm | Signed R N | qout mm | Finite bottom distance mm | Solid min J | Solid max Green principal | Medium max abs Hu /mm | Raw source indices |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for entry in data["unique_rows"]:
        row = entry["observations"]
        values = [str(entry["unique_index"])+"/"+str(row["original_target_index"]), row["leg"], row["d_mm"], entry["q_in_mm"], row["R_input_N"], row["q_out_mm"], row["tip_to_bottom_mm"], row["solid_min_J"], row["solid_Green_principal_max"], row["medium_max_abs_Hu_per_mm"], entry["source_occurrences"]]
        lines.append("| " + " | ".join(show(v) for v in values) + " |")
    lines += ["", "| Unique/global | Total Fx N | Total Fy N | Material Fx N | Material Fy N | Hu Fx N | Hu Fy N |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for entry in data["unique_rows"]:
        row = entry["observations"]
        values = [str(entry["unique_index"])+"/"+str(row["original_target_index"])] + [row[c+"_body_F"+axis+"_N"] for c in ("total", "material", "regularization") for axis in ("x", "y")]
        lines.append("| " + " | ".join(show(v) for v in values) + " |")
    lines += ["", "## Existing reference metadata", "", "Coverage belongs to the exact original result and child state below. A duplicate anchor in the display does not transfer that qualification to another source or to the composed path.", "", "| Reference | Exact source child | Unique/global | d mm | Original state status |", "| --- | --- | --- | --- | --- |"]
    for ref in data["reference_coverage"]:
        lines.append(f"| {ref['reference_label']} | {ref['source_segment']}:{ref['source_child_index']} | {ref['unique_index']}/{ref['original_target_index']} | {show(ref['target_mm'])} | {ref['reference_state_status']} |")
    for ref in data["references"]:
        lines += ["", f"{ref['label']}: " + ref["summary_metadata"].get("qualification", ref["summary_metadata"].get("reference_scope", "Original scope recorded in JSON"))]
    lines += ["", "Signed fixed-workpiece weak-form totals include material and Hu. Finite tip-to-segment distances are unsigned saved observations; zero input is an endpoint, not a pressure, effective clamp, complete release, stability or HF5 qualification.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if args.spec.suffix.lower() != ".json": raise ValueError("Spec must be ordinary JSON")
    print(json.dumps(compose_path(args.repo, json.loads(args.spec.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__": main()
