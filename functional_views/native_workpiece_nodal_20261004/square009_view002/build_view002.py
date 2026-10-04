"""Prepare a separate display correction after zero-arrow visual failure."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil

digest = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    old = root/"functional_views/native_workpiece_nodal_20261004/square009_001"
    stage = old.with_name("square009_view002")
    author = Path(__file__).resolve().parent
    pins = {}
    rel = lambda p: p.relative_to(root).as_posix()

    def bind(path, expected=None):
        value = digest(path)
        assert expected is None or value == expected, rel(path)
        pins[rel(path)] = value
        return value

    bind(old/"protocol.json")
    for name, value in read(old/"protocol.json")["bindings"].items():
        bind(root/name, value)
    for phase in ("tests", "observe", "render"):
        receipt = read(old/(phase+"_launch.json"))
        assert receipt["status"] == "pass" and receipt["exit_code"] == 0
        assert receipt["invocations"] == 1 and receipt["all_bindings_unchanged"]
        bind(old/(phase+"_launch.json"))
    for directory in ("observation_001", "render_001"):
        for p in (old/directory).rglob("*"):
            if p.is_file():
                bind(p)
    original = (old/"plot_saved_nodal_forces.py").read_bytes()
    assert original.count(b"minlength=0,minshaft=0") == 1
    candidate = original.replace(b"minlength=0,minshaft=0", b"minlength=0,minshaft=1")
    assert not stage.exists()
    stage.mkdir()
    shutil.copyfile(old/"launch_phase.py", stage/"launch_phase.py")
    bind(stage/"launch_phase.py", digest(old/"launch_phase.py"))
    (stage/"plot_saved_nodal_forces002.py").write_bytes(candidate)
    bind(stage/"plot_saved_nodal_forces002.py")
    assert (stage/"plot_saved_nodal_forces002.py").read_bytes().replace(
        b"minlength=0,minshaft=1",b"minlength=0,minshaft=0") == original
    shutil.copyfile(Path(__file__).resolve(), stage/"build_view002.py")
    bind(stage/"build_view002.py", digest(Path(__file__).resolve()))
    shutil.copyfile(author/"visual001_readonly_review.json", stage/"visual001_readonly_review.json")
    bind(stage/"visual001_readonly_review.json")
    argv = read(old/"protocol.json")["phases"]["render"]["argv"]
    argv = [value.replace(rel(old/"plot_saved_nodal_forces.py"), rel(stage/"plot_saved_nodal_forces002.py"))
                 .replace(rel(old/"render_001"), rel(stage/"render_001"))
                 .replace(rel(old/"stop_requested.txt"), rel(stage/"stop_requested.txt")) for value in argv]
    protocol = dict(schema_version="saved-nodal-force-display-correction-1.0", bindings=pins,
        sampled_RSS_bytes=8*1024**3,
        phases={"render":dict(helper_seconds=120,outer_seconds=150,argv=argv)},
        changed_literal="minshaft=0 -> minshaft=1; zero/short vectors scale their heads; minlength=0 unchanged",
        inverse_bytes_exact=True, inherited_observations=9, inherited_csv_rows=1377,
        scope="Only plotting saved identical CSV/state data; no new tests, observation, geometry metrics, F/T/equilibrium/HP",
        stop_policy="One invocation; first failure closes new card; no repair/retry/force/budget extension")
    (stage/"protocol.json").write_text(json.dumps(protocol,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="prepared_not_rendered",bindings=len(pins),protocol_sha256=digest(stage/"protocol.json"))))


if __name__ == "__main__":
    main()
