"""Storage-only regression tests; no experiment data or FE evaluation."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from summarize_contact_c2_r2 import verify_output_manifest, write_output_manifest


def test_manifest_excludes_itself_and_rejects_self_entry(tmp_path):
    (tmp_path / "summary.json").write_text('{"status":"partial"}\n', encoding="utf-8")
    entries = write_output_manifest(tmp_path)
    assert set(entries) == {"summary.json"}
    verify_output_manifest(tmp_path)
    entries["output_sha256.json"] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    (tmp_path / "output_sha256.json").write_text(json.dumps(entries), encoding="utf-8")
    with pytest.raises(ValueError, match="must not contain itself"):
        verify_output_manifest(tmp_path)


def test_changed_output_is_rejected_without_overwriting_manifest(tmp_path):
    output = tmp_path / "summary.json"
    output.write_text('{"value":1}\n', encoding="utf-8")
    write_output_manifest(tmp_path)
    manifest = tmp_path / "output_sha256.json"
    frozen = manifest.read_bytes()
    output.write_text('{"value":2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="output hash mismatch"):
        verify_output_manifest(tmp_path)
    with pytest.raises(FileExistsError):
        write_output_manifest(tmp_path)
    assert manifest.read_bytes() == frozen
