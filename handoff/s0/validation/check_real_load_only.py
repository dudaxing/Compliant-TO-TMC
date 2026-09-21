"""Exercise frozen C2 readback loader with numerical evaluation blocked."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--tree",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    tree=args.tree.resolve()
    repo=tree/"hf_repo"
    sys.path[:0]=[str(repo/"scripts"),str(repo/"src")]
    sys.dont_write_bytecode=True
    readback=importlib.import_module("audit_contact_c2_readback")
    frozen=importlib.import_module("audit_contact_c2")
    c1=importlib.import_module("audit_contact_c1")
    hp=importlib.import_module("hf4_split_precision_reference")
    assert not any(name=="jax" or name.startswith("hf_eval") for name in sys.modules)
    module_paths={module.__name__:str(Path(module.__file__).resolve()) for module in (readback,frozen,c1,hp)}
    assert all(Path(path).is_relative_to(repo) for path in module_paths.values())
    protocol_path=repo/"configs/contact_c2_v3.json"
    protocol=json.loads(protocol_path.read_text(encoding="utf-8"))
    gate=(protocol_path.parent/protocol["saved_field_admission"]["path"]).resolve()
    admission=json.loads(gate.read_text(encoding="utf-8"))["input_sha256_from_workspace_root"]
    implementation=protocol["implementation_sha256"]
    assert len(implementation)==33 and len(admission)==166
    forbidden=[]
    records=[]
    with ExitStack() as stack:
        def block(module,name):
            if hasattr(module,name):
                mock=stack.enter_context(patch.object(module,name,side_effect=AssertionError("Numerical evaluation or dispatch is forbidden in load-only validation")))
                forbidden.append((getattr(module,"__name__",str(module))+"."+name,mock))
        for module in (readback,frozen,c1):
            for name in ("audit","audit_state","evaluate_split_prescribed_state"):
                block(module,name)
        block(hp,"evaluate_split_prescribed_state")
        block(hp.DecimalSplitQ1Reference,"__init__")
        block(hp.DecimalSplitQ1Reference,"evaluate")
        for name in ("Popen","run","call","check_call","check_output"):
            block(subprocess,name)
        for case in ("padding_2p5","outer_free","mesh_h00625"):
            run=tree/"hf4_c2_diagnostics/experiments"/case
            bindings={}
            data=readback.load_run(run,protocol_path,bindings)
            portable={Path(path).relative_to(tree).as_posix():value for path,value in bindings.items()}
            verified_impl={name:portable["hf_repo/"+name] for name in implementation}
            assert verified_impl==implementation
            verified_public={name:portable[name] for name in admission if name not in readback.EXTERNAL_HISTORICAL_SOURCES}
            assert len(verified_public)==164 and all(value==admission[name] for name,value in verified_public.items())
            assert all(name not in portable for name in readback.EXTERNAL_HISTORICAL_SOURCES)
            assert all(record["status"]=="not_reverified_external_source" and record["actual_sha256"] is None for record in data["historical_sources"])
            c1_dependencies={name:value for name,value in verified_public.items() if name.startswith("hf4_c1_results/") and name.split("/")[1].startswith(("A0_","Aalpha_","TMC_"))}
            assert len(c1_dependencies)==88
            c1_bytes=sum((tree/name).stat().st_size for name in c1_dependencies)
            assert c1_bytes==145160247
            assert len(data["entries"])==len(data["paths"])==len(data["full"]["accepted_steps"])
            expected=21 if case=="mesh_h00625" else 19
            assert len(data["paths"])==expected
            records.append(dict(case_id=case,completed=data["completed"],stored_run_status=data["top_result"]["status"],
                loader_inventory=data["inventory"],accepted_npz_count=len(data["paths"]),
                implementation_verified_count=len(verified_impl),public_admission_verified_count=len(verified_public),
                c1_dependency_file_count=len(c1_dependencies),c1_dependency_bytes=c1_bytes,
                missing_external_sources=data["historical_sources"],binding_count=len(bindings),input_sha256=portable))
        assert all(mock.call_count==0 for _,mock in forbidden)
        blockers=[dict(name=name,call_count=mock.call_count) for name,mock in forbidden]
    assert not any(name=="jax" or name.startswith("hf_eval") for name in sys.modules)
    output=dict(schema="hf4-c2-s0-real-loader-only-1.0",status="pass",tree=str(tree),argv=sys.argv,
        executable=sys.executable,module_paths=module_paths,script_sha256=sha(Path(__file__)),
        readback_sha256=sha(Path(readback.__file__)),protocol_sha256=sha(protocol_path),
        no_new_fe_path=True,no_constitutive_evaluation=True,forbidden_entry_points=blockers,cases=records,
        scope="Actual readback.load_run source/model/controller/NPZ inventory loading only. Completed production inventory is distinct from independent numerical admission; the mesh final-state failure is unchanged and not assessed here.")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(output,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    print(json.dumps(dict(status="pass",cases=[{key:r[key] for key in ("case_id","accepted_npz_count","binding_count","implementation_verified_count","public_admission_verified_count","c1_dependency_file_count")} for r in records],forbidden_calls=0)))

if __name__=="__main__":
    main()
