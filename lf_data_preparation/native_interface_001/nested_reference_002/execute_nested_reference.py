"""M-REF2: fresh full-path Decimal reference of the saved h0.5 cycle.

Only loading, provenance, resource accounting and reporting are new.
B850 run_state and aa86 workpiece_checks are inherited without override.
Saved tensors are consumed; no constitutive production force/tangent or solve.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys

parser = argparse.ArgumentParser(description=__doc__)
for name in ("repo", "input", "output", "protocol"):
    parser.add_argument("--"+name, type=Path, required=True)
parser.add_argument("--time-limit", type=float, required=True)
ARGS = parser.parse_args()
ROOT = ARGS.repo.resolve()
PROTOCOL_FILE = ARGS.protocol.resolve()
CONTRACT = json.loads(PROTOCOL_FILE.read_text(encoding="utf-8"))
CORE_PATH = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py"
CORE_PIN = "b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5"
WORKPIECE_PATH = "hf_repo/scripts/audit_native_workpiece_cycle.py"
WORKPIECE_PIN = "aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938"
sha_raw = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if CONTRACT["schema_version"] != "nested-saved-cycle-independent-reference-card-1.1":
    raise ValueError("Wrong M-REF2 protocol")
for name, pin in CONTRACT["reference_sources"].items():
    if sha_raw(ROOT/name) != pin:
        raise ValueError("Reference source changed before import: "+name)
if CONTRACT["reference_sources"].get(CORE_PATH) != CORE_PIN or CONTRACT["reference_sources"].get(WORKPIECE_PATH) != WORKPIECE_PIN:
    raise ValueError("Frozen B850/aa86 reference composition differs")
sys.path[:0] = [str((ROOT/CORE_PATH).parent), str(ROOT/"hf_repo/scripts"), str(ROOT/"hf_repo/src")]
from core_audit_mechanical import Audit as CoreAudit, GATES, RSS_LIMIT, MECHANICAL_AVAILABILITY
from audit_native_workpiece_cycle import WorkpieceCycleAudit, GATES as WORKPIECE_GATES
from audit_native_force import canonical_hash, npz, read, require, sha, verify_descriptor, verify_fields, write
import numpy as np


class NestedCycleAudit(CoreAudit, WorkpieceCycleAudit):
    def __init__(self, args):
        super().__init__(args)
        self.repo = ROOT
        self.workpiece_completed = 0

    def checkpoint(self):
        self.peak = max(self.peak, self.process.memory_info().rss)
        require(perf_counter()-STARTED <= self.limit, "M-REF2 helper time limit exceeded")
        require(self.peak <= RSS_LIMIT, "M-REF2 sampled RSS exceeds 8 GiB")
        require(not (PROTOCOL_FILE.parent/"stop_requested.txt").exists(), "M-REF2 stop requested")

    def lifecycle(self, status, error=None):
        write(self.output/"lifecycle.json", dict(status=status, error=error,
            elapsed_seconds=perf_counter()-STARTED, HP_calls_started=self.hp_started,
            HP_calls_completed=self.hp_completed, checks_completed=self.checks,
            accepted_mechanical_states_completed=len(self.rows), workpiece_states_completed=self.workpiece_completed,
            sampled_peak_RSS_bytes=self.peak, time_limit_seconds=self.limit, sampled_RSS_limit_bytes=RSS_LIMIT,
            stop_policy="First error stops this one window; no repair, retry, extension, production evaluation or force"))

    def load(self):
        contract = CONTRACT
        self.bind(PROTOCOL_FILE)
        self.check(self.limit == contract["phases"]["reference"]["helper_seconds"] == 4500.
            and contract["phases"]["reference"]["outer_seconds"] == 4560.
            and contract["sampled_RSS_bytes"] == RSS_LIMIT
            and self.stage == self.repo/contract["production_stage"]
            and self.output == self.repo/contract["reference_output"]
            and contract["expected_accepted_states"] == 24 and contract["expected_new_HP_calls"] == 48
            and contract["direction"] == dict(definition="actual b_in/max(abs(b_in)), fixed components zero",
                length=27378, multiplier_direction=0., expected_port_weights=[.125,.25,.25,.25,.125])
            and contract["gates"] == GATES == WORKPIECE_GATES, "M-REF2 fixed scope/resource/original gates differ")
        for name, pin in contract["bindings"].items():
            self.bind(self.repo/name, pin)
        sources = self.output/"sources"
        names = [Path(name).name for name in contract["reference_sources"]]
        require(len(names) == len(set(names)), "Reference capsule dependency basenames must be unique")
        for name, pin in contract["reference_sources"].items():
            destination = sources/Path(name).name
            shutil.copyfile(self.repo/name, destination)
            self.bind(destination, pin)
            self.sources[name] = pin
        own = Path(__file__).resolve().relative_to(self.repo).as_posix()
        self.sources[own] = contract["bindings"][own]
        shutil.copyfile(PROTOCOL_FILE, self.output/"protocol.json")
        for name in (CORE_PATH, "hf_repo/scripts/audit_native_mean.py", "hf_repo/scripts/run_split_average_demo.py"):
            syntax = ast.parse((self.repo/name).read_text(encoding="utf-8"))
            declarations = [node.value for node in syntax.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "GATES" for target in node.targets)]
            self.check(len(declarations) == 1 and {item.arg:ast.literal_eval(item.value) for item in declarations[0].keywords} == GATES,
                "Original strict gate declaration differs: "+name)
        receipt = read(self.stage/"execution_receipt.json")
        launch = read(self.repo/contract["production_launch_file"])
        production_protocol = read(self.repo/contract["production_protocol_file"])
        self.check(receipt["schema_version"] == "native-nested-cycle-api-forward-execution-1.0"
            and receipt["status"] == "pass" and receipt["cli_invocations"] == 1
            and receipt["accepted_states"] == receipt["original_target_states"] == 24
            and receipt["additional_bisection_states"] == receipt["HP_calls"] == receipt["JIT_calls"] == 0
            and receipt["all_bindings_unchanged"] is True and receipt["cached_production_gates"]["passed"] is True
            and launch["status"] == "pass" and launch["invocations"] == 1 and launch["exit_code"] == 0
            and launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
            and launch["protocol_sha256"] == receipt["protocol_sha256"] == sha(self.repo/contract["production_protocol_file"]),
            "Original closed production launch/receipt differs")
        self.check(all(contract["bindings"].get(name) == pin for name,pin in production_protocol["bindings"].items()),
            "Original production source/input closure differs")
        self.origin = self.stage/"fixed_square"
        self.result_file = self.origin/"result.json"
        result, response = read(self.result_file), read(self.origin/"response.json")
        verify_descriptor(result)
        targets = contract["targets_mm"]
        self.check(result["schema_version"] == "hf-native-mean-result-1.2" and result["status"] == "success"
            and all(result[key] is True for key in ("production_converged","target_reached","task_target_executed",
                "path_completed","loading_peak_reached","unload_endpoint_reached","lift_origin_zero","lift_shape_zero"))
            and all(result[key] is False for key in ("equilibrium_qualified","independent_HP_qualified","HF_qualified"))
            and result["path_kind"] == "ordered_cycle" and result["targets_mm"] == receipt["requested_targets_mm"] == targets
            and result["task_target_mm"] == 1.2 and result["reached_displacement"] == result["target_origin"] == 0.
            and result["settings"] == contract["production_settings"] and result["backend"] == "numpy"
            and result["initial_guess"] == "port_projection" and result["matrix_units"] == "N/mm"
            and result["force_scale_per_length"] == 20. and result["k_out_N_per_mm"] == 0.
            and result["save_force_calls"] == result["save_tangent_calls"] == 0 and result["failure"] is None
            and result["call_counts"] == receipt["call_counts"]
            and result["tangent_execution"] == dict(mode="chunk256",element_block_size=256,global_selector_scope="full_batch")
            and all(result[key] == value for key,value in MECHANICAL_AVAILABILITY.items()), "Actual complete mechanical producer scope differs")
        self.check(response["identity"]["result"]["sha256"] == sha(self.result_file)
            and all(value is False for value in response["producer_flags"].values())
            and response["independent_reference"]["status"] == response["views"]["status"] == "not_provided",
            "Original response must retain its historical qualification/availability")
        model_file, metadata_file = (self.origin/result["model"][key] for key in ("arrays_path","descriptor_path"))
        model, metadata = npz(model_file), read(metadata_file)
        verify_descriptor(metadata)
        verify_fields(model, metadata["arrays"]["fields"])
        task = read(self.repo/contract["task_file"])
        geometry = read(self.origin/"model/source_geometry/geometry.json")
        verify_descriptor(geometry)
        self.check(len(model) == 27 and metadata["schema_version"] == "hf-native-project-model-1.1"
            and metadata["task"] == task and metadata["task_sha256"] == result["task_sha256"] == canonical_hash(task)
            and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
            and metadata["arrays"]["sha256"] == result["model"]["arrays_sha256"] == sha(model_file)
            and metadata["grid"] == result["grid"] == geometry["grid"] == contract["grid"]
            and metadata["material"] == contract["material"] and task["workpiece"] == contract["workpiece"]
            and task["path"] == dict(kind="ordered_cycle",targets_mm=targets)
            and metadata["region_metadata"]["counts"] == result["counts"] == contract["expected_counts"],
            "Exact fine model/task/material/grid identity differs")
        source = metadata["source_geometry"]
        self.check(source["geometry_id"] == geometry["geometry_id"] == task["geometry"]["geometry_id"]
            and source["descriptor_sha256"] == geometry["descriptor_sha256"] == task["geometry"]["descriptor_sha256"]
            and source["descriptor_file_sha256"] == sha(self.origin/"model/source_geometry/geometry.json")
            and source["arrays_sha256"] == sha(self.origin/"model/source_geometry/geometry.npz")
            and result["source_geometry"] == dict(source,snapshot={key:"model/"+path for key,path in source["snapshot"].items()}),
            "Current HF-derived source geometry identity differs")
        coords, conn = model["coordinates"], model["connectivity"]
        x, y = np.meshgrid(np.arange(169)*.5, np.arange(81)*.5)
        base = (np.arange(80)[:,None]*169+np.arange(168)).ravel()
        expected_conn = np.column_stack((base,base+1,base+170,base+169))
        edofs = (2*conn[:,:,None]+np.arange(2)).reshape(-1,8)
        self.check(np.array_equal(coords,np.column_stack((x.ravel(),y.ravel())))
            and np.array_equal(conn,expected_conn) and np.array_equal(edofs,model["edofs"]), "Full fine Q1 geometry/connectivity/DOF indexing differs")
        solid_nodes = np.unique(conn[model["solid"]])
        centres = coords[conn].mean(axis=1)
        cells = np.flatnonzero((centres[:,0]>=62.) & (centres[:,0]<=80.) & (centres[:,1]>=31.) & (centres[:,1]<=40.))
        nodes = np.unique(conn[cells]); dofs = (2*nodes[:,None]+np.arange(2)).ravel()
        support_nodes = solid_nodes[(coords[solid_nodes,0]==0.) & (coords[solid_nodes,1]<=8.)]
        symmetry_nodes = solid_nodes[(coords[solid_nodes,1]==40.) & (coords[solid_nodes,0]<=60.)]
        top_nodes = np.flatnonzero(coords[:,1]==40.)
        groups = dict(support=(2*support_nodes[:,None]+np.arange(2)).ravel().tolist(),
            entity_symmetry=(2*symmetry_nodes+1).tolist(), background_symmetry=(2*top_nodes+1).tolist())
        overlap = np.intersect1d(dofs,groups["background_symmetry"])
        fixed = np.unique(np.concatenate([dofs]+[np.asarray(value) for value in groups.values()]))
        regions, body = metadata["region_metadata"], metadata["region_metadata"]["workpiece"]
        self.check((len(cells),len(nodes),len(dofs),len(overlap),len(fixed)) == (648,703,1406,37,1548)
            and all(np.array_equal(model[key],value) for key,value in dict(workpiece_cells=cells,workpiece_nodes=nodes,
                workpiece_dofs=dofs,workpiece_background_symmetry_overlap_dofs=overlap,fixed_dofs=fixed,
                free_dofs=np.setdiff1d(np.arange(27378),fixed),solid_nodes=solid_nodes).items())
            and not np.intersect1d(nodes,solid_nodes).size and not np.any(model["solid"][cells])
            and all(regions[name]["dofs"] == value for name,value in groups.items())
            and regions["fixed_dofs"] == fixed.tolist() and body["definition"] == contract["workpiece"]
            and (body["selected_cells"],body["incident_nodes"],body["fixed_dofs"]) == (648,703,1406)
            and all(body[name] == value.tolist() for name,value in dict(cells=cells,nodes=nodes,dofs=dofs,
                background_symmetry_overlap_dofs=overlap).items()), "Fine body overlay and disjoint holding groups differ")
        weights = [.125,.25,.25,.25,.125]
        inlet = np.flatnonzero((coords[:,0]==0.) & (coords[:,1]>=38.))
        outlet = np.flatnonzero((coords[:,0]==80.) & (coords[:,1]>=28.) & (coords[:,1]<=30.))
        self.check(np.flatnonzero(model["b_in"]).tolist() == (2*inlet).tolist()
            and np.flatnonzero(model["b_out"]).tolist() == (2*outlet+1).tolist()
            and model["b_in"][2*inlet].tolist() == model["b_out"][2*outlet+1].tolist() == weights
            and not np.intersect1d(2*inlet,fixed).size, "Actual five-node fine physical ports differ")
        direction = model["b_in"]/max(abs(model["b_in"]))
        direction[fixed] = 0.
        self.check(direction.shape == (27378,) and direction.dtype == np.dtype("float64")
            and np.count_nonzero(direction) == 5 and np.count_nonzero(direction[fixed]) == 0,
            "Actual fixed-compatible PORT direction differs")
        states = result["states"]
        self.check(len(states) == result["accepted_states"] == 24
            and [row["d"] for row in states] == targets
            and [row["original_target_index"] for row in states] == list(range(24))
            and all(row["is_original_target"] is True and row["bisection_depth"] == 0
                and row["original_target_displacement"] == targets[index] and row["target_origin"] == 0.
                and row["physical_mean_target_mm"] == row["d"]
                and row["leg"] == ("origin" if index == 0 else "loading" if index <= 13 else "unloading")
                and row["tangent_execution"] == result["tangent_execution"] for index,row in enumerate(states)),
            "Every actual/original fine-cycle state must be retained in order")
        for row in states:
            for file in [self.origin/row["descriptor_path"]]+[self.origin/row[key]["path"] for key in ("state","forces","tangents","matrix")]:
                name = file.relative_to(self.repo).as_posix()
                self.check(receipt["outputs"][name] == contract["bindings"][name] == self.bindings[file],
                    "Selected accepted-state raw input differs from actual receipt")
        self.model,self.edofs,self.direction = model,edofs,direction
        self.result,self.metadata,self.receipt = result,metadata,receipt
        self.workpiece_dofs,self.groups = dofs,groups
        self.checkpoint()

    def run(self):
        self.checkpoint(); self.load()
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        self.reference_class = DecimalSplitQ1Reference
        for index,row in enumerate(self.result["states"]):
            self.run_state(index,row)
            self.workpiece_checks(index,row)
            self.workpiece_completed += 1
        self.check(self.hp_started == self.hp_completed == 48 and len(self.rows) == self.workpiece_completed == 24,
            "Fresh full24 mechanical/body reference coverage differs")
        for path,pin in self.bindings.items():
            self.check(sha(path) == pin, "Bound source/input changed: "+str(path))
        self.checkpoint()
        summary = dict(schema_version="native-workpiece-cycle-independent-audit-1.0",status="pass",
            alias="fixed_square_nested_h05",case_family="gripper",accepted_states=len(self.rows),states=self.rows,
            audited_targets_mm=CONTRACT["targets_mm"],path_kind="ordered_cycle",workpiece=CONTRACT["workpiece"],
            result_sha256=sha(self.result_file),checks_completed=self.checks,
            HP_calls_started=self.hp_started,HP_calls_completed=self.hp_completed,
            HP_matrix_columns_exhaustively_checked=False,full_element_and_DOF_coverage=True,
            gates=GATES,global_scatter_precision=3000,global_scatter_inexact_trap=True,
            reference_scope="All24 actual accepted/original saved states,13440 elements and27378 real DOFs; actual five-node PORT direction with deltaR=0; signed material/Hu body force and disjoint holding projections",
            qualification="Accepted mechanical states of this exact h0.5 fixed-square cycle only. Original15 strict gates; no all-column, new separate Hu-error gate, stress-HP, pressure, effective-clamp, mesh/domain convergence or HF5 qualification",
            contact_qualified=False,clamp_qualified=False,pressure_qualified=False,HF5_qualified=False,
            **MECHANICAL_AVAILABILITY,analytic_HP_energy_scope="Archived independent reference only; no candidate energy comparison or qualification",
            private_run_state_source_sha256=CORE_PIN,inherited_workpiece_checker_sha256=WORKPIECE_PIN,
            tangent_action_consumer_sha256=CONTRACT["reference_sources"]["hf_repo/src/hf_eval/tangent_action.py"],
            tangent_execution=self.result["tangent_execution"],direction=CONTRACT["direction"],
            direction_array_sha256=hashlib.sha256(self.direction.tobytes()).hexdigest(),
            source_bindings=self.sources,input_bindings={path.relative_to(self.repo).as_posix():pin for path,pin in self.bindings.items()},
            independent_reference_contract_sha256=sha(PROTOCOL_FILE),production_response_unchanged=True,
            candidate_force_calls=0,tangent_calls=0,solver_calls=0,model_constructions=0,JIT_calls=0,LF_calls=0,
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=self.peak,
            time_limit_seconds=self.limit,sampled_RSS_limit_bytes=RSS_LIMIT)
        write(self.output/"summary.json",summary)
        self.checkpoint(); self.lifecycle("pass"); self.checkpoint()
        print(dict(status="pass",accepted_states=len(self.rows),HP_calls=self.hp_completed,checks_completed=self.checks),flush=True)


def main():
    require(ARGS.time_limit == 4500., "M-REF2 requires its explicit pre-frozen4500s helper window")
    audit = NestedCycleAudit(ARGS)
    try:
        audit.run()
    except BaseException as error:
        audit.lifecycle("not_pass",repr(error))
        write(audit.output/"summary.json",dict(status="not_pass",error=repr(error),states=audit.rows,
            accepted_states=len(audit.rows),workpiece_states_completed=audit.workpiece_completed,
            HP_calls_started=audit.hp_started,HP_calls_completed=audit.hp_completed,checks_completed=audit.checks,
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=audit.peak))
        raise


if __name__ == "__main__":
    main()
