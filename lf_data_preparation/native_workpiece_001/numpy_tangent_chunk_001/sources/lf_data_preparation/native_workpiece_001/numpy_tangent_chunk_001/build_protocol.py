"""Freeze source and exact saved inputs; no mechanics imports or evaluation."""
from hashlib import sha256
import ast
import json
from pathlib import Path
import shutil
import subprocess

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
sha = lambda p: sha256(p.read_bytes()).hexdigest()
protocol_file = STAGE/"protocol.json"
assert not protocol_file.exists()
baseline_file = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/sources/split_numpy_tangent.py"
live_file = ROOT/"hf_repo/src/hf_eval/split_numpy_tangent.py"
old = ast.parse(baseline_file.read_text(encoding="utf-8"))
new = ast.parse(live_file.read_text(encoding="utf-8"))
old_tangent = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == "_tangent")
new_pairs = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == "_tangent_pairs")
new_finish = next(n for n in new.body if isinstance(n, ast.FunctionDef) and n.name == "_finish_tangent")
# Inverse extraction: selector stays at its original position in the restored core.
restored = old_tangent.body[:5] + new_pairs.body[4:-1] + new_finish.body[1:]
assert ast.dump(ast.Module(body=restored, type_ignores=[]), include_attributes=False) == ast.dump(
    ast.Module(body=old_tangent.body, type_ignores=[]), include_attributes=False), "DD core expression/order changed"
fixtures = [
    dict(name="origin007", directory="lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/result/accepted/000"),
    dict(name="peak008", directory="lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/result/accepted/004"),
    dict(name="return007", directory="lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/result/accepted/006")]
names = [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/"hf_repo/src/hf_eval").glob("*.py"))]
names += ["hf_repo/pyproject.toml", "hf_repo/tests/test_split_numpy_tangent.py",
          "hf_repo/tests/test_split_numpy_tangent_chunked.py",
          baseline_file.relative_to(ROOT).as_posix(),
          "lf_data_preparation/native_workpiece_001/models/gripper_coarse_square/model.npz",
          "lf_data_preparation/native_workpiece_001/coarse_square_cycle_007/reference/summary.json",
          "lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/execution_receipt.json",
          "lf_data_preparation/native_workpiece_001/coarse_square_cycle_008/result/result.json"]
names += [f["directory"]+"/"+name for f in fixtures for name in
          ("state.npz", "state.json", "forces.npz", "tangents.npz", "total_matrix.npz")]
names += [(STAGE/n).relative_to(ROOT).as_posix() for n in
          ("README.md", "measure_once.py", "launch_phase.py", "build_protocol.py")]
bindings = {name: sha(ROOT/name) for name in sorted(set(names))}
sources = {}
for name in names:
    if not name.endswith(".py"):
        continue
    source = ROOT/name
    compile(source.read_text(encoding="utf-8"), name, "exec")
    destination = STAGE/"sources"/name
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists()
    shutil.copyfile(source, destination)
    sources[destination.relative_to(ROOT).as_posix()] = sha(destination)
bindings.update(sources)
protocol = dict(schema_version="numpy-tangent-chunk-card-1.0",
    baseline_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    sampled_RSS_bytes=8*1024**3, bindings=bindings, fixtures=fixtures,
    model_file="lf_data_preparation/native_workpiece_001/models/gripper_coarse_square/model.npz",
    baseline_tangent=baseline_file.relative_to(ROOT).as_posix(),
    candidate_tangent=live_file.relative_to(ROOT).as_posix(), block_size=256,
    DD_core_AST_inverse_equal=True, expected_force_calls=3, expected_tangent_calls=9,
    expected_sparse_assemblies=9, cost_decision_archived_over_chunk_minimum=1.25,
    tests_mechanics_call_counts="not instrumented; null; separate from comparison fixture counts",
    qualification="Saved-input byte equivalence and single-pass cost only; no fresh HP or new equilibrium",
    preserved_next_path_mm=[0,.5,1,1.5,1.75,1.5,1,.5,0],
    failure_policy="First error closes current card; no retry/repair/force/extension",
    phases={p: dict(helper_seconds=h, outer_seconds=o,
             argv=[(STAGE/"measure_once.py").relative_to(ROOT).as_posix(),p])
            for p,h,o in (("tests",120,150),("comparison",180,210))})
protocol_file.write_text(json.dumps(protocol, indent=2)+"\n", encoding="utf-8")
print(json.dumps(dict(protocol_sha256=sha(protocol_file), bindings=len(bindings),
                     source_caps=len(sources), DD_core_AST_inverse_equal=True)))
