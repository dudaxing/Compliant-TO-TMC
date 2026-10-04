"""Freeze a saved-only view card; no observations or numerical calls."""
from pathlib import Path
from hashlib import sha256
import argparse,json,shutil

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--stage",required=True)
    p.add_argument("--case",action="append",required=True)
    p.add_argument("--reference",action="append",default=[])
    a=p.parse_args();root=a.repo.resolve();stage=root/a.stage;author=Path(__file__).resolve().parent
    assert not stage.exists()
    sources=[root/"hf_repo"/s for s in ("src/hf_eval/__init__.py","src/hf_eval/native_region_geometry.py",
        "src/hf_eval/boundary_geometry.py","src/hf_eval/workpiece_nodal.py","scripts/measure_native_workpiece_regions.py")]
    viewer=author/"saved_shift_views.py"
    assert sha256(viewer.read_bytes()).hexdigest()=="16d2c0295d03579a32adaf321a283ad9ae6f23579c4455f688be8720bb1984b0"
    compile(viewer.read_text(encoding="utf-8"),str(viewer),"exec")
    stage.mkdir(parents=True)
    for file in (viewer,author/"saved_shift_views_README.md",author/"saved_shift_views_author_note.json",Path(__file__).resolve()):
        shutil.copyfile(file,stage/file.name)
    launcher=root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/launch_cycle010.py"
    shutil.copyfile(launcher,stage/"launch_view.py")
    files=sources+[x for x in stage.iterdir() if x.is_file()]
    prefix=stage.relative_to(root).as_posix()
    argv=[prefix+"/saved_shift_views.py","--repo","hf_repo","--protocol",prefix+"/protocol.json",
        "--output",prefix+"/view","--time-limit","120","--stop-file",prefix+"/stop_requested.txt"]
    counts={}
    for spec in a.case:
        label,name=spec.split("=",1);directory=root/name;directory.relative_to(root)
        result=json.loads((directory/"result.json").read_text(encoding="utf-8"))
        counts[label]=dict(accepted_states=result["accepted_states"],production_status=result["status"],complete=result["path_completed"])
        files += [x for x in directory.rglob("*") if x.is_file()]
        argv += ["--case",spec]
    for spec in a.reference:
        _,name=spec.split("=",1);files.append(root/name);argv += ["--reference",spec]
    bindings={f.relative_to(root).as_posix():sha256(f.read_bytes()).hexdigest() for f in files}
    protocol=dict(schema_version="saved-shift-view-card-1.0",bindings=bindings,sampled_RSS_bytes=8*1024**3,
        phases=dict(view=dict(helper_seconds=120,outer_seconds=150,argv=argv)),cases=counts,
        scope="Actual saved-state geometry/nodal weak-force observations and x1 plots; partial paths explicitly allowed as preliminary only.",
        zero_mechanics_contract="Allowed pure module origins and saved-array derivations; no dynamic mechanics hook monitoring.",
        stop_policy="One phase once; first failure closes, no retry/repair/extension/force. No mechanics or HP qualification.",
        static_review=dict(reviewer="root",quiver_minlength=0,minshaft=1,source_compile=True,
            checks=["pure import closure and source origins", "saved result/model/state/force hashes", "status and partial path labels", "actual-index GIF and shared scales", "tip finite-segment distances are not contact pressure"]))
    with (stage/"protocol.json").open("x",encoding="utf-8") as f:json.dump(protocol,f,indent=2);f.write("\n")
    print(json.dumps(dict(status="frozen_only",bindings=len(bindings),cases=counts)))

if __name__=="__main__":main()
