"""Record source whitespace validation and retain raw-archive exceptions."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

root = Path(r"D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
out = root / "docs/evidence/workpiece_enlargement_20261007/right_margin_source_context/closure_001"
product = ["hf_repo/src/hf_eval/analysis_domain.py", "hf_repo/scripts/prepare_analysis_domain.py", "hf_repo/tests/test_analysis_domain.py", "README.md", "hf_repo/README.md", "docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md", "docs/WORKPIECE_ENLARGEMENT_20261007.md"]
full = subprocess.run(["git", "diff", "--cached", "--check"], cwd=root, capture_output=True)
current = subprocess.run(["git", "diff", "--cached", "--check", "--", *product], cwd=root, capture_output=True)
assert current.returncode == 0 and not current.stdout and not current.stderr
findings = []
for line in full.stdout.decode("utf-8").splitlines():
    match = re.match(r"(.+):(\d+): (.+)", line)
    if not match:
        assert line == "+ "
        continue
    name, number, issue = match.groups()
    historical = name.endswith((".diff", ".construction_banner.txt", ".prefix.md")) or name.rsplit("/", 1)[-1] in {"013.md", "014.md", "015.md", "016.md"} and "right_margin_source_context/closure_001/files/" in name
    assert historical, name
    findings.append(dict(path=name, line=int(number), issue=issue, sha256=sha256((root / name).read_bytes()).hexdigest()))
assert full.returncode != 0 and not full.stderr
(out / "git_diff_check.stdout.log").write_bytes(full.stdout)
record = dict(status="pass_current_sources_raw_archives_retained", product_paths=product, product_diff_check_exit=0, all_staged_check_exit=full.returncode, raw_archive_findings=findings, policy="Historical diff context and interim banners retain their original pinned bytes; current source and entry documents pass. No numerical rerun.", validator_correction="An initial check expected exit 1; the direct Git process returns 2 for these archived whitespace findings. Initial validator wrote no files or scientific results.", scientific_calls=0)
(out / "delivery_source_check.json").write_bytes((json.dumps(record, indent=2) + "\n").encode("utf-8"))
(out / "record_delivery_check.py").write_bytes(Path(__file__).read_bytes())
(out / "record_delivery_check_pre_returncode_fix.py").write_bytes(Path(__file__).with_name("record_delivery_check_pre_returncode_fix.py").read_bytes())
print(json.dumps(dict(status=record["status"], raw_archive_findings=len(findings), scientific_calls=0)))
