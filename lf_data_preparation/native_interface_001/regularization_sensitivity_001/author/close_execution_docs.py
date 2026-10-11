"""Close ordinary documents only after genuine terminal review; no mechanics."""
import argparse
from hashlib import sha256
from pathlib import Path
from deliver_execution import BASE, REL, PROTOCOL_SHA, FRONTS, TOOLS, ROOT_DEFAULT, read, sha, git, write_new, terminal_metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=ROOT_DEFAULT)
    parser.add_argument("--input",type=Path,default=Path(__file__).resolve().parent/"execution_closure_input.json")
    args = parser.parse_args()
    root, external = args.repo.resolve(), args.input.resolve().parent
    stage = root/REL
    data = read(args.input)
    assert data["source_commit"] == BASE and git(root,"rev-parse","HEAD").decode().strip() == BASE
    assert not (stage/"author/execution_documentation_receipt.json").exists()
    assert set(data["reports"]) == {"terminal","physical","visual","tools"}
    sources = dict(data["reports"], **data["drafts"], front_body=data["front_body"])
    raw = {}
    for key,entry in sources.items():
        path = (external/entry["file"]).resolve()
        path.relative_to(external)
        assert sha(path) == entry["sha256"], key
        raw[key] = path.read_bytes()
    protocol, terminal = terminal_metadata(root,external/data["reports"]["terminal"]["file"])
    assert data["execution_status"] == terminal["execution_status"]
    for key in ("physical","visual"):
        status = read(external/data["reports"][key]["file"])["status"]
        assert status.startswith(("pass","completed","not_available")), (key,status)
    tool_review = read(external/data["reports"]["tools"]["file"])
    assert tool_review["status"].startswith("pass")
    assert set(TOOLS) <= tool_review["reviewed_external_SHA256"].keys()
    for name,pin in tool_review["reviewed_external_SHA256"].items():
        assert sha(external/name) == pin
    assert set(data["drafts"]) == {"RESULTS.md","NEXT_STEP_REVIEW.md"}
    pending = {stage/name:raw[name] for name in data["drafts"]}
    archives = {"terminal":"execution_terminal_review.json","physical":"execution_physical_review.json",
                "visual":"execution_visual_review.json","tools":"execution_tool_static_review.json"}
    for key,name in archives.items():
        pending[stage/"author"/name] = raw[key]
    for name in (*TOOLS,"record_authorization.py","review_terminal_alpha.py","terminal_review_contract.json",
                 "terminal_tool_static_review.json","EXECUTION_DELIVERY_PLAN.md","EXECUTION_DELIVERY_INTERFACE.md",
                 "delivery_tools_author_receipt.json"):
        pending[stage/"author"/name] = (external/name).read_bytes()
    pending[stage/"author/execution_closure_input.json"] = args.input.read_bytes()
    assert all(not path.exists() for path in pending)
    body = raw["front_body"].decode("utf-8")
    assert body.strip() and "\ufffd" not in body
    heading = "M-ALPHA1实际执行已闭卡：" + ("通过" if terminal["execution_status"] == "pass" else "未通过")
    histories, fronts = [], {}
    for name in sorted(FRONTS):
        path = root/name
        prior = git(root,"show",BASE+":"+name)
        assert path.read_bytes() == prior
        url = "../"+REL+"/" if name.startswith("docs/") else ""
        prefix = ("# 当前接续："+heading+"\n\n"+body+"\n\n"+
            "[实际结果]("+url+"RESULTS.md) · [最近取舍]("+url+"NEXT_STEP_REVIEW.md) · "+
            "[终态审阅]("+url+"author/execution_terminal_review.json)\n\n"+
            "<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n").encode("utf-8")
        current = prefix+prior+b"\n</details>\n"
        assert current.count(prior) == 1
        fronts[path] = current
        histories.append(dict(path=name,old_bytes=len(prior),old_sha256=sha256(prior).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(prior),
            new_sha256=sha256(current).hexdigest(),old_body_preserved_exactly=True))
    assert all(value and b"\xef\xbf\xbd" not in value for value in pending.values())
    for path,value in pending.items():
        with path.open("xb") as stream:
            stream.write(value)
    for path,value in fronts.items():
        path.write_bytes(value)
    receipt = dict(status="pass_actual_execution_documentation_closed",source_commit=BASE,protocol_sha256=PROTOCOL_SHA,
        execution_status=terminal["execution_status"],authorized=True,executed=True,execution_closed=True,
        result_sha256=sha(stage/"RESULTS.md"),next_step_sha256=sha(stage/"NEXT_STEP_REVIEW.md"),front_history=histories,
        archived_source_and_review_SHA256={path.relative_to(root).as_posix():sha(path) for path in pending},
        actions=dict(new_candidate_runs=0,new_NPZ_decodes=0,new_force_tangent_HP_solves=0,new_scientific_sums_or_renders=0),
        qualification=dict(new_stability=False,new_pressure=False,new_effective_clamp=False,new_HP=False,whole_HF5=False))
    write_new(stage/"author/execution_documentation_receipt.json",receipt)
    print(dict(status=receipt["status"],execution_status=receipt["execution_status"],fronts_updated=3))


if __name__ == "__main__":
    main()
