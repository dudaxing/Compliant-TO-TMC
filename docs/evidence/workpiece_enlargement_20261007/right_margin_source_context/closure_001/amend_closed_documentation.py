"""Close current-reference wording and append the saved-result interpretation."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--author", type=Path, required=True)
    args = parser.parse_args()
    author, repo = args.author, args.repo
    closure = repo / "docs/evidence/workpiece_enlargement_20261007/right_margin_source_context/closure_001"
    review = json.loads((author / "root_interpretation_review.json").read_text(encoding="utf-8"))
    assert review["status"].startswith("pass")
    assert not review["blocking_findings"]
    proposals = json.loads((author / "final_doc_proposals_001/final_summary.json").read_text(encoding="utf-8"))["proposal_sha256"]
    names = ["docs/WORKPIECE_ENLARGEMENT_20261007.md", "docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json"]
    before = {name: digest(repo / name) for name in names}
    assert all(before[name] == proposals[name] for name in names)
    receipt_path = closure / "root_documentation_amendment.json"
    assert closure.is_dir() and not receipt_path.exists()
    interpretation = (author / "root_physical_interpretation.md").read_bytes()
    assert sha256(interpretation).hexdigest() == review["text_sha256"]
    report = repo / names[0]
    progress_path = repo / names[1]
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    old_reference = progress["reference"]
    assert old_reference["status"] == "running_not_qualified"
    actual = progress["final_reference_view_observations"]["cases"]["right2col"]
    assert (actual["accepted_states"], actual["HP_started"], actual["HP_completed"], actual["checks_completed"]) == (24, 48, 48, 476733)
    report.write_bytes(report.read_bytes() + interpretation)
    progress["prior_reference_snapshot"] = old_reference
    progress["reference"] = dict(old_reference, status="pass", HP_started=actual["HP_started"], HP_completed=actual["HP_completed"], checks_completed=actual["checks_completed"], actual_helper_seconds=554.0963570999447, actual_outer_seconds=actual["reference_elapsed_seconds"], scope=progress["qualification"])
    progress["documentation_closure"] = "right_margin_source_context/closure_001/INDEX.md"
    progress_path.write_bytes((json.dumps(progress, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))
    for name in ("root_physical_interpretation.md", "root_interpretation_review.json", "amend_closed_documentation.py"):
        target = closure / name
        source = author / name
        if target.exists():
            assert target.read_bytes() == source.read_bytes()
        else:
            target.write_bytes(source.read_bytes())
    receipt = dict(status="pass_documentation_only", created_utc=datetime.now(timezone.utc).isoformat(), before_sha256=before, after_sha256={name: digest(repo / name) for name in names}, interpretation_sha256=sha256(interpretation).hexdigest(), review_sha256=digest(author / "root_interpretation_review.json"), reason="Current reference status was stale; preserve the historical snapshot and report actual closed evidence. Append physical interpretation without rewriting raw reviewed proposals.", scientific_calls=0)
    receipt_path.write_bytes((json.dumps(receipt, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
