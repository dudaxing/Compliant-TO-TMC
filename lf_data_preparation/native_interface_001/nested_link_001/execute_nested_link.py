"""M-LINK1 prepared source: attach existing same-identity reference/views to a new response.

Consumes saved metadata, source and image bytes only. No arrays or mechanics.
This prepared source requires separate card execution authorization before launch.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
import hashlib
import json
from pathlib import Path
import sys
import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo",type=Path,required=True)
parser.add_argument("--protocol",type=Path,required=True)
parser.add_argument("--time-limit",type=float,required=True)
args = parser.parse_args()
repo,protocol_file = args.repo.resolve(),args.protocol.resolve()
read = lambda path:json.loads(path.read_text(encoding="utf-8"))
sha = lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
protocol = read(protocol_file)
process,peak = psutil.Process(),0
calls = dict(saved_summary_started=0,saved_summary_completed=0,response_writes=0,index_writes=0)
output = repo/protocol["output_directory"]

def checkpoint():
    global peak
    peak = max(peak,process.memory_info().rss)
    if perf_counter()-STARTED > args.time_limit or peak > protocol["sampled_RSS_bytes"] or (protocol_file.parent/"stop_requested.txt").exists():
        raise RuntimeError("M-LINK1 cooperative resource/stop boundary reached")

def write(path,value):
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def artifact(path):
    return dict(path=path.relative_to(repo).as_posix(),path_scope="repo_relative",sha256=sha(path))

def run():
    if protocol["schema_version"] != "native-saved-linked-delivery-card-1.0" or args.time_limit != 180.:
        raise ValueError("M-LINK1 requires its explicit frozen180s helper card")
    checkpoint()
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Bound source/saved artifact changed: "+name)
    sys.path.insert(0,str(repo/"hf_repo/src"))
    from hf_eval.native_response import summarize_saved_native_result,write_native_response
    calls["saved_summary_started"] += 1
    response = summarize_saved_native_result(protocol["result_file"],repo_root=repo,
        reference_file=protocol["reference_file"],view_manifest=protocol["raw_view_file"])
    calls["saved_summary_completed"] += 1
    if response["independent_reference"]["status"] != "matched" or not response["independent_reference"]["full_path_reference_pass"] or response["views"]["status"] != "matched":
        raise ValueError("Existing saved API did not match complete same-result reference and views")
    checkpoint()
    linked = output/"linked_response.json"
    write_native_response(response,linked)
    calls["response_writes"] += 1
    phase_path = repo/protocol["view_phase_file"]
    phase = read(phase_path)
    if phase["status"] != "pass" or phase["raw_view_manifest_sha256"] != protocol["bindings"][protocol["raw_view_file"]]:
        raise ValueError("Closed view phase does not bind this raw view")
    image_names = [link["path"] for link in response["views"]["links"]]
    fourth = (phase_path.parent/phase["comparison"]["image"]).relative_to(repo).as_posix()
    image_names.append(fourth)
    # The raw view remains unchanged: its fourth PNG belongs to the existing phase.
    for name in image_names:
        local = (repo/name).relative_to(phase_path.parent).as_posix()
        if phase["outputs"].get(local) != protocol["bindings"].get(name):
            raise ValueError("A delivery image does not match the closed phase: "+name)
    index = dict(schema_version="native-saved-linked-delivery-index-1.0",status="pass",
        linked_response=artifact(linked),result=artifact(repo/protocol["result_file"]),
        original_response=artifact(repo/protocol["original_response_file"]),reference=artifact(repo/protocol["reference_file"]),
        raw_view=artifact(repo/protocol["raw_view_file"]),view_phase=artifact(phase_path),
        images=[artifact(repo/name) for name in image_names],
        tables=[artifact(repo/name) for name in protocol["table_files"]],
        accepted_states=response["path"]["accepted_states"],
        reference_status=response["independent_reference"]["status"],views_status=response["views"]["status"],
        source_flags=response["producer_flags"],
        qualification="Same-result saved artifact association only. Existing full24 HP report remains directional, not all-column; images remain saved diagnostics/two-grid sensitivity, not pressure/effective-clamp/mesh-domain-convergence/HF5 qualification",
        fourth_PNG_origin="Original phase comparison.image; the raw view and phase were neither rewritten nor copied",
        path_basis="Repository-relative artifact paths; caller resolves against checkout root after restoration")
    write(output/"delivery_index.json",index)
    calls["index_writes"] += 1
    checkpoint()
    for name,pin in protocol["bindings"].items():
        if sha(repo/name) != pin:
            raise ValueError("Original bound artifact changed: "+name)
    checkpoint()
    return dict(schema_version="M-LINK1-saved-association-execution-1.0",status="pass",calls=calls,
        protocol_sha256=sha(protocol_file),all_bindings_unchanged=True,outputs={path.name:sha(path) for path in (linked,output/"delivery_index.json")},
        elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak,
        mechanical_hooks_monitored=False,zero_new_mechanics_basis="Pinned native_response imports stdlib only and consumes JSON/source/image bytes; no model/array/production/HP/render calls")

def main():
    output.mkdir(parents=True,exist_ok=False)
    try:
        receipt = run()
    except BaseException as error:
        write(output/"execution_receipt.json",dict(status="not_pass",error=repr(error),calls=calls,
            elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak))
        raise
    write(output/"execution_receipt.json",receipt)
    print(json.dumps(dict(status=receipt["status"],calls=calls)),flush=True)

if __name__ == "__main__":
    main()
