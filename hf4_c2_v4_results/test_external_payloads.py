"""Tests for external_payloads.py on a synthetic run (no real payloads needed).

Run: python -m pytest hf4_c2_v4_results/test_external_payloads.py -q
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import external_payloads as ep  # noqa: E402


def make_run(root, name="run_x"):
    run = root / "results/experiments" / name
    (run / "stages/s1/steps").mkdir(parents=True)
    (run / "audit_states").mkdir()

    def put(relative, data):
        (run / relative).write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    controller = put("stages/s1/controller_full.json.gz", gzip.compress(b'{"accepted_steps": []}', mtime=0))
    steps = []
    for i in range(2):
        npz = put(f"stages/s1/steps/state_{i:03d}.npz", bytes([i]) * 100)
        record = put(f"stages/s1/steps/state_{i:03d}.record.json.gz", bytes([i + 10]) * 50)
        steps.append(dict(index=i, file=f"state_{i:03d}.npz", sha256=npz, record_file=f"state_{i:03d}.record.json.gz", record_sha256=record))
    (run / "stages/s1/steps/index.json").write_text(json.dumps(dict(steps=steps)), encoding="utf-8")
    (run / "stages/s1/result.json").write_text(json.dumps(dict(controller_full_sha256=controller)), encoding="utf-8")
    (run / "stages/index.json").write_text(json.dumps(dict(stages=[dict(directory="stages/s1")])), encoding="utf-8")
    states = [dict(detail_file=f"audit_states/state_{i:03d}.json",
                   detail_sha256=put(f"audit_states/state_{i:03d}.json", json.dumps(dict(i=i)).encode())) for i in range(2)]
    (run / "audit.json").write_text(json.dumps(dict(states=states)), encoding="utf-8")
    (run / "metadata.json").write_text("{}", encoding="utf-8")
    for action in ("solve", "audit"):
        (run.parent / f"{name}.{action}.receipt.json").write_text(
            json.dumps(dict(protocol_sha256="p" * 64, audit_sha256="a" * 64)), encoding="utf-8")
    return run


@pytest.fixture
def built(tmp_path):
    repo = tmp_path / "repo"
    run = make_run(repo)
    archive = tmp_path / "outside/evidence-v1/payloads.zip"
    manifest = repo / "results/experiments/run_x.external_payloads.json"
    record = ep.build(run, archive, manifest, root=repo)
    return dict(repo=repo, run=run, archive=archive, manifest=manifest, record=record, tmp=tmp_path)


def test_build_splits_bound_payloads_from_git_records(built):
    record = built["record"]
    assert record["member_count"] == 7
    assert {m["path"].rsplit("/", 1)[-1] for m in record["members"]} == {
        "controller_full.json.gz", "state_000.npz", "state_001.npz", "state_000.record.json.gz",
        "state_001.record.json.gz", "state_000.json", "state_001.json"}
    assert {k["path"].split("run_x/", 1)[1] for k in record["kept_in_git"]} == {
        "audit.json", "metadata.json", "stages/index.json", "stages/s1/result.json", "stages/s1/steps/index.json"}
    assert (built["archive"].parent / "manifest.json").read_bytes() == built["manifest"].read_bytes()
    with zipfile.ZipFile(built["archive"]) as bundle:
        assert bundle.namelist() == [m["path"] for m in record["members"]]


def test_round_trip_into_an_empty_directory_matches_the_originals(built):
    outcome = ep.restore(built["manifest"], built["archive"], built["tmp"] / "restore", empty_target=True, compare_with=built["repo"])
    assert outcome == dict(target_was_empty=True, members=7, restored=7, already_present=0, member_mismatches=[],
                           byte_mismatches_against_originals=[])


def test_restore_into_the_repository_is_idempotent(built):
    outcome = ep.restore(built["manifest"], built["archive"], built["repo"])
    assert (outcome["restored"], outcome["already_present"], outcome["member_mismatches"]) == (0, 7, [])


def test_empty_target_is_enforced(built):
    with pytest.raises(ep.PayloadError, match="empty"):
        ep.restore(built["manifest"], built["archive"], built["repo"], empty_target=True)


def test_build_refuses_a_payload_that_differs_from_its_binding(tmp_path):
    repo = tmp_path / "repo"
    run = make_run(repo)
    (run / "stages/s1/steps/state_001.npz").write_bytes(b"changed")
    with pytest.raises(ep.PayloadError, match="state_001.npz does not match"):
        ep.build(run, tmp_path / "outside/a.zip", repo / "m.json", root=repo)


def test_build_refuses_large_unbound_files_archives_inside_the_repository_and_existing_outputs(tmp_path):
    repo = tmp_path / "repo"
    run = make_run(repo)
    with pytest.raises(ep.PayloadError, match="outside the repository"):
        ep.build(run, repo / "a.zip", repo / "m.json", root=repo)
    (run / "big.bin").write_bytes(b"\0" * (ep.KEEP_IN_GIT_LIMIT + 1))
    with pytest.raises(ep.PayloadError, match="would go into Git"):
        ep.build(run, tmp_path / "outside/a.zip", repo / "m.json", root=repo)
    (run / "big.bin").unlink()
    (repo / "m.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ep.PayloadError, match="write-once"):
        ep.build(run, tmp_path / "outside/a.zip", repo / "m.json", root=repo)


def test_restore_refuses_a_tampered_archive(built):
    data = bytearray(built["archive"].read_bytes())
    data[len(data) // 2] ^= 0xFF
    built["archive"].write_bytes(bytes(data))
    with pytest.raises(ep.PayloadError, match="does not match the manifest"):
        ep.restore(built["manifest"], built["archive"], built["tmp"] / "restore", empty_target=True)


def test_restore_refuses_to_overwrite_a_different_file(built):
    target = built["tmp"] / "restore"
    first = built["record"]["members"][0]["path"]
    (target / first).parent.mkdir(parents=True)
    (target / first).write_bytes(b"other bytes")
    with pytest.raises(ep.PayloadError, match="refusing to overwrite"):
        ep.restore(built["manifest"], built["archive"], target)


def rewrite(built, entries, members):
    archive = built["tmp"] / "crafted.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in entries:
            bundle.writestr(name, data)
    manifest = json.loads(built["manifest"].read_text(encoding="utf-8"))
    manifest.update(archive_bytes=archive.stat().st_size, archive_sha256=ep.sha256_file(archive), members=members)
    path = built["tmp"] / "crafted.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, archive


def test_restore_refuses_extra_entries_and_unsafe_paths(built):
    members = built["record"]["members"]
    entries = [(m["path"], (built["repo"] / m["path"]).read_bytes()) for m in members]
    manifest, archive = rewrite(built, entries + [("extra.bin", b"x")], members)
    with pytest.raises(ep.PayloadError, match="entries differ"):
        ep.restore(manifest, archive, built["tmp"] / "restore")
    evil = dict(path="../evil.bin", bytes=1, sha256=hashlib.sha256(b"x").hexdigest(), bound_by="audit.json")
    manifest, archive = rewrite(built, [("../evil.bin", b"x")], [evil])
    with pytest.raises(ep.PayloadError, match="unsafe member path"):
        ep.restore(manifest, archive, built["tmp"] / "restore")
    assert not (built["tmp"] / "evil.bin").exists()


def test_command_line_refusal_returns_two(built, capsys):
    code = ep.main(["restore", "--manifest", str(built["manifest"]), "--archive", str(built["archive"]),
                    "--into", str(built["repo"]), "--empty-target"])
    assert code == 2
    assert "refused" in capsys.readouterr().err
