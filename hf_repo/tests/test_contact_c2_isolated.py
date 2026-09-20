"""Regression for a written pass followed by failed/changed audit evidence."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import run_contact_c2_isolated as isolated


def fixture_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(isolated, "__file__", str(tmp_path/"hf_repo/scripts/run_contact_c2_isolated.py"))
    experiments = tmp_path/"experiments"
    run = experiments/"padding_2p5"
    run.mkdir(parents=True)
    protocol = tmp_path/"protocol.json"
    protocol.write_text("{}")
    source = tmp_path/"source.py"
    source.write_text("frozen")
    detail = run/"detail.json"
    detail.write_text("{}")
    audit = dict(status="pass",case_id="padding_2p5",schema_version="contact-c2-independent-audit-1.0",
                 input_and_helper_sha256={"../../source.py":isolated.sha(source)},
                 detail_output_sha256={"detail.json":isolated.sha(detail)})
    (run/"audit.json").write_text(json.dumps(audit))
    receipts = {}
    for action in ("solve", "audit"):
        log = experiments/f"padding_2p5.{action}.log"
        log.write_text("completed")
        value = dict(schema="contact_c2_external_receipt_v1",action=action, case_id="padding_2p5",run_name=run.name,returncode=0,timed_out=False,
                     protocol_sha256=isolated.sha(protocol),log_sha256=isolated.sha(log))
        if action == "audit":
            value["audit_sha256"] = isolated.sha(run/"audit.json")
        (experiments/f"padding_2p5.{action}.receipt.json").write_text(json.dumps(value))
        receipts[action]=value
    return experiments, run, protocol, receipts


def test_successful_unchanged_audit_permits_next_case(tmp_path, monkeypatch):
    experiments, _, protocol, receipts = fixture_tree(tmp_path, monkeypatch)
    isolated.validate_previous([receipts["solve"]], experiments, protocol)


@pytest.mark.parametrize("change", ["timeout", "exit", "missing_receipt", "audit", "detail", "source", "log", "protocol"])
def test_written_pass_cannot_hide_failed_or_changed_evidence(tmp_path, monkeypatch, change):
    experiments, run, protocol, receipts = fixture_tree(tmp_path, monkeypatch)
    receipt_path=experiments/"padding_2p5.audit.receipt.json"
    if change in ("timeout", "exit"):
        receipts["audit"].update({"timed_out": True} if change=="timeout" else {"returncode": 1})
        receipt_path.write_text(json.dumps(receipts["audit"]))
    elif change=="missing_receipt":
        receipt_path.unlink()
    else:
        paths={"audit":run/"audit.json", "detail":run/"detail.json", "source":tmp_path/"source.py",
               "log":experiments/"padding_2p5.audit.log", "protocol":protocol}
        with paths[change].open("a") as stream: stream.write(" ")
    with pytest.raises((ValueError, OSError)):
        isolated.validate_previous([receipts["solve"]], experiments, protocol)
