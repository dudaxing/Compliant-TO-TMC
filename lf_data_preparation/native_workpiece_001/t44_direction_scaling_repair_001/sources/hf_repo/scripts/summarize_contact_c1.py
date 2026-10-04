"""Read saved C1 evidence into an honest, possibly partial summary and figures.

No solver, production mechanics or high-precision evaluator is imported.
Only hash-bound independent-audit prefix values become comparison scores.
Production read-back remains explicitly diagnostic, never an HP substitute.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import fsum
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection


REPO = Path(__file__).resolve().parents[1]
KINDS = ("A0", "Aalpha", "TMC")
COLORS = {"A0": "#315b8a", "Aalpha": "#b46923", "TMC": "#187d72"}
STYLES = {.25: "--", .125: "-"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def finite(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if np.isfinite(number) else None


def read_npz(path):
    with np.load(path, allow_pickle=False) as data:
        result = {key: data[key] for key in data.files}
    if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in result.values()):
        raise ValueError("saved arrays must be finite ordinary primitives")
    return result


def inside(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or Path(relative).is_absolute():
        raise ValueError("expected a confined relative POSIX evidence path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("evidence path escapes declared root")
    return path


class Reader:
    def __init__(self, root):
        self.root = root
        self.bindings = {}

    def bind(self, path):
        path = path.resolve()
        key = path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else str(path)
        self.bindings[key] = sha(path)
        return self.bindings[key]

    def json(self, path, optional=False):
        if optional and not path.exists():
            return None
        self.bind(path)
        return read_json(path)

    def npz(self, path):
        self.bind(path)
        return read_npz(path)


def audit_binding_check(audit, run, root):
    """Validate the audit's original evidence, including portable root remaps."""
    bindings = audit.get("input_and_helper_sha256", {})
    if not isinstance(bindings, dict) or not bindings:
        return False, set(), ["audit has no input hash bindings"]
    checked, errors = set(), []
    for name, expected in bindings.items():
        try:
            if not isinstance(name, str) or not isinstance(expected, str):
                raise ValueError("non-string binding")
            path = Path(name)
            if not path.is_absolute():
                # The audit explicitly binds sibling preloads and unchanged
                # helper sources as ../ and ../../ paths, not just this run.
                if "\\" in name:
                    raise ValueError("audit binding must use POSIX separators")
                path = (run / name).resolve()
                if not path.is_relative_to(root.parent):
                    raise ValueError("audit binding escapes experiment workspace")
            if not path.is_file():
                # Audit records from another host may retain their old absolute
                # root. Remap only an explicit experiment-root suffix.
                parts = name.replace("\\", "/").split("/")
                if root.name not in parts:
                    raise ValueError("bound file is unavailable")
                tail = parts[parts.index(root.name) + 1:]
                path = inside(root, "/".join(tail))
            if sha(path) != expected:
                raise ValueError("hash differs")
            checked.add(path.resolve())
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
    return not errors, checked, errors


def phase_expected(phase, protocol):
    values = protocol["uniform_targets_mm"]
    gap = protocol["geometry"]["gap_mm"]
    if phase == "uniform_precontact":
        return [x for x in values if x <= gap]
    if phase == "uniform_closed":
        return [x - gap for x in values if x >= gap]
    return protocol["amplitude_targets_mm"] if phase == "perturbation" else values


def read_run(run, reader, protocol):
    meta = reader.json(run / "metadata.json")
    mode, kind, h = meta["mode"], meta["kind"], meta["h"]
    if kind not in KINDS or h not in STYLES or mode not in ("uniform", "perturbation"):
        raise ValueError("undeclared C1 run identity")
    if mode == "uniform" and kind == "Aalpha":
        raise ValueError("Aalpha uniform path is not a declared experiment")
    issues = []
    if meta.get("protocol") != protocol:
        issues.append("run protocol differs from the summary protocol")
    result = reader.json(run / "result.json", optional=True) or {}
    reader.json(run / "completion.json", optional=True)
    audit = reader.json(run / "audit.json", optional=True)
    audited, covered, binding_errors = False, set(), []
    hp_rows, prefix_rows = {}, {}
    if audit is not None:
        audited, covered, binding_errors = audit_binding_check(audit, run, reader.root)
        if audit.get("schema_version") != "contact-c1-independent-audit-1.0":
            audited = False
            binding_errors.append("unsupported independent audit schema")
        for row in audit.get("states", []):
            identity = row.get("state_id")
            if identity in hp_rows:
                audited = False
                binding_errors.append("duplicate audited state identity")
            hp_rows[identity] = row
        for row in audit.get("prefix", {}).get("states", []):
            identity = row.get("state_id")
            if identity in prefix_rows:
                audited = False
                binding_errors.append("duplicate audited prefix identity")
            prefix_rows[identity] = row
    issues.extend(binding_errors)
    stages_index = reader.json(run / "stages/index.json", optional=True) or {"stages": []}
    stages, states, last_display = [], [], None
    prefix_open = audited and not issues
    declared_phases = (["uniform_precontact", "uniform_closed"] if kind == "A0" else ["uniform_tmc"]) if mode == "uniform" else ["perturbation"]
    seen_phases = []
    for stage_entry in stages_index["stages"]:
        phase = stage_entry["phase_id"]
        if len(seen_phases) >= len(declared_phases) or phase != declared_phases[len(seen_phases)]:
            issues.append("stages are not in the declared chronological order")
            prefix_open = False
        seen_phases.append(phase)
        stage = inside(run, stage_entry["directory"])
        sm = reader.json(stage / "metadata.json", optional=True) or {}
        sr = reader.json(stage / "result.json", optional=True) or {}
        reader.json(stage / "completion.json", optional=True)
        index = reader.json(stage / "steps/index.json", optional=True) or {"steps": []}
        expected = phase_expected(phase, protocol)
        stage_info = dict(phase_id=phase, solver_status=sr.get("status", stage_entry.get("status", "unknown")),
                          independent_status=next((a.get("status", "unknown") for a in (audit or {}).get("stages", [])
                                                   if a.get("phase_id") == phase), "not_audited") if audited else "unknown",
                          requested_targets=expected, accepted_targets=[], accepted_count=len(index["steps"]),
                          result_accepted_count=len(sr.get("accepted_steps", [])) if sr else None,
                          target_reached=sr.get("target_reached"), failure=sr.get("failure"))
        stages.append(stage_info)
        model = None
        if (stage / "model.npz").exists():
            model = reader.npz(stage / "model.npz")
        records = sr.get("accepted_steps", [])
        for ordinal, entry in enumerate(index["steps"]):
            identity = f"{phase}:{entry['index']}"
            s = finite(entry.get("d"))
            if s is None:
                raise ValueError("nonfinite saved stage parameter")
            if entry.get("is_original_target") is True:
                stage_info["accepted_targets"].append(s)
            path = inside(stage / "steps", entry["file"])
            hp, prefix = hp_rows.get(identity, {}), prefix_rows.get(identity, {})
            record = records[ordinal] if ordinal < len(records) else {}
            row_issues = []
            arrays = None
            try:
                digest = reader.bind(path)
                if digest != entry.get("sha256"):
                    raise ValueError("saved-state index hash differs")
                arrays = reader.npz(path)
            except (OSError, ValueError) as error:
                row_issues.append(str(error))
            required = [path, stage / "model.npz", stage / "metadata.json", stage / "steps/index.json", stage / "result.json"]
            hp_trusted = audited and all(p.resolve() in covered for p in required)
            if hp and (hp.get("phase_id") != phase or hp.get("index") != entry["index"]
                       or finite(hp.get("parameter_s")) != s):
                row_issues.append("audit state identity differs from saved index")
                hp_trusted = False
            checks = {c["name"]: c for c in hp.get("checks", [])}
            comparable = bool(prefix_open and hp_trusted and not row_issues and hp.get("status") == "pass"
                              and prefix.get("comparable") is True and prefix.get("local_valid") is True
                              and finite(prefix.get("parameter_s")) == s)
            # The independent precontact row only supplies a zero score after
            # its rigid-translation branch checks pass; no production fallback.
            force = finite(prefix.get("normal_force")) if comparable else None
            if comparable and force is None:
                comparable = False
                row_issues.append("audited prefix has no finite force")
            if not comparable:
                prefix_open = False
                force = None
            offset = .25 if phase == "uniform_closed" else .375 if phase == "perturbation" else 0.
            declared_drive = offset + (0 if phase == "perturbation" else s)
            components = hp.get("force_components", {}).get("normal_top", {}) if hp_trusted else {}
            measures = hp.get("measurements", {}) if hp_trusted else {}
            residual_check = checks.get("hp80_relative_residual", {})
            raw_force = finite(hp.get("normal_force_raw")) if hp_trusted else None
            prod_group = record.get("group_reactions", {}).get("top", {})
            prod_force = finite(prod_group.get("constraint_force"))
            prod_force = -prod_force if prod_force is not None else None
            if prod_force is None and arrays is not None and model is not None and "group_top" in model:
                prod_force = -float(model["group_top"] @ arrays["internal_force"])
            production_norms = {}
            if arrays is not None:
                for label, key in (("material_force", "material_internal_force"),
                                   ("regularization_force", "regularization_internal_force")):
                    if key in arrays:
                        production_norms[label] = float(np.linalg.norm(arrays[key]))
            row = dict(state_id=identity, phase_id=phase, index=entry["index"], parameter_s=s,
                       declared_physical_mean_drive_mm=declared_drive,
                       physical_mean_drive_hp_mm=hp.get("physical_mean_drive") if hp_trusted else None,
                       comparison_coordinate=s if mode == "perturbation" else declared_drive,
                       original_target=entry.get("is_original_target") is True,
                       state_file=path.relative_to(reader.root).as_posix(), saved_sha256=entry.get("sha256"),
                       independent_status=hp.get("status", "unknown") if hp_trusted else "unknown",
                       comparable=comparable, normal_force_N=force,
                       force_authority="independent HP80 validated prefix" if comparable else "unknown; no score",
                       normal_force_hp_raw_N=raw_force, normal_force_production_raw_N=prod_force,
                       hp80_relative_residual=finite(residual_check.get("value", measures.get("hp80_relative_residual"))) if hp_trusted else None,
                       production_relative_residual=finite(record.get("relative_residual")),
                       hp_component_norms={k: finite(v) for k, v in measures.get("component_norms", {}).items()},
                       production_component_norms=production_norms,
                       hp_normal_components={k: finite(v) for k, v in components.items()},
                       hp_measurements=measures,
                       geometry=hp.get("geometry") if hp_trusted else None,
                       independent_checks=hp.get("checks", []) if hp_trusted else [], issues=row_issues)
            states.append(row)
            if arrays is not None and model is not None:
                xy = np.array([[fsum((float(model["coordinates"][i, k]), float(arrays["u_lift"][2*i+k]),
                                      float(arrays["u_fluctuation"][2*i+k]))) for k in (0, 1)]
                               for i in range(len(model["coordinates"]))])
                last_display = dict(xy=xy, connectivity=model["connectivity"], solid=model["solid"].astype(bool), row=row)
        stage_info["accepted_target_count"] = len(stage_info["accepted_targets"])
        stage_info["complete"] = bool(sr.get("status") == "success" and stage_info["accepted_targets"] == expected)
    complete = bool(result.get("status") == "success" and seen_phases == declared_phases
                    and all(s["complete"] for s in stages))
    admitted = bool(complete and audited and not issues and audit.get("status") == "pass"
                    and states and all(s["comparable"] for s in states))
    return dict(name=run.relative_to(reader.root).as_posix(), kind=kind, h_mm=h, mode=mode,
                solver_status=result.get("status", "incomplete"), independent_status=audit.get("status") if audit else "not_audited",
                audit_bindings_valid=audited, complete=complete, path_admitted=admitted, issues=issues,
                stages=stages, states=states, accepted_count=len(states),
                valid_prefix_count=sum(s["comparable"] for s in states),
                first_unscored_state=next((s["state_id"] for s in states if not s["comparable"]), None),
                missing_stages=[p for p in declared_phases if p not in seen_phases]), last_display


def comparable_points(run):
    # A0's verified closure state is stored on both sides of a stage handoff.
    # At that exact coordinate use the later phase, without interpolation.
    return {s["comparison_coordinate"]: s for s in run["states"] if s["comparable"]}


def differences(left, right, label):
    a, b = comparable_points(left), comparable_points(right)
    rows = []
    for x in sorted(a.keys() & b.keys()):
        fa, fb = a[x]["normal_force_N"], b[x]["normal_force_N"]
        rows.append(dict(coordinate=x, left_state_id=a[x]["state_id"], right_state_id=b[x]["state_id"],
                         left_force_N=fa, right_force_N=fb, left_minus_right_N=fa-fb,
                         relative_to_abs_right=None if fb == 0 else (fa-fb)/abs(fb)))
    return dict(label=label, left_run=left["name"], right_run=right["name"], states=rows,
                rule="exact common declared coordinates within both audited prefixes; no interpolation; later closure phase used")


def save_figure(fig, output, name):
    for extension in ("png", "svg"):
        fig.savefig(output / f"{name}.{extension}", dpi=180)
    plt.close(fig)


def line(ax, run, field, *, component=None, label=None, positive=False, prefix_only=True):
    for j, stage in enumerate(run["stages"]):
        rows = [s for s in run["states"] if s["phase_id"] == stage["phase_id"]]
        xx, yy = [], []
        for s in rows:
            value = s[field].get(component) if component else s.get(field)
            value = finite(value)
            if (prefix_only and not s["comparable"]) or (positive and value is not None and value <= 0):
                value = None
            xx.append(s["comparison_coordinate"])
            yy.append(np.nan if value is None else value)
        ax.plot(xx, yy, STYLES[run["h_mm"]], marker="o", ms=3, color=COLORS[run["kind"]],
                label=label if j == 0 else None)


def make_plots(runs, displays, protocol, output, partial):
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    prefix = "PARTIAL | " if partial else ""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), constrained_layout=True)
    for run in runs:
        label = f"{run['kind']}, h={run['h_mm']}"
        if run["mode"] == "uniform":
            line(axes[0], run, "normal_force_N", label=label)
            line(axes[1], run, "normal_force_N", label=label)
        else:
            line(axes[2], run, "normal_force_N", label=label)
    axes[0].set(title="Uniform loading: validated prefix", xlabel="Mean solid-bottom drive d (mm)", ylabel="Force on rigid plane (N)")
    axes[1].set(title="Before / at nominal closure: parasitic force", xlabel="Mean solid-bottom drive d (mm)", ylabel="Force on rigid plane (N)",
                xlim=(0, protocol["geometry"]["gap_mm"]))
    # Explicitly scale the parasite panel from preclosure evidence, not the
    # postclosure values drawn outside its x limits.
    pre = [s["normal_force_N"] for r in runs if r["mode"] == "uniform" for s in r["states"]
           if s["comparable"] and s["comparison_coordinate"] <= protocol["geometry"]["gap_mm"]]
    if pre:
        lo, hi = min(pre), max(pre)
        pad = max((hi-lo)*.12, max(abs(lo), abs(hi))*1e-3, 1e-12)
        axes[1].set_ylim(lo-pad, hi+pad)
    axes[2].set(title="PWL perturbation about d=0.375 mm", xlabel="Amplitude a (mm)", ylabel="Force on rigid plane (N)")
    for ax in axes:
        ax.grid(alpha=.2)
        if not any(np.any(np.isfinite(line.get_ydata())) for line in ax.lines):
            ax.text(.5, .5, "No audited prefix values", ha="center", transform=ax.transAxes, color="#68737d")
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=7)
    fig.suptitle(prefix + "C1 matched comparisons | HP80 only | lines stop at first unscored state")
    save_figure(fig, output, "c1_force_comparison")

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for i, mode in enumerate(("uniform", "perturbation")):
        for run in [r for r in runs if r["mode"] == mode]:
            label = f"{run['kind']}, h={run['h_mm']}"
            line(axes[i, 0], run, "hp80_relative_residual", label=label, positive=True)
            # Failed/non-prefix HP checks remain visible as unconnected crosses.
            raw = [s for s in run["states"] if not s["comparable"] and s["hp80_relative_residual"] is not None
                   and s["hp80_relative_residual"] > 0]
            axes[i, 0].scatter([s["comparison_coordinate"] for s in raw], [s["hp80_relative_residual"] for s in raw],
                               marker="x", s=35, color=COLORS[run["kind"]])
            for j, component in ((1, "material_force"), (2, "regularization_force")):
                line(axes[i, j], run, "hp_component_norms", component=component, label=label, positive=True)
        axes[i, 0].axhline(protocol["audit"]["relative_residual"], color="#ac3949", ls=":", label="Frozen HP gate")
        for j, title in enumerate(("HP80 residual / SF", "Material internal-force norm (N)", "HuHu internal-force norm (N)")):
            axes[i, j].set(title=f"{mode}: {title}", xlabel="d (mm)" if mode == "uniform" else "a (mm)", yscale="log")
            axes[i, j].grid(alpha=.2)
            if j > 0 and not any(np.any(np.isfinite(line.get_ydata())) for line in axes[i, j].lines):
                axes[i, j].text(.5, .5, "No positive audited values\n(exact zeros omitted)", ha="center",
                                transform=axes[i, j].transAxes, color="#68737d")
            if axes[i, j].get_legend_handles_labels()[0]:
                axes[i, j].legend(fontsize=7)
    fig.suptitle(prefix + "C1 independent precision and component magnitudes | exact zero omitted from log axes")
    save_figure(fig, output, "c1_precision_and_components")

    n = max(len(runs), 1)
    columns = min(3, n)
    rows = (n + columns - 1) // columns
    fig, axes = plt.subplots(rows, columns, figsize=(5*columns, 3.4*rows), squeeze=False, constrained_layout=True)
    rectangle = protocol["geometry"]["obstacle_rectangle_mm"]
    for ax, run in zip(axes.ravel(), runs):
        data = displays.get(run["name"])
        if data is None:
            ax.text(.5, .5, "No readable accepted state", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(run["name"], fontsize=8)
            continue
        xy, conn, solid = data["xy"], data["connectivity"], data["solid"]
        for mask, face, edge in ((~solid, "#e7ecef", "#b8c4cb"), (solid, COLORS[run["kind"]], "#273f50")):
            if np.any(mask):
                ax.add_collection(PolyCollection(xy[conn[mask]], facecolors=face, edgecolors=edge, linewidths=.35, alpha=.65))
        ax.plot(rectangle[:2], [rectangle[2]]*2, color="#242e38", lw=2)
        state = data["row"]
        label = "validated prefix" if state["comparable"] else "UNSCORED accepted state"
        ax.set_title(f"{run['kind']} {run['mode']}, h={run['h_mm']}\n{state['phase_id']}:s={state['parameter_s']:g} | {label}", fontsize=8)
        ax.set(xlabel="x (mm)", ylabel="y (mm)", aspect="equal",
               xlim=(min(float(xy[:, 0].min()), 0)-.15, max(float(xy[:, 0].max()), 2)+.15),
               ylim=(min(float(xy[:, 1].min()), 0)-.08, max(float(xy[:, 1].max()), rectangle[2])+.1))
    for ax in list(axes.ravel())[len(runs):]:
        ax.set_visible(False)
    if not runs:
        axes[0, 0].set_visible(True)
        axes[0, 0].text(.5, .5, "No C1 runs found", ha="center", transform=axes[0, 0].transAxes)
    fig.suptitle(prefix + "Last saved accepted state in each path | actual scale | rounded display only")
    save_figure(fig, output, "c1_last_accepted_deformation")


def summarize(root, output, selection_path=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not root.is_dir():
        raise ValueError("experiment root must exist")
    if output.exists():
        raise FileExistsError("refusing to overwrite a summary")
    reader = Reader(root)
    protocol_path = REPO / "configs/contact_c1_v1.json"
    protocol = reader.json(protocol_path)
    runs, displays, unreadable = [], {}, []
    # Directory names do not determine identity. Only the stored run schema does.
    for path in sorted(root.rglob("metadata.json")):
        try:
            metadata = read_json(path)
            if metadata.get("schema") != "contact_c1_run_v1":
                continue
            run, display = read_run(path.parent, reader, protocol)
            runs.append(run)
            displays[run["name"]] = display
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            unreadable.append(dict(path=path.relative_to(root).as_posix(), error=str(error)))
    expected = [(mode, kind, h) for mode, kinds in (("uniform", ("A0", "TMC")), ("perturbation", KINDS))
                for kind in kinds for h in protocol["mesh_sizes_mm"]]
    chosen_names, superseded = {}, {}
    selection_evidence = None
    if selection_path is not None:
        selection_path = Path(selection_path).resolve()
        selection_evidence = reader.json(selection_path)
        if selection_evidence.get("schema") != "contact_c1_summary_selection_v1":
            raise ValueError("unsupported explicit selection schema")
        for entry in selection_evidence["runs"]:
            key = (entry["mode"], entry["kind"], entry["h"])
            name = inside(root, entry["run"]).relative_to(root).as_posix()
            if key not in expected or key in chosen_names or name in chosen_names.values():
                raise ValueError("selection must declare each expected combination and run exactly once")
            chosen_names[key] = name
        if set(chosen_names) != set(expected):
            raise ValueError("explicit selection must name all ten combinations, including unexecuted ones")
        for entry in selection_evidence.get("superseded", []):
            name = inside(root, entry["run"]).relative_to(root).as_posix()
            if name in superseded or name in chosen_names.values() or not entry.get("reason"):
                raise ValueError("superseded runs need a distinct name and explicit reason")
            superseded[name] = entry["reason"]
    selection, missing, ambiguous = {}, [], []
    for key in expected:
        matches = [r for r in runs if (r["mode"], r["kind"], r["h_mm"]) == key]
        identity = dict(mode=key[0], kind=key[1], h_mm=key[2])
        if chosen_names:
            identity["selected_run"] = chosen_names[key]
            matches = [r for r in matches if r["name"] == chosen_names[key]]
        if not matches:
            missing.append(identity)
        elif len(matches) > 1:
            ambiguous.append(dict(**identity, runs=[r["name"] for r in matches]))
        else:
            selection[key] = matches[0]
    for run in runs:
        run["selected_for_current_comparison"] = run in selection.values()
        run["superseded_reason"] = superseded.get(run["name"])
        if chosen_names and not run["selected_for_current_comparison"] and run["name"] not in superseded:
            ambiguous.append(dict(run=run["name"], reason="observed run is neither selected nor explicitly superseded"))
    comparisons, sensitivity = [], []
    for mode, left_kind, right_kind in (("uniform", "TMC", "A0"), ("perturbation", "Aalpha", "A0"),
                                       ("perturbation", "TMC", "Aalpha"), ("perturbation", "TMC", "A0")):
        for h in protocol["mesh_sizes_mm"]:
            left, right = selection.get((mode, left_kind, h)), selection.get((mode, right_kind, h))
            if left and right:
                comparisons.append(differences(left, right, f"{mode} {left_kind} minus {right_kind}, h={h}"))
    for mode, kind, _ in expected[::2]:
        coarse, fine = selection.get((mode, kind, .25)), selection.get((mode, kind, .125))
        if coarse and fine:
            sensitivity.append(differences(coarse, fine, f"{mode} {kind}: coarse minus fine; sensitivity only"))
    receipts = []
    for path in sorted(root.glob("*.receipt.json")):
        receipt = reader.json(path)
        command = receipt.get("command", [])
        script = Path(command[1]).name if len(command) > 1 else "unknown"
        action = "solve" if script.startswith("run_contact_c1") else "audit" if script.startswith("audit_contact_c1") else "other"
        receipts.append(dict(file=path.name, action=action, elapsed_seconds=finite(receipt.get("elapsed_seconds")),
                             returncode=receipt.get("returncode"), timed_out=receipt.get("timed_out")))
    selected_runs = list(selection.values())
    partial = bool(missing or ambiguous or unreadable or len(selected_runs) != len(expected)
                   or any(not r["path_admitted"] for r in selected_runs))
    payload = dict(schema_version="contact-c1-summary-1.0", created_utc=datetime.now(timezone.utc).isoformat(),
                   status="partial" if partial else "complete", expected_paths=len(expected), observed_runs=len(runs),
                   admitted_paths=sum(r["path_admitted"] for r in runs),
                   selected_paths=len(selected_runs), selected_admitted_paths=sum(r["path_admitted"] for r in selected_runs),
                   selection=selection_evidence, superseded_runs=superseded,
                   accepted_states=sum(r["accepted_count"] for r in runs),
                   validated_prefix_states=sum(r["valid_prefix_count"] for r in runs),
                   independent_checks=sum(len(s["independent_checks"]) for r in runs for s in r["states"]),
                   independent_checks_passed=sum(c.get("status") == "pass" for r in runs for s in r["states"] for c in s["independent_checks"]),
                   runs=runs, not_executed_combinations=missing, ambiguous_combinations=ambiguous,
                   unreadable_records=unreadable, matched_comparisons=comparisons, mesh_sensitivity=sensitivity,
                   subprocess_receipts=receipts, solve_attempts=sum(r["action"] == "solve" for r in receipts),
                   audit_attempts=sum(r["action"] == "audit" for r in receipts), input_sha256=reader.bindings,
                   summary_script_sha256=sha(__file__), protocol_sha256=sha(protocol_path),
                   scope=["Restricted matched C1 task; no general active set, parameter convergence, gripper or ranking admission.",
                          "Aalpha is a regularized-solid diagnostic, not a new physical truth. Differences are coupled model outcomes, not independent additive error mechanisms.",
                          "TMC total plane force includes background-medium and boundary effects; the nodal body/outer reaction partition is not a physical contact-force separation.",
                          "Two grids give sensitivity, not convergence, an error bound or a smooth-Hessian result for the kinked PWL trace.",
                          "Only exact common declared coordinates in both audited prefixes are compared. No gap interpolation or recovery after first invalid/unknown state.",
                          "Accepted counts include inserted states and separately stored stage-handoff states; they are not independent experiments.",
                          "Missing audits remain unknown. A0 precontact zero is supplied only by a passing independent rigid-translation audit.",
                          "Force/component values used for comparison are independent HP80; separately named production values and rounded deformation are diagnostic only."])
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    make_plots(selected_runs, displays, protocol, output, partial)
    print(json.dumps({key: payload[key] for key in ("status", "observed_runs", "admitted_paths", "accepted_states", "validated_prefix_states")}))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--selection", help="Predeclared selection JSON; all other attempts remain in the summary")
    args = parser.parse_args()
    summarize(args.root, args.output, args.selection)
