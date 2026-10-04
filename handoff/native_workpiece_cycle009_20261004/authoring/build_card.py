"""Install/freeze a unique full nine-target card; no FE, HP or constructor."""
from pathlib import Path
import argparse
from hashlib import sha256
import json
import shutil
import subprocess

ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
AUTHOR = Path(__file__).resolve().parent
STAGE = ROOT/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_009"
PRIOR = STAGE.parent/"coarse_square_cycle_007"
BASELINE = "97b7e0eecd07aee0bd16c61961dedb360202641c"
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding="utf-8"))


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bind(pins, path):
    pins[path.relative_to(ROOT).as_posix()] = sha(path)


def install():
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASELINE
    assert read(AUTHOR/"candidate_physical_review.json")["status"] == "pass"
    assert not STAGE.exists()
    STAGE.mkdir()
    names = ["prepare_cycle009.py", "execute_cycle009.py", "audit_cycle009.py",
             "launch_cycle009.py", "core_audit_mechanical.py", "task.json", "README.md"]
    for name in names:
        shutil.copyfile(AUTHOR/name, STAGE/name)
    (STAGE/"authoring").mkdir()
    for path in sorted(AUTHOR.iterdir()):
        if path.name in names:
            continue
        shutil.copyfile(path, STAGE/"authoring"/path.name)
    old = read(PRIOR/"input_inventory.json")
    pins = dict(old["input_bindings"])
    assert len(pins) == 46 and all(sha(ROOT/n) == v for n,v in pins.items())
    source003 = read(STAGE.parent/"coarse_square_cycle_003"/"source_freeze.json")["sources"]
    source007 = read(PRIOR/"source_freeze.json")["sources"]
    changed = {"hf_repo/src/hf_eval/native_mean.py", "hf_repo/scripts/solve_native_mean.py",
               "hf_repo/src/hf_eval/split_numpy_tangent.py"}
    assert {n for n in source003 if sha(ROOT/n) != source007[n]} == changed
    for name in source003:
        bind(pins, ROOT/name)
    for path in [PRIOR/n for n in ("input_inventory.json", "source_freeze.json",
                                  "execution_receipt.json", "reference/summary.json")]:
        bind(pins, path)
    chunk = STAGE.parent/"numpy_tangent_chunk_001"
    integration = STAGE.parent/"native_mean_chunk_integration_001"
    for path in [chunk/n for n in ("protocol.json","tests_launch.json","tests_receipt.json",
                                  "comparison_launch.json","comparison_receipt.json")] + [
        integration/n for n in ("protocol.json","tests_launch.json","tests_receipt.json")] + [
        STAGE.parent/"coarse_square_cycle_008"/"execution_receipt.json",
        STAGE.parent/"coarse_square_cycle_008"/"result"/"result.json"]:
        bind(pins,path)
    for path in [STAGE/n for n in names]+list((STAGE/"authoring").iterdir()):
        bind(pins,path)
    protocol = dict(schema_version="native-mechanical-cycle-card-1.0", baseline_commit=BASELINE,
        sampled_RSS_bytes=8*1024**3, bindings=pins,
        phases=dict(prepare=dict(argv=[(STAGE/"prepare_cycle009.py").relative_to(ROOT).as_posix()],
                                 outer_seconds=60)),
        scope="Only input/source freeze after bitwise tangent and tiny entry integration; zero FE/solver/HP",
        stop_policy="One actual invocation per phase; first formal failure closes card, no retry/repair/force/extension")
    write(STAGE/"prepare_protocol.json",protocol)
    print(json.dumps(dict(status="installed_not_executed", prepare_pins=len(pins),
                         prepare_protocol_sha256=sha(STAGE/"prepare_protocol.json"))))


def freeze():
    prepare = read(STAGE/"prepare_launch.json")
    assert prepare["status"] == "pass" and prepare["exit_code"] == 0 and prepare["invocations"] == 1
    assert prepare["all_bindings_unchanged"] and prepare["stop_reason"] is None
    old,new = read(PRIOR/"input_inventory.json"),read(STAGE/"input_inventory.json")
    assert new["settings"] == old["settings"] and new["gates"] == old["gates"]
    assert new["execution_limits"] == old["execution_limits"] and len(new["input_bindings"]) == 63
    assert new["case"]["targets_mm"] == [0,.5,1,1.5,1.75,1.5,1,.5,0]
    assert new["case"]["tangent_mode"] == "chunk256"
    sources = read(STAGE/"source_freeze.json")["sources"]
    assert len(sources) == 68
    pins = dict(new["input_bindings"])
    for name,pin in sources.items():
        assert sha(ROOT/name) == pin and sha(STAGE/"sources"/Path(name).name) == pin
        bind(pins,ROOT/name)
        bind(pins,STAGE/"sources"/Path(name).name)
    for name in ("input_inventory.json","source_freeze.json","prepare_protocol.json","prepare_launch.json"):
        bind(pins,STAGE/name)
    for name,pin in read(STAGE/"prepare_protocol.json")["bindings"].items():
        assert sha(ROOT/name) == pin
        pins[name] = pin
    protocol = dict(schema_version="native-mechanical-cycle-card-1.0", baseline_commit=BASELINE,
        sampled_RSS_bytes=8*1024**3, bindings=pins,
        phases=dict(
            production=dict(helper_seconds=600,outer_seconds=660,
                argv=[(STAGE/"execute_cycle009.py").relative_to(ROOT).as_posix()]),
            reference=dict(helper_seconds=240,outer_seconds=300,
                argv=[(STAGE/"audit_cycle009.py").relative_to(ROOT).as_posix(),
                      "--input",STAGE.relative_to(ROOT).as_posix(),"--output",
                      (STAGE/"reference").relative_to(ROOT).as_posix(),"--time-limit","240"])),
        prerequisite="Whole productionpass then fresh HP80/120 for every actual accepted index; no failed partial replay",
        stop_policy="One actual invocation per phase; first formal failure closes card, no retry/repair/force/extension")
    write(STAGE/"protocol.json",protocol)
    print(json.dumps(dict(status="frozen_not_executed", scientific_pins=len(pins),
                         sources=68,input_bindings=63,protocol_sha256=sha(STAGE/"protocol.json"))))


parser=argparse.ArgumentParser()
parser.add_argument("mode",choices=("install","freeze"))
args=parser.parse_args()
install() if args.mode == "install" else freeze()
