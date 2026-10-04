"""Install the once-only pure metadata validation, with actual closed-source inputs."""
from pathlib import Path
from hashlib import sha256
import json,shutil
root=Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
author=Path(__file__).resolve().parent/"reference_candidate_v2"
stage=root/"lf_data_preparation/native_workpiece_001/shift_counter_metadata_001"
assert not stage.exists();stage.mkdir()
for name in ("counter_attempts.py","validate_counter_metadata.py","peer_review.json","v2_author_note.json"):
    file=author/name
    if file.exists():shutil.copyfile(file,stage/name)
shutil.copyfile(Path(__file__).resolve(),stage/Path(__file__).name)
shutil.copyfile(root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/launch_cycle010.py",stage/"launch_metadata.py")
files=[p for p in stage.iterdir() if p.is_file()]
for name in ("coarse_square_cycle_010", "shift_square_pose_001/run_001"):
    folder=root/"lf_data_preparation/native_workpiece_001"/name
    files += [folder/"result/result.json",folder/"execution_receipt.json"]
pins={p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in files}
prefix=stage.relative_to(root).as_posix()
protocol=dict(schema_version="shift-counter-metadata-card-1.0",bindings=pins,sampled_RSS_bytes=8*1024**3,
    phases=dict(validation=dict(helper_seconds=60,outer_seconds=90,
        argv=[prefix+"/validate_counter_metadata.py","--repo",".","--output",prefix+"/result"])),
    scope="Eight pure metadata cases; historical complete trace, failed trace rejection, synthetic known-prefix counter shape and five malformed negatives. Zero mechanical APIs.",
    synthetic_scope="A metadata unit fixture only, never a shortened physical task, new equilibrium, or prefix qualification.",
    static_review="Root read full127-line validator and194-line math-only helper; exact actual ordinals and unsupported paths separated; peer static pass binds helper.",
    stop_policy="Once; first unexpected failure closes, no retry/extension/force; no HP or production calls.")
with (stage/"protocol.json").open("x",encoding="utf-8") as f:json.dump(protocol,f,indent=2);f.write("\n")
print(json.dumps(dict(status="frozen_only",bindings=len(pins))))
