"""Source/AST/diff receipt only: never import the candidate or read NPZ fields."""
import ast
from difflib import unified_diff
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
names = sorted(p.relative_to(HERE/"candidate").as_posix() for p in (HERE/"candidate").rglob("*.py"))
files,baseline,diff = {},{},[]
for name in names:
    current = (HERE/"candidate"/name).read_bytes()
    tree = ast.parse(current,filename=name)
    files[name] = dict(sha256=sha256(current).hexdigest(),bytes=len(current),AST="parsed_without_import",
                      functions=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(tree)))
    old = HERE/"baseline"/name
    previous = old.read_bytes() if old.exists() else b""
    if old.exists():
        assert previous == (ROOT/name).read_bytes()
        baseline[name] = sha256(previous).hexdigest()
    diff.extend(unified_diff(previous.decode("utf-8").splitlines(True),current.decode("utf-8").splitlines(True),
                             fromfile="baseline/"+name,tofile="candidate/"+name))
nodeids = ["tests/test_saved_native_resume.py::"+name for name in (
    "test_absolute_anchor_fresh_tangent_and_linear_suffix",
    "test_non_equilibrated_anchor_stops_before_correction_or_commit",
    "test_unaccepted_descending_attempt_rolls_back_revalidated_anchor",
    "test_nonzero_parameter_requires_finite_matching_ordered_saved_anchor",
    "test_public_saved_partial_resume_inherits_options_and_preserves_parent")]
test_tree = ast.parse((HERE/"candidate/hf_repo/tests/test_saved_native_resume.py").read_bytes())
assert {n.name for n in test_tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")} == {n.split("::")[1] for n in nodeids}
(HERE/"candidate_source.diff").write_text("".join(diff),encoding="utf-8")
receipt = dict(status="prepared_source_AST_only_not_imported_or_executed",card="M-RESUME1",
    authorized=False,executed=False,
    base_commit=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),
    candidate_files=files,baseline_files_SHA256=baseline,focused_test_nodeids=nodeids,
    notes_sha256=sha256((HERE/"source_author_notes.md").read_bytes()).hexdigest(),
    diff_sha256=sha256((HERE/"candidate_source.diff").read_bytes()).hexdigest(),
    actual_actions=dict(HF_import=0,candidate_import=0,tests=0,NPZ_decode=0,force=0,tangent=0,
                        solver=0,observer=0,HP=0,JIT=0,render=0,formal_repository_mutation=0),
    future_saved_input=dict(NPZ_files=2,NPZ_fields=6,ordinary_JSON_files=4),
    state_transport="absolute original suffix; original split/signed R; fresh validate-only anchor/K=None",
    qualification=dict(functional_validation_completed=False,independent_HP=False,contact=False,
                       pressure=False,gripping=False,physical_stability=False,HF5=False))
(HERE/"candidate_author_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status=receipt["status"],base_commit=receipt["base_commit"],files=files,
    receipt_sha256=sha256((HERE/"candidate_author_receipt.json").read_bytes()).hexdigest()),indent=2))
