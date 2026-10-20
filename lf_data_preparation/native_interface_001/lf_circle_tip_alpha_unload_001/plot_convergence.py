"""Circle alpha=2.5e-7 first-unload copy of the saved-result convergence observer; no mechanics.

Data projection and plotting algorithms retain the frozen third-cycle source.
Only the case/title and explicit observer provenance metadata are generalized.
"""

from hashlib import sha256
import json
from pathlib import Path


STATE_FIELDS = (
    "d", "physical_mean_target_mm", "R_input", "q_in", "q_out",
    "relative_residual", "free_force_residual_norm", "residual_scale",
    "constraint_residual", "constraint_bound", "relative_global_force_balance",
    "global_force_balance_scale", "minimum_J", "newton_checks",
    "original_target_displacement", "original_target_index", "is_original_target",
    "bisection_depth", "elapsed_seconds", "state_sha256", "leg",
)


def plot_convergence(result_file, output_dir, checkpoint=lambda event: None, *, label, title=None):
    """Write one ordinary JSON projection and one PNG from the new result JSON.

    The output directory must be new. Zero residuals remain zero on a symlog
    axis. A check group starts when the recorded target changes or the Newton
    check counter restarts; it is not a separately recorded controller attempt.
    """
    title = title if title is not None else f"{label}: actual saved alpha-unload convergence"
    checkpoint("convergence_read_started")
    source = Path(result_file).resolve()
    raw = source.read_bytes()
    result = json.loads(raw)
    diagnostics = result["path_diagnostics"]
    history = diagnostics["newton_history"]
    states = [{key: row[key] for key in STATE_FIELDS if key in row}
              for row in result["states"]]
    tolerance = result["settings"]["tolerance"]
    groups = []
    previous = None
    for ordinal, row in enumerate(history, 1):
        if (previous is None or row["d"] != previous["d"]
                or row["newton_check"] <= previous["newton_check"]):
            groups.append({"group": len(groups) + 1, "d_mm": row["d"],
                           "first_ordinal": ordinal, "last_ordinal": ordinal,
                           "raw_history_indices_zero_based": []})
        groups[-1]["last_ordinal"] = ordinal
        groups[-1]["raw_history_indices_zero_based"].append(ordinal - 1)
        previous = row
    trials = diagnostics["trials"]
    counts = dict(accepted_states=len(states), newton_base_checks=len(history),
                  inferred_check_groups=len(groups), line_search_trials=len(trials),
                  line_search_accepted=sum(row["accepted"] is True for row in trials),
                  line_search_rejected=sum(row["accepted"] is False for row in trials),
                  failed_attempts=len(diagnostics["failed_attempts"]),
                  linear_solves=len(diagnostics["linear_solve_diagnostics"]),
                  maximum_bisection_depth=diagnostics["maximum_bisection_depth"],
                  zero_newton_residuals=sum(row["relative_residual"] == 0 for row in history))
    scales = {"relative_residual_symlog_linear_threshold": tolerance * 1e-4,
              "constraint_mm_symlog_linear_threshold": 1e-16}
    report = dict(
        schema_version="hf-labelled-convergence-observation-1.0",
        scope="Saved ordinary result observation; no mechanics re-evaluation",
        display_context=dict(label=label, title=title,
            observer_source=dict(path=str(Path(__file__).resolve()),
                sha256=sha256(Path(__file__).read_bytes()).hexdigest()),
            historical_source="lf_data_preparation/native_interface_001/lf_third_cycle_001/plot_convergence.py",
            historical_source_sha256="559d01596d5a75ea6f61f38b76e2fca3029e2ca8969b7be4daea415127fe1bef",
            adaptation="Case/title and observer provenance only; original data and plotting algorithms retained"),
        source=dict(file=str(source), sha256=sha256(raw).hexdigest(), bytes=len(raw)),
        result_metadata={key: result[key] for key in (
            "schema_version", "scope", "status", "production_converged",
            "target_reached", "targets_mm", "task_target_mm", "task_target_executed",
            "reached_displacement", "path_completed", "loading_peak_reached",
            "unload_endpoint_reached", "settings", "failure", "timing_seconds",
            "independent_HP_qualified", "equilibrium_qualified", "HF_qualified",
            "path_kind", "full_original_path_completed", "full_extended_path_completed",
            "new_peak_reached", "extended_segment_completed", "continuation")
            if key in result},
        counts=counts, accepted_state_field_projection=list(STATE_FIELDS),
        accepted_states=states, raw_newton_history=history, inferred_check_groups=groups,
        raw_line_search_trials=trials, raw_failed_attempts=diagnostics["failed_attempts"],
        raw_linear_solve_diagnostics=diagnostics["linear_solve_diagnostics"],
        raw_path_timing_seconds=diagnostics["timing_seconds"], plot_scales=scales,
        accepted_state_display_axis=dict(
            kind="zero_based_accepted_state_index_in_original_order",
            tick_label="accepted-state index, then actual d in mm",
            records=[dict(index=index, d_mm=row["d"], leg=row.get("leg"))
                     for index, row in enumerate(states)]),
        plot_notes=[
            "Every recorded Newton base check is shown, in source order, with no filtering.",
            "Groups are inferred from target changes/counter restarts; an attempt failing before its first base check has no group.",
            "Symlog axes preserve exact zero. Linear thresholds change axis display only; no residual is clipped or replaced.",
            "Accepted-state markers use zero-based chronological state index, with sparse ticks also showing actual d in mm; loading and unloading at equal d remain separate. No interpolated mechanical states.",
            "The residual tolerance comes from saved settings. Global force balance is a separate dimensionless diagnostic; no new acceptance gate is inferred.",
            "Constraint residual magnitude and its saved bound are in mm, on a separate panel.",
            "Rejected Armijo/backtracking trials are internal bounded solver work, not an external retry.",
            "Production convergence alone does not grant independent-reference, contact-pressure, or effective-clamping qualification.",
        ],
        new_mechanics_calls=dict(model_build=0, force=0, tangent=0,
                                 independent_HP=0, equilibrium_solve=0),
    )
    checkpoint("convergence_read_completed")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    checkpoint("convergence_plot_started")
    figure, axes = plt.subplots(1, 3, figsize=(16.5, 5.6))
    for group_index, group in enumerate(groups):
        indices = group["raw_history_indices_zero_based"]
        axes[0].plot([index + 1 for index in indices],
                     [history[index]["relative_residual"] for index in indices],
                     marker="o", markersize=3, linewidth=1.2, color="#176480",
                     label="Grouped base checks" if group_index == 0 else None)
    axes[0].axhline(tolerance, color="#a43d34", linestyle="--", linewidth=1,
                   label=f"Saved tolerance {tolerance:g}")
    axes[0].set(title="All recorded Newton base checks", xlabel="Chronological check ordinal",
                ylabel="Relative residual (dimensionless)")
    axes[0].legend(fontsize=7, loc="best")

    accepted_indices = list(range(len(states)))
    axes[1].scatter(accepted_indices, [row["relative_residual"] for row in states],
                    marker="o", s=42, color="#176480", label="Accepted residual")
    axes[1].scatter(accepted_indices, [row["relative_global_force_balance"] for row in states],
                    marker="x", s=52, color="#ca7b22", label="Global force balance")
    axes[1].axhline(tolerance, color="#a43d34", linestyle="--", linewidth=1,
                   label="Saved residual tolerance")
    axes[1].set(title="Accepted equilibrium diagnostics", xlabel="Accepted-state index / input d (mm)",
                ylabel="Dimensionless diagnostic")
    axes[1].legend(fontsize=8, loc="best")

    axes[2].scatter(accepted_indices, [abs(row["constraint_residual"]) for row in states],
                    marker="o", s=42, color="#176480", label="Absolute mean-constraint residual")
    axes[2].scatter(accepted_indices, [row["constraint_bound"] for row in states],
                    marker="_", s=180, color="#a43d34", label="Saved constraint bound")
    axes[2].set(title="Accepted mean-displacement constraint", xlabel="Accepted-state index / input d (mm)",
                ylabel="Residual magnitude / bound (mm)")
    axes[2].legend(fontsize=8, loc="best")
    tick_indices = list(range(0, len(states), max(1, (len(states) + 4) // 6)))
    if states and tick_indices[-1] != len(states) - 1:
        tick_indices.append(len(states) - 1)
    tick_labels = [f"{index}\n{states[index]['d']:g}" for index in tick_indices]
    for axis in axes[1:]:
        axis.set_xticks(tick_indices, tick_labels)
    for axis in axes[:2]:
        axis.set_yscale("symlog", linthresh=scales["relative_residual_symlog_linear_threshold"])
    axes[2].set_yscale("symlog", linthresh=scales["constraint_mm_symlog_linear_threshold"])
    for axis in axes:
        axis.grid(True, which="both", alpha=.23)
        axis.set_ylim(bottom=0)
    total = diagnostics["timing_seconds"]["total"]
    figure.suptitle(title, fontsize=15)
    figure.text(.02, .055,
                f"{len(states)} accepted states; {len(history)} Newton checks; "
                f"{len(trials)} line-search trials ({counts['line_search_rejected']} rejected); "
                f"{counts['failed_attempts']} failed attempts; max bisection depth "
                f"{counts['maximum_bisection_depth']}; controller {total:.1f} s.", fontsize=9)
    figure.text(.02, .018,
                "Symlog preserves exact zero; accepted-panel ticks show state index then actual input d (mm). "
                "Saved scalar observations only; no new HP or mechanical qualification.", fontsize=9)
    figure.tight_layout(rect=(0, .11, 1, .94))
    png = output / "convergence.png"
    figure.savefig(png, dpi=160)
    plt.close(figure)
    checkpoint("convergence_plot_completed")
    json_path = output / "convergence.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")
    checkpoint("convergence_written")
    return dict(label=label, json_file=str(json_path), png_file=str(png), counts=counts,
                source_result_sha256=report["source"]["sha256"],
                source_status=result["status"], mechanics_re_evaluated=False)
