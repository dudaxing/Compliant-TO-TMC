"""Evidence persistence tests use a mocked solve, not a new FE path."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse

SCRIPTS = Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0, str(SCRIPTS))
import run_contact_c2 as runner


def protocol(tmp_path, case="padding_2p5"):
    gate=tmp_path/"gate.json"
    gate.write_text('{"status":"pass"}')
    h,padding,policy=runner.CASES[case]
    spec=dict(schema="contact_c2_uniform_diagnostic_v1", cases={case:dict(h_mm=h,padding_mm=padding,
         outer_bottom_policy=policy)}, saved_field_admission=dict(path="gate.json",sha256=runner.sha(gate)),solver={})
    path=tmp_path/"protocol.json"
    path.write_text(json.dumps(spec))
    return path


def test_missing_admission_never_starts_or_creates_run(tmp_path, monkeypatch):
    path=protocol(tmp_path)
    (tmp_path/"gate.json").write_text('{"status":"not_pass"}')
    called=[]
    monkeypatch.setattr(runner, "build_problem", lambda *a: called.append(a))
    with pytest.raises(ValueError, match="admission"):
        runner.run(tmp_path/"run", "padding_2p5", path)
    assert not called and not (tmp_path/"run").exists()


def test_baseline_is_preflight_only(tmp_path):
    with pytest.raises(ValueError, match="preflight"):
        runner.run(tmp_path/"run", "baseline_h0125", protocol(tmp_path,"baseline_h0125"))
    assert not (tmp_path/"run").exists()


def test_full_and_each_accepted_record_are_losslessly_retained(tmp_path, monkeypatch):
    path=protocol(tmp_path)
    captured={}
    def assembly(model, state, tangent=True):
        z=np.zeros((model.ne,8))
        return sparse.eye(model.ndof,format="csc"), np.zeros(model.ndof), dict(
            material_residual=z,regularization_residual=z,J=np.ones((model.ne,9)))
    monkeypatch.setattr(runner.split_kernel,"assemble_split",assembly)
    monkeypatch.setattr(runner,"component_actions",lambda m,s,v:dict(
        material_residual=np.zeros(m.ndof),regularization_residual=np.zeros(m.ndof)))
    def solve(model, *args, **kwargs):
        record=dict(d=0.,is_original_target=True,original_target_displacement=0.,bisection_depth=0,
                    relative_residual=0.,u_lift=np.zeros(model.ndof),u_fluctuation=np.zeros(model.ndof))
        kwargs["on_accept"](record)
        result=dict(status="failed_test_fixture",target_reached=False,reached_displacement=0.,
                    accepted_steps=[record],diagnostic="mock trace: not an FE result")
        captured.update(runner.plain(result))
        return result
    monkeypatch.setattr(runner,"solve_split_affine_path",solve)
    out=tmp_path/"run"
    assert runner.run(out,"padding_2p5",path) is False
    stage=out/"stages/uniform_tmc"
    with gzip.open(stage/"controller_full.json.gz","rt") as f:
        assert json.load(f)==captured
    entry=json.loads((stage/"steps/index.json").read_text())["steps"][0]
    with gzip.open(stage/"steps"/entry["record_file"],"rt") as f:
        assert json.load(f)==captured["accepted_steps"][0]
    assert entry["record_sha256"]==runner.sha(stage/"steps"/entry["record_file"])
    assert entry["sha256"]==runner.sha(stage/"steps"/entry["file"])
    completion=json.loads((stage/"completion.json").read_text())
    compact=json.loads((stage/"result.json").read_text())
    assert completion["controller_full_sha256"]==compact["controller_full_sha256"]==runner.sha(stage/"controller_full.json.gz")
    assert completion["status"]=="failed_test_fixture"
    with pytest.raises(FileExistsError):
        runner.run(out,"padding_2p5",path)
