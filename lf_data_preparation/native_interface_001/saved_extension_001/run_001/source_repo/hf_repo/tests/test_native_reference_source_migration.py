"""Old positive JSON evidence stays intact when installed source bindings differ."""
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import pytest

from hf_eval import native_response


REPO = Path(os.environ.get("HF_INTERFACE_TEST_REPO", Path(__file__).resolve().parents[2])).resolve()
RESULT = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/result/result.json"
REFERENCE = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference/summary.json"
QUALIFIED = "lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json"
OLD_PINS = {
    RESULT: "b49955f7e56cd714b35283c0834757ebefc947d3ca25a4f505ed44e8947db7b6",
    REFERENCE: "91c3ef2720e80547e13e1c84e9bfb09d132804f16d3ab819509310e2bbd080e7",
    QUALIFIED: "6762f15477b4aacc00167e5526a20189992deac046954c2888fc6b86219a3fab",
}


@pytest.fixture(autouse=True)
def ordinary_saved_records_only(monkeypatch):
    original_open = Path.open

    def no_npz(path, *args, **kwargs):
        assert path.suffix.lower() != ".npz", "Source migration must not read archived arrays"
        return original_open(path, *args, **kwargs)

    def no_array_decode(*args, **kwargs):
        pytest.fail("Source migration attempted an array decode")

    monkeypatch.setattr(Path, "open", no_npz)
    monkeypatch.setattr(np, "load", no_array_decode)


def test_old_positive_reference_becomes_source_mismatch_after_installation():
    before = {name: (REPO / name).read_bytes() for name in OLD_PINS}
    assert {name: sha256(raw).hexdigest() for name, raw in before.items()} == OLD_PINS
    result = json.loads(before[RESULT])
    reference = json.loads(before[REFERENCE])
    previous_response = json.loads(before[QUALIFIED])
    assert result["status"] == "success" and reference["status"] == "pass"
    assert previous_response["independent_reference"]["accepted_reference_pass"] is True
    assert previous_response["independent_reference"]["full_path_reference_pass"] is True
    assert sha256(Path(native_response.__file__).read_bytes()).hexdigest() == sha256(
        (REPO / "hf_repo/src/hf_eval/native_response.py").read_bytes()).hexdigest()
    for name in ("hf_repo/src/hf_eval/native_mean.py", "hf_repo/src/hf_eval/split_displacement.py"):
        assert sha256((REPO / name).read_bytes()).hexdigest() != reference["source_bindings"][name]

    response = native_response.summarize_saved_native_result(
        RESULT, repo_root=REPO, reference_file=REFERENCE)
    assert response["status"] == "success" and response["path"]["completed"] is True
    assert response["identity"]["result"]["sha256"] == OLD_PINS[RESULT]
    assert response["path"]["accepted_states"] == result["accepted_states"] == 24
    current = response["independent_reference"]
    assert current["status"] == "mismatch" and current["source_bindings_verified"] is False
    assert current["reasons"] == ["Declared reference source bindings were not verified"]
    assert current["accepted_reference_pass"] is current["full_path_reference_pass"] is False
    assert current["reported_status"] == "pass"
    assert current["HP_calls_completed"] == reference["HP_calls_completed"] == 48
    assert not any(current[key] for key in (
        "HP_all_columns_qualified", "contact_qualified", "clamp_qualified", "pressure_qualified", "HF5_qualified"))
    assert before == {name: (REPO / name).read_bytes() for name in OLD_PINS}
