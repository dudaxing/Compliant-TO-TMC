"""Freeze ordinary M-AVIEW1 result delivery metadata; no scientific work."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
EXTERNAL = Path(__file__).resolve().parent
BASE = "7887aa1138f8e46a2b15f47a1060aa7d72cfe651"
REL = "functional_views/native_alpha_partial_20261011/complete_001"
STAGE = ROOT / REL
AUTHOR = STAGE / "author"
CONFIG = REL + "/author/execution_delivery_config.json"
FINAL = REL + "/author/execution_final_delivery_static_review.json"
FRONTS = {"docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md"}


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(["git", "-c", "gc.auto=0", *args], cwd=ROOT)


def main():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    old_raw = git("show", BASE + ":handoff/repository_manifest.json")
    assert (ROOT / "handoff/repository_manifest.json").read_bytes() == old_raw
    old = {row["path"]: row for row in json.loads(old_raw)["files"]}
    protocol = read(STAGE / "protocol.json")
    documentation = read(AUTHOR / "execution_documentation_receipt.json")
    assert documentation["status"] == "pass_actual_execution_documentation_closed"
    assert documentation["execution_closed"] is True
    assert documentation["source_commit"] == BASE
    assert documentation["result_sha256"] == sha(STAGE / "RESULTS.md")
    assert documentation["next_step_sha256"] == sha(STAGE / "NEXT_STEP_REVIEW.md")
    assert all(sha(ROOT / path) == pin for path, pin in protocol["bindings"].items())

    reports = (
        "execution_delivery_tool_static_review.json",
        "execution_documentation_physics_review.json",
    )
    assert all(read(EXTERNAL / name)["status"].startswith("pass") for name in reports)
    copied = (
        "deliver_execution.py", "DELIVERY_TOOL_SOURCE_NOTES.md",
        "delivery_tool_author_receipt.json", "author_delivery_source.py",
        "configure_execution_delivery.py", *reports,
    )
    for name in copied:
        with (AUTHOR / name).open("xb") as stream:
            stream.write((EXTERNAL / name).read_bytes())

    stage_paths = {path.relative_to(ROOT).as_posix() for path in STAGE.rglob("*") if path.is_file()}
    new = stage_paths - old.keys()
    allowed = sorted(new | FRONTS | {CONFIG, FINAL})
    assert not (set(old) - {path.decode("utf-8") for path in git("ls-files", "-z").split(b"\0") if path})
    for row in documentation["front_history"]:
        prior = git("show", BASE + ":" + row["path"])
        current = (ROOT / row["path"]).read_bytes()
        assert current.count(prior) == 1
        assert current[row["history_start_byte"]:row["history_end_byte_exclusive"]] == prior
        assert sha(ROOT / row["path"]) == row["new_sha256"]

    checked_links = 0
    for name in sorted(new | FRONTS):
        if not name.endswith(".md"):
            continue
        path = ROOT / name
        content = path.read_text(encoding="utf-8")
        if name in FRONTS:
            content = content.split("<details>", 1)[0]
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
            target = target.strip().strip("<>")
            if target.startswith(("http:", "https:", "#", "mailto:", "codex:")):
                continue
            local = target.split("#", 1)[0]
            assert local and (path.parent / local).resolve().exists(), (name, target)
            checked_links += 1

    previous_path = REL + "/author/M_AVIEW1_source_publication_receipt.json"
    config = dict(
        status="frozen_actual_execution_delivery_config",
        source_commit=BASE, execution_status="pass", authorized=True,
        executed=True, execution_closed=True,
        allowed_delta_paths=allowed,
        protocol_sha256=sha(STAGE / "protocol.json"),
        binding_pins=protocol["bindings"],
        front_history=documentation["front_history"],
        final_review_path=FINAL,
        previous_publication_receipt=dict(path=previous_path, sha256=sha(ROOT / previous_path)),
        documentation_receipt_path=REL + "/author/execution_documentation_receipt.json",
        review_pins={**documentation["review_pins"], **{REL + "/author/" + name: sha(AUTHOR / name) for name in reports}},
        local_markdown_links_checked=checked_links,
        metadata_actions_only=True,
        original_M_ALPHA1_status="not_pass", original_unload_completed=False,
        new_HP_pressure_effective_clamp_stability_HF5_qualification=False,
    )
    with (ROOT / CONFIG).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(config, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(status="pass_actual_config_frozen", allowed_delta_files=len(allowed),
        frozen_binding_count=len(protocol["bindings"]), checked_links=checked_links,
        config_sha256=sha(ROOT / CONFIG), only_pending_file=FINAL, new_science_actions=0)))


if __name__ == "__main__":
    main()
