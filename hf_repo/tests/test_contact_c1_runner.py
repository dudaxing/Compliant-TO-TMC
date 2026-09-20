"""Manufactured evidence contracts; these tests do not run finite elements.

The synthetic audit is a schema fixture, never a mechanical admission result.
It permits independent corruption of each stored provenance link.
"""
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_contact_c1 as runner


TARGETS = {
    "uniform_precontact": [0., .125, .21875, .25],
    "uniform_closed": [0., .03125, .125, .25],
    "uniform_tmc": [0., .125, .21875, .25, .28125, .375, .5],
}
SOURCE_FILES = ["src/hf_eval/contact_c1.py", "src/hf_eval/split_affine.py",
                "src/hf_eval/split_kernel.py", "scripts/run_contact_c1.py",
                "scripts/hf4_common.py"]


def save(path, value):
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def edit(path, mutate):
    value = runner.read_json(path)
    mutate(value)
    save(path, value)


def seal(directory, index_name):
    result = runner.read_json(directory / "result.json")
    completion = dict(status=result["status"],
                      metadata_sha256=runner.sha(directory / "metadata.json"),
                      result_sha256=runner.sha(directory / "result.json"),
                      index_sha256=runner.sha(directory / index_name))
    if index_name == "steps/index.json":
        completion["accepted_states"] = len(result["accepted_steps"])
    save(directory / "completion.json", completion)


def audit_fixture(source, repo):
    bindings = {p.relative_to(source).as_posix(): runner.sha(p)
                for p in source.rglob("*") if p.is_file() and p.name != "audit.json"}
    helper = repo / "scripts/audit_contact_c1.py"
    bindings[Path(os.path.relpath(helper, source)).as_posix()] = runner.sha(helper)
    save(source / "audit.json", dict(schema_version="contact-c1-independent-audit-1.0",
         status="pass", run="Z:/unavailable/historical/machine/run",
         input_and_helper_sha256=bindings))


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    actual_repo = runner.REPO
    repo = tmp_path / "repo"
    for name in SOURCE_FILES + ["configs/contact_c1_v1.json", "scripts/audit_contact_c1.py"]:
        destination = repo / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual_repo / name, destination)
    monkeypatch.setattr(runner, "REPO", repo)

    def make(kind="A0", internal=False):
        source = repo / "results" / (kind + ("_internal" if internal else "_uniform"))
        source.mkdir(parents=True)
        phases = ["uniform_tmc"] if kind == "TMC" else ["uniform_precontact", "uniform_closed"]
        metadata = dict(schema="contact_c1_run_v1", kind=kind, mode="uniform", h=.25,
                        protocol_sha256=runner.PROTOCOL_SHA256,
                        protocol=runner.read_json(repo / "configs/contact_c1_v1.json"),
                        source_sha256={name: runner.sha(repo / name) for name in SOURCE_FILES},
                        planned_stages=phases)
        save(source / "metadata.json", metadata)
        for phase in phases[:1] if internal else phases:
            stage = source / "stages" / phase
            (stage / "steps").mkdir(parents=True)
            np.savez(stage / "model.npz", synthetic_only=np.array([1.]))
            np.savez(stage / "initial_state.npz", u_lift=np.zeros(4), u_fluctuation=np.zeros(4))
            save(stage / "metadata.json", dict(phase_id=phase, kind=kind, h=.25,
                 targets=TARGETS[phase], model_sha256=runner.sha(stage / "model.npz"),
                 initial_state_sha256=runner.sha(stage / "initial_state.npz")))
            entries, records = [], []
            for index, d in enumerate(TARGETS[phase]):
                # The small component would be lost by premature recombination.
                state = runner.SplitDisplacement([1.e16, d, 0., -0.], [.125, 0., 1.e-18, -0.])
                name = f"state_{index:03d}.npz"
                np.savez(stage / "steps" / name, u_lift=state.lift, u_fluctuation=state.fluctuation)
                entry = dict(index=index, file=name, d=d, is_original_target=True,
                             original_target_displacement=d, bisection_depth=0,
                             sha256=runner.sha(stage / "steps" / name))
                entries.append(entry)
                records.append(dict(entry, u_lift=state.lift.tolist(),
                                    u_fluctuation=state.fluctuation.tolist(),
                                    state_sha256=runner.state_hash(state)))
            save(stage / "steps/index.json", {"steps": entries})
            save(stage / "result.json", dict(status="success", accepted_steps=records,
                 target_reached=True, reached_displacement=TARGETS[phase][-1],
                 target_metrics={"d": TARGETS[phase][-1]}))
            seal(stage, "steps/index.json")
        if not internal:
            stages = [dict(phase_id=p, directory="stages/" + p, status="success") for p in phases]
            save(source / "stages/index.json", {"stages": stages})
            save(source / "result.json", dict(status="success", stages=stages))
            seal(source, "stages/index.json")
            audit_fixture(source, repo)
        return source

    return repo, make


def inherit(source, kind="A0", current=None):
    return runner.source_state(source, "uniform_tmc" if kind == "TMC" else "uniform_closed",
                               .375 if kind == "TMC" else .125,
                               current or source.parent / "perturbation", kind, expected_h=.25)


@pytest.mark.parametrize("kind", ["A0", "Aalpha", "TMC"])
def test_preload_requires_full_chain_and_preserves_both_arrays(evidence, kind):
    repo, make = evidence
    source = make("TMC" if kind == "TMC" else "A0")
    state, provenance = inherit(source, kind)
    assert state.lift[0] == 1.e16 and state.fluctuation[0] == .125
    assert np.signbit(state.lift[-1]) and np.signbit(state.fluctuation[-1])
    assert provenance["source_state_identity_sha256"] == runner.state_hash(state)
    assert provenance["source_audit_sha256"] == runner.sha(source / "audit.json")
    assert provenance["type"] == ("cross_model_warm_start" if kind == "Aalpha" else "same_model_inheritance")
    assert provenance["source_run"] == "../" + source.name
    assert all(not Path(name).is_absolute() for name in provenance["source_evidence_sha256"])
    assert "completion.json" in provenance["source_evidence_sha256"]


def test_internal_stage_transfer_does_not_require_unfinished_run_completion(evidence):
    _, make = evidence
    source = make(internal=True)
    state, provenance = runner.source_state(source, "uniform_precontact", .25, source, "A0", expected_h=.25)
    assert state.lift[1] == .25
    assert provenance["source_run"] == "."
    assert "source_audit_sha256" not in provenance
    assert not (source / "completion.json").exists()


def test_relative_audit_binding_survives_repository_move_and_foreign_cwd(evidence, tmp_path, monkeypatch):
    repo, make = evidence
    source = make()
    relocated = tmp_path / "another checkout"
    shutil.copytree(repo, relocated)
    monkeypatch.setattr(runner, "REPO", relocated)
    monkeypatch.chdir(tmp_path)
    state, provenance = inherit(relocated / "results" / source.name)
    assert state.fluctuation[0] == .125
    assert provenance["source_audit_sha256"] == runner.sha(source / "audit.json")


@pytest.mark.parametrize("relative", ["metadata.json", "result.json", "stages/index.json",
    "stages/uniform_closed/metadata.json", "stages/uniform_closed/result.json",
    "stages/uniform_closed/steps/index.json", "stages/uniform_closed/model.npz",
    "stages/uniform_closed/initial_state.npz", "stages/uniform_closed/steps/state_002.npz"])
def test_each_source_evidence_link_rejects_changed_bytes(evidence, relative):
    _, make = evidence
    source = make()
    with (source / relative).open("ab") as stream:
        stream.write(b" \n")
    with pytest.raises(ValueError, match="hash mismatch"):
        inherit(source)


@pytest.mark.parametrize("directory", [".", "stages/uniform_closed"])
def test_failed_completion_is_not_admitted(evidence, directory):
    _, make = evidence
    source = make()
    edit(source / directory / "completion.json", lambda value: value.update(status="failed"))
    with pytest.raises(ValueError, match="completed successfully"):
        inherit(source)


@pytest.mark.parametrize("mutation", ["missing_inputs", "not_pass", "missing_helper", "missing_state", "stale_binding", "absolute_path"])
def test_audit_status_alone_or_stale_bindings_cannot_admit_preload(evidence, mutation):
    repo, make = evidence
    source = make()
    audit = runner.read_json(source / "audit.json")
    bindings = audit["input_and_helper_sha256"]
    if mutation == "missing_inputs":
        audit.pop("input_and_helper_sha256")
    elif mutation == "not_pass":
        audit["status"] = "not_pass"
    elif mutation == "missing_helper":
        bindings.pop(next(key for key in bindings if key.endswith("audit_contact_c1.py")))
    elif mutation == "missing_state":
        bindings.pop("stages/uniform_closed/steps/state_002.npz")
    elif mutation == "stale_binding":
        bindings["completion.json"] = "0" * 64
    else:
        bindings[str(source / "completion.json")] = runner.sha(source / "completion.json")
    save(source / "audit.json", audit)
    with pytest.raises(ValueError):
        inherit(source)


@pytest.mark.parametrize("mutation,match", [("scalar", "index/result"), ("state_hash", "identity hash"),
    ("split_array", "split arrays"), ("incomplete", "complete frozen stage"),
    ("escape", "basename"), ("unindexed", "complete frozen stage")])
def test_resealing_outer_hashes_does_not_hide_invalid_accepted_inventory(evidence, mutation, match):
    repo, make = evidence
    source = make()
    stage = source / "stages/uniform_closed"
    index = runner.read_json(stage / "steps/index.json")
    result = runner.read_json(stage / "result.json")
    if mutation == "scalar":
        result["accepted_steps"][2]["d"] = .124
    elif mutation == "state_hash":
        result["accepted_steps"][2]["state_sha256"] = "0" * 64
    elif mutation == "split_array":
        result["accepted_steps"][2]["u_fluctuation"][0] = 0.
    elif mutation == "incomplete":
        index["steps"].pop()
        result["accepted_steps"].pop()
        (stage / "steps/state_003.npz").unlink()
    elif mutation == "escape":
        index["steps"][2]["file"] = "../initial_state.npz"
    else:
        shutil.copyfile(stage / "steps/state_000.npz", stage / "steps/unindexed.npz")
    save(stage / "steps/index.json", index)
    save(stage / "result.json", result)
    seal(stage, "steps/index.json")
    audit_fixture(source, repo)
    with pytest.raises(ValueError, match=match):
        inherit(source)


@pytest.mark.parametrize("mutation", ["mesh", "code", "protocol"])
def test_source_identity_must_match_receiving_frozen_model(evidence, mutation):
    repo, make = evidence
    source = make()
    metadata = runner.read_json(source / "metadata.json")
    if mutation == "mesh":
        metadata["h"] = .125
    elif mutation == "code":
        metadata["source_sha256"]["scripts/run_contact_c1.py"] = "0" * 64
    else:
        metadata["protocol_sha256"] = "0" * 64
    save(source / "metadata.json", metadata)
    seal(source, "stages/index.json")
    audit_fixture(source, repo)
    with pytest.raises(ValueError, match="identity"):
        inherit(source)


def test_invalid_preload_is_rejected_before_output_directory_creation(evidence):
    repo, make = evidence
    source = make()
    edit(source / "audit.json", lambda value: value.update(status="not_pass"))
    output = source.parent / "must_not_start"
    with pytest.raises(ValueError, match="audit must pass"):
        runner.run(output, "A0", .25, "perturbation", repo / "configs/contact_c1_v1.json", source)
    assert not output.exists()


def test_runner_refuses_overwriting_existing_evidence(evidence):
    repo, make = evidence
    source = make()
    before = runner.sha(source / "metadata.json")
    with pytest.raises(FileExistsError):
        runner.run(source, "A0", .25, "uniform", repo / "configs/contact_c1_v1.json")
    assert runner.sha(source / "metadata.json") == before
