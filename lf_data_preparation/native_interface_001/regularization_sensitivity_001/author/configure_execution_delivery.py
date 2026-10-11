"""Freeze the genuine terminal delta after closure; no scientific work/staging."""
import argparse
from pathlib import Path
from deliver_execution import BASE, REL, M, PROTOCOL_SHA, CONFIG, FINAL, FRONTS, ROOT_DEFAULT, read, sha, git, write_new, source_metadata, closed_documentation, identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=ROOT_DEFAULT)
    parser.add_argument("--external-base",type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, external = args.repo.resolve(), args.external_base.resolve()
    assert git(root,"rev-parse","HEAD").decode().strip() == BASE
    assert not (root/CONFIG).exists() and not (external/"execution_delivery_config.json").exists() and not (root/FINAL).exists()
    oldraw, old, old_entries = source_metadata(root)
    assert (root/M).read_bytes() == oldraw
    protocol, terminal, doc = closed_documentation(root)
    stage_files = {p.relative_to(root).as_posix() for p in (root/REL).rglob("*") if p.is_file()}
    assert old_entries.keys() & stage_files == {n for n in old_entries if n.startswith(REL+"/")}
    new = stage_files-old_entries.keys()
    existing = new | FRONTS
    records = {name:identity(root,name) for name in sorted(existing)}
    assert all(records[name]["sha256"] == item["sha256"] and records[name]["bytes"] == item["bytes"]
               for name,item in terminal["actual_run_file_inventory"].items())
    reviews = {REL+"/author/"+name:sha(root/REL/"author"/name) for name in (
        "execution_terminal_review.json","execution_physical_review.json","execution_visual_review.json","execution_tool_static_review.json")}
    config = dict(schema_version="M-ALPHA1-execution-delivery-1.0",source_commit=BASE,protocol_sha256=PROTOCOL_SHA,
        binding_count=57,execution_status=terminal["execution_status"],execution_closed=True,
        allowed_delta_paths=sorted(existing | {CONFIG,FINAL}),
        record_pins={name:item["sha256"] for name,item in records.items()},review_pins=reviews,
        final_review_path=FINAL,final_review_scope="This frozen config has no self hash; only the final review itself remains to be created. It is hashed with the actual staged delta.",
        source_publication_receipt=REL+"/author/M_ALPHA1_source_publication_receipt.json",
        inherited_manifest_sha256=sha(root/M),inherited_manifest_entries=18651,inherited_manifest_bytes=9296517834,
        authorized=True,executed=True,whole_HF5_complete=False)
    write_new(external/"execution_delivery_config.json",config)
    with (root/CONFIG).open("xb") as stream:
        stream.write((external/"execution_delivery_config.json").read_bytes())
    print(dict(status="actual_terminal_delta_configured",execution_status=config["execution_status"],delta_files=len(config["allowed_delta_paths"]),config_sha256=sha(root/CONFIG)))


if __name__ == "__main__":
    main()
