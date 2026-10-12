"""Typed saved-entry errors without opening a parent or calling mechanics."""
import json

import pytest

from hf_eval import native_evaluate, native_mean


@pytest.mark.parametrize("invalid_settings", [{}, object()], ids=["dict", "object"])
def test_saved_invalid_settings_returns_typed_input_error_without_parent_or_mechanics(
        invalid_settings, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid settings must stop before saved defaults or mechanics")

    monkeypatch.setattr(native_evaluate, "saved_resume_defaults", forbidden)
    monkeypatch.setattr(native_evaluate, "solve_native_mean", forbidden)
    monkeypatch.setattr(native_mean, "build_native_project", forbidden)
    parent = tmp_path / "absent_parent" / "result.json"
    output = tmp_path / "child"
    response = native_evaluate.evaluate_native(None, None, output,
        saved_result=parent, selected_state_index=13, settings=invalid_settings)

    assert response["status"] == "error"
    assert response["failure"] == dict(stage="input", code="invalid_settings",
        exception_class="TMCError", reason="settings must be DisplacementSettings")
    assert response["result_file"] is None and response["independent_reference"] is None
    assert response["target_response"] is None and response["last_accepted"] is None
    assert json.loads((output / "response.json").read_text(encoding="utf-8")) == response
    assert [path.name for path in output.iterdir()] == ["response.json"]
    assert not parent.parent.exists()
