"""Synthetic record-binding contracts; no FE, high precision, or evidence restore."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate_contact_c2_stable_f.py"
SPEC = importlib.util.spec_from_file_location("stable_f_record_binding_under_test", SCRIPT)
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture
def c1():
    records = [dict(d=d, is_original_target=True,
                    original_target_displacement=d, bisection_depth=0)
               for d in (0.0, 0.125)]
    entries = [dict(record, index=i, file=f"state_{i}.npz", sha256=digest(f"state {i}"))
               for i, record in enumerate(records)]
    hashes = {name: digest(name) for name in ("result.json", "steps/index.json", "metadata.json")}
    return dict(metadata=dict(schema="contact_c1_stage_v1"), entry=deepcopy(entries[1]),
                completion=dict(status="success", accepted_states=2,
                                result_sha256=hashes["result.json"],
                                index_sha256=hashes["steps/index.json"],
                                metadata_sha256=hashes["metadata.json"]),
                file_sha256=hashes, controller=dict(status="success", accepted_steps=records),
                entries=entries)


@pytest.fixture
def c2():
    return dict(metadata=dict(schema="contact_c2_stage_v1"),
                entry=dict(index=1, file="state_1.npz", sha256=digest("state 1"),
                           record_file="record_1.json.gz", record_sha256=digest("record 1")),
                record_sha256=digest("record 1"))


@pytest.mark.parametrize("schema", ["c1", "c2"])
def test_valid_schema_binding_preserves_inputs(schema, request):
    data = request.getfixturevalue(schema)
    original = deepcopy(data)
    assert validation.validate_saved_record_binding(**data) is None
    assert data == original


@pytest.mark.parametrize("key", ["result_sha256", "index_sha256", "metadata_sha256",
                                 "status", "accepted_states"])
def test_c1_missing_completion_key_rejected(c1, key):
    del c1["completion"][key]
    with pytest.raises(KeyError, match=key):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("filename", ["result.json", "steps/index.json", "metadata.json"])
def test_c1_each_completion_hash_is_required(c1, filename):
    c1["file_sha256"][filename] = digest("changed file")
    with pytest.raises(ValueError, match="completion binding mismatch"):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("mutation", ["completion_count", "accepted_records", "index_entries",
                                      "completion_status", "controller_status"])
def test_c1_inventory_and_success_status_are_required(c1, mutation):
    if mutation == "completion_count":
        c1["completion"]["accepted_states"] += 1
    elif mutation == "accepted_records":
        c1["controller"]["accepted_steps"].pop()
    elif mutation == "index_entries":
        c1["entries"].pop()
    elif mutation == "completion_status":
        c1["completion"]["status"] = "not_pass"
    else:
        c1["controller"]["status"] = "not_pass"
    with pytest.raises(ValueError, match="record inventory mismatch"):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("index", [-1, 2, 1.0, True, "1"])
def test_c1_invalid_selected_index_is_not_python_indexing(c1, index):
    c1["entry"]["index"] = index
    with pytest.raises(ValueError, match="selected record index out of range"):
        validation.validate_saved_record_binding(**c1)


def test_c1_selected_entry_must_be_the_indexed_entry(c1):
    c1["entry"]["file"] = "other_state.npz"
    with pytest.raises(ValueError, match="selected embedded record differs"):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("key,value", [("d", 0.25), ("is_original_target", False),
                                       ("original_target_displacement", 0.25),
                                       ("bisection_depth", 1)])
def test_c1_each_selected_record_field_is_bound(c1, key, value):
    c1["controller"]["accepted_steps"][1][key] = value
    with pytest.raises(ValueError, match="selected embedded record differs"):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("key", ["d", "is_original_target", "original_target_displacement", "bisection_depth"])
def test_c1_missing_embedded_record_field_rejected(c1, key):
    del c1["controller"]["accepted_steps"][1][key]
    with pytest.raises(KeyError, match=key):
        validation.validate_saved_record_binding(**c1)


def test_c2_wrong_record_hash_is_rejected(c2):
    c2["record_sha256"] = digest("changed record")
    with pytest.raises(ValueError, match="C2 per-state record hash mismatch"):
        validation.validate_saved_record_binding(**c2)


def test_c2_missing_expected_record_hash_is_rejected(c2):
    del c2["entry"]["record_sha256"]
    with pytest.raises(KeyError, match="record_sha256"):
        validation.validate_saved_record_binding(**c2)


def test_c2_missing_actual_record_hash_is_rejected(c2):
    del c2["record_sha256"]
    with pytest.raises(ValueError, match="C2 per-state record hash mismatch"):
        validation.validate_saved_record_binding(**c2)


@pytest.mark.parametrize("schema", ["contact_c1_stage_v2", "contact_c2_stage_v2", "", None])
def test_unknown_schema_is_not_treated_as_optional_binding(c1, schema):
    c1["metadata"]["schema"] = schema
    with pytest.raises(ValueError, match="unknown saved stage record schema"):
        validation.validate_saved_record_binding(**c1)


def test_missing_schema_is_rejected(c1):
    c1["metadata"].clear()
    with pytest.raises(KeyError, match="schema"):
        validation.validate_saved_record_binding(**c1)


@pytest.mark.parametrize("schema", ["c1", "c2"])
def test_saved_rejects_bad_binding_before_output_or_numerics(schema, request, monkeypatch):
    data = request.getfixturevalue(schema)
    metadata, entry = data["metadata"], data["entry"]
    metadata["model_sha256"] = digest("model")
    documents = {"stage/metadata.json": metadata}
    hashes = {"stage/model.npz": digest("model"),
              "stage/steps/" + entry["file"]: entry["sha256"]}
    if schema == "c1":
        documents.update({"stage/completion.json": data["completion"],
                          "stage/result.json": data["controller"],
                          "stage/steps/index.json": {"steps": data["entries"]}})
        hashes.update({"stage/" + name: value for name, value in data["file_sha256"].items()})
        data["controller"]["accepted_steps"][1]["d"] = 0.25
    else:
        hashes["stage/steps/" + entry["record_file"]] = digest("changed record")
    evidence = SimpleNamespace(json=documents.__getitem__, path=lambda name: name)
    monkeypatch.setattr(validation, "sha", hashes.__getitem__)
    monkeypatch.setattr(validation, "saved_descriptors",
                        lambda *_: [("synthetic", "stage", entry, {})])

    def forbidden(*args, **kwargs):
        pytest.fail("record binding must fail before output or numerical evaluation")

    for name in ("write", "production_model", "evaluate_production", "legacy_control"):
        monkeypatch.setattr(validation, name, forbidden)
    with pytest.raises(ValueError, match="record"):
        validation.saved(SimpleNamespace(all_c2=False), None, evidence,
                         None, None, None, None, None, None)
