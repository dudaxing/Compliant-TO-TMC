"""Synthetic in-memory/readback contracts only; no experiment or FE data made."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from summarize_contact_c2 import Reader,compare_runs,digest,load_run,prefix_mask,pwl_value,state_observables

D=Decimal
HATS=[dict(name="left_hat",x_mm=[-.5,-.25,0],values=[0,1,0]),
      dict(name="right_hat",x_mm=[2,2.25,2.5],values=[0,1,0])]


def primitives():
    model=dict(coordinates=np.array([[-.5,0],[-.25,0],[-.5,1.25],[-.25,1.25]],dtype=float),top_nodes=np.array([2,3]),
               direction=np.array([0.,1.,0.,0.,0.,0.,0.,0.]),fixed_dofs=np.array([1,5,7]))
    total=["0"]*8;material=total.copy();reg=total.copy()
    total[5],total[7]="-.2",".1"
    material[5],material[7]="-.25",".08"
    reg[5],reg[7]=".05",".02"
    total[1],material[1],reg[1]=".7",".6",".1"
    row=dict(state_id="uniform_tmc:0",index=0,parameter_s=0.,status="pass",
        precision_evidence_decimal={"80":dict(internal_decimal=total,material_internal_decimal=material,
             regularization_internal_decimal=reg,physical_displacement_decimal=["0"]*8)},
        measurements=dict(component_precision=dict(total_force=dict(absolute_error=".01",cross_precision_absolute_error=".001")),
                          physical_drive=dict(body="0",whole_bottom="-.1"),hp80_relative_residual="1e-12"),
        force_components=dict(normal_top=dict(total=".1"),parameter_generalized_force=dict(total=".7",material=".6",regularization=".1")))
    return model,row


def test_hat_has_fixed_spatial_support_and_exact_nested_values():
    assert [pwl_value(D(x),HATS[0]) for x in ("-.75","-.5","-.375","-.25","-.125","0",".25")]==list(map(D,("0","0",".5","1",".5","0","0")))
    assert pwl_value(D("2.25"),HATS[1])==1


def test_signed_hp_observables_and_measured_error_envelope():
    model,row=primitives();value=state_observables(row,model,HATS)
    assert value["normal_top_N"]["total"]==D(".1")
    assert value["negative_sum_N"]==D("-.1") and value["negative_node_count"]==1
    assert value["functionals"]["left_hat"]["values_N"]["total"]==D("-.1")
    assert value["functionals"]["left_hat"]["numerical_error_envelope_N"]==D(".011")
    assert value["functionals"]["right_hat"]["values_N"]["total"]==0
    assert value["body_bottom_mean_mm"]==0 and value["whole_bottom_mean_mm"]==D("-.1")
    assert value["parameter_generalized_force_N"]==dict(total=D(".7"),material=D(".6"),regularization=D(".1"))
    assert all(v==0 for v in value["parameter_generalized_force_dot_check_N"].values())


def test_bad_force_sum_and_missing_error_primitive_are_rejected():
    model,row=primitives();bad=deepcopy(row);bad["force_components"]["normal_top"]["total"]=".2"
    with pytest.raises(ValueError): state_observables(bad,model,HATS)
    del row["measurements"]["component_precision"]["total_force"]["cross_precision_absolute_error"]
    with pytest.raises(KeyError): state_observables(row,model,HATS)


def test_prefix_is_absorbing_even_if_later_audit_claims_comparable():
    rows=[dict(state_id=str(i),status=status) for i,status in enumerate(("pass","not_pass","pass"))]
    prefix=[dict(state_id=str(i),comparable=True) for i in range(3)]
    assert prefix_mask(rows,prefix)==[True,False,False]
    assert prefix_mask(rows,[prefix[0],prefix[2]])==[True,False,False]


def test_comparison_sums_two_norm_scaled_envelopes_and_never_interpolates():
    model,row=primitives();value=state_observables(row,model,HATS)
    left=dict(case_id="L",targets=[dict(d_mm=D(0),comparable=True,measurement=deepcopy(value)),dict(d_mm=D(".5"),comparable=False,measurement=None)])
    right=dict(case_id="R",targets=[dict(d_mm=D(0),comparable=True,measurement=deepcopy(value)),dict(d_mm=D(".5"),comparable=True,measurement=deepcopy(value))])
    left["targets"][0]["measurement"]["functionals"]["left_hat"]["values_N"]["total"]+=D(".03")
    result=compare_runs(left,right)
    hat=result[0]["functionals"]["left_hat"]
    assert hat["left_minus_right_N"]==D(".03") and hat["numerical_difference_envelope_N"]==D(".022")
    assert hat["distinguishable_at_recorded_numerical_envelope"] is True
    assert result[1]["comparable"] is False and result[1]["functionals"] is None


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding="utf-8")


def readback_fixture(root):
    model,first=primitives();run=root/"run";stage=run/"stages/uniform_tmc"
    source=root/"hf_repo/source.py";source.parent.mkdir();source.write_text("# synthetic fixture")
    spec=dict(h_mm=.125,padding_mm=2.,outer_bottom_policy="free")
    protocol=dict(uniform_targets_mm=[0.,.5],virtual_test_functions=HATS)
    protocol_path=root/"protocol.json";put(protocol_path,protocol)
    put(run/"metadata.json",dict(kind="TMC",mode="uniform",h=.125,case_id="outer_free",case=spec,protocol=protocol,
                                protocol_sha256=digest(protocol_path),source_sha256={"source.py":digest(source)}))
    put(run/"result.json",dict(status="failed"))
    put(run/"stages/index.json",dict(stages=[dict(phase_id="uniform_tmc",directory="stages/uniform_tmc")]))
    (stage/"steps").mkdir(parents=True)
    np.savez(stage/"model.npz",**model)
    entries=[]
    for i,d in enumerate((0.,.5)):
        p=stage/"steps"/f"state_{i:03d}.npz";np.savez(p,u_lift=np.zeros(8),u_fluctuation=np.zeros(8))
        entries.append(dict(index=i,d=d,is_original_target=True,file=p.name,sha256=digest(p)))
    put(stage/"steps/index.json",dict(steps=entries))
    second=dict(state_id="uniform_tmc:1",index=1,parameter_s=.5,status="not_pass")
    compact=[];detail_bindings={}
    for row in (first,second):
        name=f"audit_states/state_{row['index']:03d}.json";p=run/name;put(p,row)
        detail_bindings[name]=digest(p)
        compact.append({**{k:row[k] for k in ("state_id","index","parameter_s","status")},"detail_file":name,"detail_sha256":digest(p)})
    paths=[run/"metadata.json",run/"stages/index.json",stage/"model.npz",stage/"steps/index.json"]+[stage/"steps"/e["file"] for e in entries]
    audit=dict(schema_version="contact-c2-independent-audit-1.0",status="not_pass",measurement_precision=80,verification_precision_pair=[80,120],
               states=compact,detail_output_sha256=detail_bindings,input_and_helper_sha256={p.relative_to(run).as_posix():digest(p) for p in paths},
               prefix=dict(states=[dict(state_id="uniform_tmc:0",comparable=True),dict(state_id="uniform_tmc:1",comparable=False)]))
    put(run/"audit.json",audit)
    return run,spec,protocol,protocol_path


def test_compact_detail_failed_path_keeps_only_valid_prefix(tmp_path):
    run,spec,protocol,path=readback_fixture(tmp_path)
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert value["failed"] and not value["admitted"] and value["source_and_detail_chain_valid"]
    assert value["valid_prefix_state_count"]==1
    assert value["targets"][0]["measurement"] is not None and value["targets"][1]["measurement"] is None


def test_tampered_detail_invalidates_chain_without_fallback(tmp_path):
    run,spec,protocol,path=readback_fixture(tmp_path)
    (run/"audit_states/state_000.json").write_text("{}")
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert value["source_and_detail_chain_valid"] is False
    assert all(t["measurement"] is None for t in value["targets"])


def test_unexecuted_case_stays_planned_and_null(tmp_path):
    value=load_run(Reader(tmp_path),tmp_path/"missing","mesh_h00625",dict(h_mm=.0625),
                   dict(uniform_targets_mm=[0,.5]),tmp_path/"protocol.json")
    assert value["planned"] and not value["executed"] and not value["failed"]
    assert all(t["measurement"] is None and t["reason"]=="not_executed" for t in value["targets"])


def test_generalized_force_sign_and_free_direction_are_verified():
    model,row=primitives();bad=deepcopy(row)
    bad["force_components"]["parameter_generalized_force"]["total"]="-.7"
    with pytest.raises(ValueError,match="generalized force"): state_observables(bad,model,HATS)
    model["direction"][0]=1
    with pytest.raises(ValueError,match="free DOFs"): state_observables(row,model,HATS)


def fully_passed_fixture(root):
    run,spec,protocol,path=readback_fixture(root)
    audit=json.loads((run/"audit.json").read_text())
    _,second=primitives();second.update(state_id="uniform_tmc:1",index=1,parameter_s=.5)
    name="audit_states/state_001.json";put(run/name,second)
    audit["states"][1].update(status="pass",detail_sha256=digest(run/name))
    audit["detail_output_sha256"][name]=digest(run/name)
    audit["prefix"]["states"][1]["comparable"]=True
    audit["status"]="pass";put(run/"audit.json",audit)
    put(run/"result.json",dict(status="success"))
    for action in ("solve","audit"):
        log=run.parent/f"{run.name}.{action}.log";log.write_text("synthetic successful process")
        receipt=dict(schema="contact_c2_external_receipt_v1",action=action,case_id="outer_free",run_name=run.name,
            returncode=0,timed_out=False,protocol_sha256=digest(path),log_sha256=digest(log))
        if action=="audit": receipt["audit_sha256"]=digest(run/"audit.json")
        put(run.parent/f"{run.name}.{action}.receipt.json",receipt)
    return run,spec,protocol,path


def test_written_pass_requires_bound_successful_process_receipts(tmp_path):
    run,spec,protocol,path=fully_passed_fixture(tmp_path)
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert value["admitted"] and value["external_execution"]["status"]=="pass"


@pytest.mark.parametrize("damage",["exit","timeout","protocol_hash","log_hash","audit_hash"])
def test_bad_external_receipt_denies_admission_but_keeps_valid_hp_prefix(tmp_path,damage):
    run,spec,protocol,path=fully_passed_fixture(tmp_path)
    receipt_path=run.parent/f"{run.name}.audit.receipt.json"
    receipt=json.loads(receipt_path.read_text())
    key,value={"exit":("returncode",1),"timeout":("timed_out",True),"protocol_hash":("protocol_sha256","0"*64),
               "log_hash":("log_sha256","0"*64),"audit_hash":("audit_sha256","0"*64)}[damage]
    receipt[key]=value;put(receipt_path,receipt)
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert value["failed"] and not value["admitted"] and value["external_execution"]["status"]=="failed"
    assert value["source_and_detail_chain_valid"] and value["valid_prefix_state_count"]==2
    assert all(t["measurement"] is not None for t in value["targets"])


def test_missing_receipt_is_pending_and_cannot_admit(tmp_path):
    run,spec,protocol,path=fully_passed_fixture(tmp_path)
    # Missing is unknown, distinct from an observed unsuccessful exit.
    (run.parent/f"{run.name}.audit.receipt.json").unlink()
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert not value["admitted"] and not value["failed"]
    assert value["status"]=="executed_pending_receipts" and value["valid_prefix_state_count"]==2


def test_production_failure_cannot_be_admitted_by_written_audit_pass(tmp_path):
    run,spec,protocol,path=fully_passed_fixture(tmp_path)
    put(run/"result.json",dict(status="failed"))
    value=load_run(Reader(tmp_path),run,"outer_free",spec,protocol,path)
    assert value["failed"] and not value["admitted"] and value["valid_prefix_state_count"]==2
