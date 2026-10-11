"""Interpret already saved ordinary outputs; no numerical observer is run."""
import csv
import hashlib
import json
from pathlib import Path

REPO = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
STAGE = REPO/"lf_data_preparation/native_interface_001/nested_material_volume_001"
OUT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def table(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))

volume = read(STAGE/"run_001/material_volume.json")
receipt = read(STAGE/"run_001/execution_receipt.json")
launch = read(STAGE/"volume_launch.json")
cell_csv = table(STAGE/"run_001/cell_comparisons.csv")
depth_csv = table(STAGE/"run_001/depths.csv")
sample_csv = table(STAGE/"run_001/samples.csv")
old_cells = table(REPO/"lf_data_preparation/native_interface_001/nested_material_support_001/run_001/cells.csv")

sources = {}
for relative in ("run_001/material_volume.json", "run_001/cell_comparisons.csv", "run_001/depths.csv", "run_001/samples.csv",
        "run_001/execution_receipt.json", "volume_launch.json", "protocol.json", "M-VOLUME1_CARD.md",
        "run_001/nine_point_material_P.png", "run_001/material_depth_volume_comparison.png"):
    path = STAGE/relative
    data = path.read_bytes()
    sources[relative] = dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
for name, pin in receipt["output_SHA256"].items():
    assert sources["run_001/"+name]["sha256"] == pin

cases = []
for state in volume["states"]:
    index = state["identity"]["index"]
    for cell in state["cells"]:
        cell_id = cell["cell_id"]
        row = next(row for row in cell_csv if int(row["index"]) == index and int(row["cell_id"]) == cell_id)
        old = next(row for row in old_cells if int(row["index"]) == index and int(row["cell_id"]) == cell_id)
        for prefix, key in (("saved_weak_material", "saved_weak_material_on_body_N"),
                ("saved_top_material_line", "saved_top_material_line_on_body_N"),
                ("rounded_P_direct_volume", "rounded_P_direct_volume_on_body_N"),
                ("regrouped_same_q_terms", "regrouped_same_q_terms_on_body_N"),
                ("geometric_three_depth_volume", "geometric_three_depth_volume_on_body_N"),
                ("geometric_depth_gap", "geometric_depth_gap_on_body_N")):
            assert [float(row[prefix+"_F"+axis+"_N"]) for axis in "xy"] == cell[key]
        assert [float(old["body_material_F"+axis+"_N"]) for axis in "xy"] == cell["saved_weak_material_on_body_N"]
        for name, values in cell["descriptive_differences_N"].items():
            assert [float(row[name+"_F"+axis+"_N"]) for axis in "xy"] == values
        for depth in cell["depths"]:
            entry = next(row for row in depth_csv if int(row["index"]) == index and int(row["cell_id"]) == cell_id and float(row["eta"]) == depth["eta"])
            assert json.loads(entry["point_indices"]) == depth["point_indices"]
            for prefix,key in (("C_eta", "C_eta_on_body_N"), ("regrouped_same_q_terms", "regrouped_same_q_terms_on_body_N"),
                    ("geometric_depth_contribution", "geometric_depth_contribution_on_body_N")):
                assert [float(entry[prefix+"_F"+axis+"_N"]) for axis in "xy"] == depth[key]
        for sample in cell["samples"]:
            entry = next(row for row in sample_csv if int(row["index"]) == index and int(row["cell_id"]) == cell_id and int(row["point_index"]) == sample["point_index"])
            assert [float(entry["P_xy_MPa"]),float(entry["P_yy_MPa"])] == sample["P_normal_column_MPa"]
            assert [float(entry["x_mm"]),float(entry["y_mm"])] == sample["coordinates_mm"]
            assert [float(entry["rounded_P_volume_contribution_F"+axis+"_N"]) for axis in "xy"] == sample["rounded_P_volume_contribution_on_body_N"]
        cases.append(dict(identity=state["identity"],cell_id=cell_id,node_ids=cell["node_ids"],
            selected_body_node_ids=cell["selected_body_node_ids"],
            original_local_internal_material_force_N=cell["original_local_internal_material_force_N"],
            saved_weak_material_on_body_N=cell["saved_weak_material_on_body_N"],
            rounded_P_direct_volume_on_body_N=cell["rounded_P_direct_volume_on_body_N"],
            saved_top_material_line_on_body_N=cell["saved_top_material_line_on_body_N"],
            geometric_three_depth_volume_on_body_N=cell["geometric_three_depth_volume_on_body_N"],
            geometric_depth_gap_on_body_N=cell["geometric_depth_gap_on_body_N"],
            same_q_term_regrouping=cell["same_q_term_regrouping"],
            descriptive_differences_N=cell["descriptive_differences_N"],
            depth_observations=cell["depths"],sample_observations=cell["samples"],
            largest_saved_Q_layer_in_both_signed_component_magnitudes="eta=0, middle" if index == 6 else "eta=-1, bottom",
            exact_ordinary_CSV_JSON_old_support_association=True))

report = dict(
    schema_version="saved-material-volume-actual-physical-interpretation-1.0",
    status="completed_actual_saved_result_interpretation_no_new_scientific_gate",
    source_main_at_execution="7ea78ce19ba066dfce8a03892395d5604707dda6",
    reviewer_role="independent_volume_math_review",
    source_directory=str(STAGE),actual_sources=sources,
    actual_execution=dict(helper_status=receipt["status"],calls=receipt["calls"],counts=receipt["counts"],
        outer_status=launch["status"],invocations=launch["invocations"],exit_code=launch["exit_code"],stop_reason=launch["stop_reason"],
        bindings_unchanged=receipt["all_bindings_unchanged"],helper_seconds=receipt["elapsed_seconds"],
        helper_sampled_RSS_bytes=receipt["sampled_peak_RSS_bytes"],outer_seconds=launch["elapsed_seconds"],
        outer_sampled_tree_RSS_bytes=launch["peak_sampled_tree_RSS_bytes"],
        scientific_gate_meaning="Execution PASS covers the card's identities, counts, exact original associations and same-q-term regrouping; no new material kernel or pressure gate."),
    observed_cases=cases,
    findings=[
        dict(id="original_weak_vs_exported_P_volume",conclusion="The four saved Fy W-minus-V differences are all exactly0. Saved Fx differences are0 except state6/cell10406 -1.6940658945086007e-21N and state13/cell10407 +2.710505431213761e-20N.",
            implication="The observed large local W-versus-top-T differences do not arise from a large separately rounded-P contraction mismatch in these four cases. There is no new evidence to reopen the DD force kernel or replay the full original compensated response. This is an actual comparison, not a new correctly-rounded or HP qualification."),
        dict(id="what_Q_and_T_measure",conclusion="The three Q rows partition the same nine rounded-P volume terms. T is the already saved full top-edge reference Simpson amount; Q_top has the top layer's volume weight and is not T. C_top is the separately constructed geometric row amount whose descriptive difference from T is saved.",
            implication="Do not equate top Q with the old line or add V/W/T comparison bars. The real-arithmetic three-layer identity explains why the selected-node body load can differ from the top edge functional."),
        dict(id="state6_middle_layer",conclusion="For state6 both selected cells have their largest Q contribution in the middle layer. Cell10406 saved Fy Qbottom/Qmiddle/Qtop are0.00010421267325071169 /0.00035952161658755604 /7.873865687086649e-05N; cell10407 values are0.0002935810147878305 /0.0008606118250645263 /0.00016960260973354426N.",
            implication="All three saved Fy Q contributions are positive and all Fx Q contributions are negative. The middle Simpson-weighted layer dominates this state even though bottom-row C_Fy is larger than middle-row C_Fy; C and Q must be distinguished."),
        dict(id="state13_bottom_layer",conclusion="At peak state13 the largest Q layer switches to the bottom. Cell10406 saved Fy Qbottom/Qmiddle/Qtop are0.031043132462937814 /0.005357051117790915 /0.0008195914253922073N; cell10407 values are0.05636985514290049 /0.020623848742840855 /0.003230651429018177N.",
            implication="The top three samples do not carry the same sampling information as the full nine-point volume. This is direct saved-row evidence, not a continuous stress derivative, side-flux or jump-integral diagnosis."),
        dict(id="four_case_saved_local_gaps",conclusion="Saved W-minus-T Fy differences are state6/cell10406 +7.004100548393542e-05N, state6/cell10407 +0.00030617979118463556N, state13/cell10406 +0.03230222645376769N and state13/cell10407 +0.060840446740650464N. The corresponding Fx differences are negative in all four cases.",
            implication="Geometric D reproduces the local sampling-functional gap with the separately stored descriptive residuals. Peak Fy D-minus-(V-minus-T) is -6.938893903907228e-18N in each cell. No new inter-cell sum, percentage, ratio or all-body/all24-state conclusion is computed here."),
        dict(id="owner_specific_sample_evidence",conclusion="At the same peak-state reference point(79.5,30.5)mm, cell10406 q6 stores P_yy=-0.10789581898447494MPa while cell10407 q0 stores P_yy=-0.0015374396545330166MPa. Peak cell10407 q6 at(80,30.5) stores P_yy=-0.1880183184803604MPa, whereas its top q8 at(80,31) stores -0.0039494633933005825MPa.",
            implication="Saved samples belong to their original cell owners. Averaging or smoothing them would alter evidence. These point observations alone do not quantify the role of stress jumps, equilibrium defects, near-contact compression, DivP or solver error."),
        dict(id="actual_discrete_arithmetic",conclusion="All four saved same-q-term regrouping records report passed=true. Saved Fy regrouping errors are0 in all four cases; the only nonzero Fx regrouping error is state6/cell10406 -1.6940658945086007e-21N with saved bound1.3678888063449353e-20N. The other components retain their original saved per-case bounds in observed_cases.",
            implication="No arithmetic is rerun and no stricter or looser scientific gate is introduced. This proves neither original DD contraction replay nor continuous line-volume equality."),
        dict(id="functional_status",conclusion="The new observer now displays and preserves the local nine-point material-force depth contribution, original weak load and prior owner trace side by side. The force and trace are separate observed functionals; the prior original equilibrium/HP qualification is unchanged.",
            implication="The requested local discrepancy investigation has a useful discrete explanation for these four cases. Pressure, total Hu-inclusive boundary action, effective gripping capacity and full HF5 batch labels remain incomplete.")
    ],
    visual_observation=dict(
        source="Root explicitly provided actual original-resolution view_image observations; this reviewer did not independently load pixels.",
        original_dimensions="Two PNGs, each2100x2400",
        root_observations=["Eight panels per PNG, signed independent scales and numeric annotations; eta bottom=-1/top=+1 order correct.",
            "Peak-state Pyy bottom-right sample is strongly negative while its owner top three values are smaller in magnitude.",
            "V/W bars show the same displayed height; state6 Qmiddle and state13 Qbottom dominate.",
            "These are reference sampling figures, not deformed structures; colors across panels cannot be directly compared.",
            "A dominant point makes smaller same-panel values appear gray; labels/CSV preserve them. Original pixels frozen with no rerender."],
        limits="The numeric data and source meanings were independently reviewed; pixel findings are attributed to root. No pressure qualification is inferred from the colors."),
    nearest_coarse_route=dict(
        decision="Close this local saved-P/weak/trace discrepancy investigation without reopening DD, expanding to24 states or adding another full-path ledger.",
        next_function="Prepare the physical contract for public workpiece total generalized load/holding reaction, including material plus Hu, declared virtual motion, half-model and full mirrored-assembly reporting and signed force conventions. Prefer the existing original total nodal reaction as the work-conjugate force baseline rather than forcing a material-P top trace integral to equal it.",
        Hu_dependency="Original source regularization is a Hu/hessian virtual-work contraction. TR/TL selected basis chi has zero second derivative on a face-owner rectangle, while a single corner basis has a mixed second derivative. This is a SOURCE-STATIC mathematical dependency, not a numerical Hu result: M-VOLUME1 did not read Hu or regularization arrays and cannot report their actual face/corner totals.",
        pressure_dependency="A local pressure density or Hu-inclusive boundary traction requires a definition compatible with the original Q1 discrete weak action and higher-derivative/corner contributions, plus a minimal validation plan. Do not add a scalar Hu value to P@N or divide the current W by the top area and claim pressure qualification.",
        assembly_reporting="In a symmetric full assembly, opposite vertical half reactions cancel in net resultant. Per-half signed reaction, full net force and a two-sided normal-magnitude indicator must be explicitly distinguished; none automatically means effective grip or frictional holding capacity.",
        scope="This is a capability/dependency route only, not a new resource window, execution card or authorization."),
    activities=dict(ordinary_JSON_CSV_source_reads=True,raw_file_SHA=True,exact_ordinary_saved_value_association=True,
        NPZ_decodes=0,API_calls=0,new_integrals=0,new_fsum_calls=0,new_ratios=0,new_cross_cell_aggregations=0,
        new_png_writes=0,independent_pixel_loads=0,implementation_edits=0,repository_mutations=0),
    no_new_scientific_gate=True
)
(OUT/"physical_results_review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status=report["status"],report_sha256=hashlib.sha256((OUT/"physical_results_review.json").read_bytes()).hexdigest(),bytes=(OUT/"physical_results_review.json").stat().st_size),ensure_ascii=False))
