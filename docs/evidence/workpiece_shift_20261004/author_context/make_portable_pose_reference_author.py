from pathlib import Path
from hashlib import sha256
import json,shutil,difflib
base=Path(__file__).resolve().parent
old,new=base/"reference_candidate_v2",base/"reference_candidate_v2_portable"
assert not new.exists();shutil.copytree(old,new)
file=new/"reference_contract_builder.py"
before=file.read_text(encoding="utf-8")
after=before.replace('"--repo",str(root),','"--repo",".",')
assert after!=before and before.count('"--repo",str(root),')==1
compile(after,str(file),"exec");file.write_text(after,encoding="utf-8")
(new/"portable_argv_delta.diff").write_text("".join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile="v2/reference_contract_builder.py",tofile="portable/reference_contract_builder.py")),encoding="utf-8")
note=dict(status="author_static_pass_only",scope="Root static review: only frozen argv repo uses cwd-relative dot, keeping complete Git-root execution and source origin checks.",
    old_builder_sha256=sha256((old/file.name).read_bytes()).hexdigest(),new_builder_sha256=sha256(file.read_bytes()).hexdigest(),
    same_core_audit_counter_math=True,previous_peer_review_scope="peer_review.json binds original v2 builder; inherited audit/counter/core review remains, new one-line argv delta reviewed here.",
    formal_reference_invocations=0,new_F_T_HP_solver_model_calls=0)
(new/"portable_argv_review.json").write_text(json.dumps(note,indent=2)+"\n",encoding="utf-8")
print(json.dumps(note))
