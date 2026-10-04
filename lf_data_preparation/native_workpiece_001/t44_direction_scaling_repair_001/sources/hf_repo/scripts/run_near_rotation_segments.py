"""Bounded, static saved-field attribution. Never calls a production solver.

The parent freezes selected inputs and source into a new independent directory.
Tests, reference closure, three cases and plots share one 300-second budget.
An unsuccessful phase stops the invocation; no retry or budget reset is offered.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

CASES = ("unit__near_rotation", "dyadic_rect__near_rotation", "nondyadic_rect__near_rotation")
FILES = ("inputs.npz", "input_freeze.json", "production_0.npz", "hp_0.json", "result.json")
COMPONENTS = ("total_force", "material_force", "regularization_force")
HP_KEYS = dict(zip(COMPONENTS, ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal")))
LIMITS = dict(zip(COMPONENTS, ("1e-11", "1e-9", "1e-9")))
PRECISIONS = (80, 120)
AGREEMENT = Decimal("1e-40")
SF = Decimal("1.2500e-7")
SOURCE = "hf4_c2_independent_recheck_20260927/manufactured_001"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False,
                  default=lambda x: str(x) if isinstance(x, Decimal) else fail("Unserializable value"))
        stream.write("\n")


def fail(message):
    raise ValueError(message)


def require(condition, message):
    if not condition:
        fail(message)


def decimal_tree(value):
    if isinstance(value, list):
        return [decimal_tree(item) for item in value]
    require(isinstance(value, str), "HP authority must be a Decimal string")
    result = Decimal(value)
    require(result.is_finite(), "Nonfinite HP authority")
    return result


def binary_tree(value):
    import numpy as np
    array = np.asarray(value)
    require(array.dtype.kind in "fiu" and bool(np.isfinite(array).all()), "Nonfinite/non-numeric binary64 input")
    if array.ndim:
        return [binary_tree(item) for item in array]
    return Decimal.from_float(float(array))


def flatten(value):
    if isinstance(value, list):
        return [leaf for item in value for leaf in flatten(item)]
    return [value]


def norm(values):
    return sum((value * value for value in values), Decimal(0)).sqrt()


def subtract(left, right):
    require(len(left) == len(right), "Vector dimension mismatch")
    return [a-b for a, b in zip(left, right)]


def forces(hp):
    return {name: decimal_tree(hp[key]) for name, key in HP_KEYS.items()}


def denominators(hp80):
    return {name: SF if name == "total_force" else max(norm(value), Decimal("1e-12")*SF)
            for name, value in hp80.items()}


def errors(values, reference, scales):
    return {name: norm(subtract(values[name], reference[name]))/scales[name] for name in COMPONENTS}


def agreement(values, reference, scales, label):
    result = errors(values, reference, scales)
    require(all(v <= AGREEMENT for v in result.values()), label+" does not close to 1e-40")
    return result


def load_case(root, case):
    import numpy as np
    directory = root/"inputs"/case
    with np.load(directory/"inputs.npz", allow_pickle=False) as data:
        fixture = {name: data[name].copy() for name in data.files}
    with np.load(directory/"production_0.npz", allow_pickle=False) as data:
        production = {name: data[name].copy() for name in data.files}
    hp, old, freeze = read(directory/"hp_0.json"), read(directory/"result.json"), read(directory/"input_freeze.json")
    require(freeze["input_sha256"] == sha(directory/"inputs.npz"), "Frozen input hash mismatch")
    require(freeze["physical_authority"] == "exact D(lift)+D(fluctuation)", "Split authority changed")
    require(freeze["level"] == .125 and freeze["force_scale_per_length"] == 100., "Normalization contract changed")
    require(old["case"] == case and old["directions"][0]["direction"] == 0, "Wrong saved case/direction")
    require(Decimal(old["directions"][0]["force_scale"]) == SF, "Original SF changed")
    require(bool(np.all(np.max(np.abs(production["G"]), axis=(-1, -2)) > .01)), "This card is restricted to the saved direct material branch")
    require(bool(np.all(production["J"] > 0)), "Nonpositive production J")
    hp80 = forces(hp["80"])
    fixed = set(map(int, fixture["fixed_dofs"]))
    values = hp80["total_force"]
    sf = max(norm([v for i, v in enumerate(values) if i in fixed]),
             norm([v for i, v in enumerate(values) if i not in fixed]),
             Decimal("1e-8")*Decimal(100)*max(Decimal(".125"), Decimal("1e-6")))
    require(sf == SF, "SF does not reproduce the frozen HP80 definition")
    return fixture, production, hp, old, hp80, denominators(hp80)


def check_bound_copy(root, repo=None):
    plan = read(root/"plan.json")
    for row in plan["frozen_files"]:
        require(sha(root/row["copy"]) == row["sha256"], "Frozen copy changed: "+row["copy"])
        if repo is not None:
            require(sha(repo/row["source"]) == row["sha256"], "Original source changed: "+row["source"])


def reference_phase(root):
    from hf4_split_precision_reference import DecimalSplitQ1Reference
    from near_rotation_field_assembly import assemble_fields
    check_bound_copy(root)
    records = []
    with localcontext() as context:
        context.prec = 120
        for case in CASES:
            fixture, production, hp, old, hp80, scales = load_case(root, case)
            record = {"case": case, "precision": {}, "force_scales": scales}
            record["saved_hp_precision_agreement"] = agreement(hp80, forces(hp["120"]), scales, case+" saved HP precision")
            endpoints = {}
            for precision in PRECISIONS:
                saved = hp[str(precision)]
                endpoint = assemble_fields(fixture, *(decimal_tree(saved[key]) for key in ("F_decimal", "J_decimal", "Hu_decimal")), precision=precision)
                rebuilt = DecimalSplitQ1Reference(fixture, precision=precision).evaluate(
                    fixture["u_lift"], fixture["u_fluctuation"], derivative=False)
                rebuilt_force = {name: rebuilt[key] for name, key in HP_KEYS.items()}
                endpoint_close = agreement(endpoint, forces(saved), scales, case+" field reconstruction")
                reference_close = agreement(rebuilt_force, forces(saved), scales, case+" original split reference")
                field_close = {}
                for key in ("F_decimal", "J_decimal", "Hu_decimal"):
                    value, expected = flatten(rebuilt[key]), flatten(decimal_tree(saved[key]))
                    field_close[key] = norm(subtract(value, expected))/max(norm(expected), Decimal(1))
                    require(field_close[key] <= AGREEMENT, "HP input reconstruction differs: "+key)
                endpoints[str(precision)] = {name: endpoint[name] for name in COMPONENTS}
                record["precision"][str(precision)] = dict(field_force_closure=endpoint_close,
                    frozen_reference_force_closure=reference_close, field_closure=field_close)
            record["precision_agreement"] = agreement(endpoints["80"], endpoints["120"], scales, case+" endpoint precision")
            record["E"] = endpoints
            records.append(record)
    dump(root/"reference_closure.json", dict(status="pass", cases=records,
         precision_gate=str(AGREEMENT), new_equilibrium_paths=0, tangent_evaluations=0))


def determinant_fields(F, precision):
    with localcontext() as context:
        context.prec = precision
        return [[q[0][0]*q[1][1]-q[0][1]*q[1][0] for q in element] for element in F]


def case_phase(root, case):
    from near_rotation_field_assembly import assemble_fields
    require(case in CASES, "Unexpected case")
    check_bound_copy(root)
    closure = read(root/"reference_closure.json")
    require(closure["status"] == "pass" and [r["case"] for r in closure["cases"]] == list(CASES), "All E closures must precede segments")
    with localcontext() as context:
        context.prec = 120
        fixture, production, hp, old, hp80, scales = load_case(root, case)
        A = {name: binary_tree(production[name]) for name in COMPONENTS}
        original_errors = errors(A, hp80, scales)
        original_checks = {row["name"]: row for row in old["directions"][0]["checks"]}
        for name in COMPONENTS:
            frozen = original_checks["candidate_"+name]
            require(Decimal(frozen["limit"]) == Decimal(LIMITS[name]), "Original gate changed")
            delta = abs(original_errors[name]-Decimal(frozen["value"]))/max(abs(Decimal(frozen["value"])), Decimal("1e-60"))
            require(delta <= AGREEMENT, "Original A error/normalization did not reproduce")
        Fp, Jp, Hup = (binary_tree(production[key]) for key in ("F", "J", "Hu"))
        stages, all_fields = {}, {}
        for precision in PRECISIONS:
            Fh, Jh, Huh = (decimal_tree(hp[str(precision)][key]) for key in ("F_decimal", "J_decimal", "Hu_decimal"))
            fields = {"B": (Fp, Jp, Hup), "C": (Fp, determinant_fields(Fp, precision), Hup),
                      "D": (Fh, Jh, Hup), "E": (Fh, Jh, Huh)}
            values = {"A": A}
            for name, inputs in fields.items():
                assembled = assemble_fields(fixture, *inputs, precision=precision)
                values[name] = {key: assembled[key] for key in COMPONENTS}
            require(values["D"]["material_force"] == values["E"]["material_force"], "Hu replacement changed material force")
            E_expected = next(row for row in closure["cases"] if row["case"] == case)["E"][str(precision)]
            agreement(values["E"], {k:decimal_tree(v) for k,v in E_expected.items()}, scales, "Repeated E identity")
            stages[str(precision)] = values
            all_fields[str(precision)] = {name: dict(F=f, J=j, Hu=h) for name,(f,j,h) in fields.items()}
        precision_checks = {name: agreement(stages["80"][name], stages["120"][name], scales, name+" precision") for name in "BCDE"}
        values = stages["120"]
        changes = {left+"_to_"+right: {key:subtract(values[right][key], values[left][key]) for key in COMPONENTS}
                   for left,right in zip("ABCD", "BCDE")}
        telescoping = {}
        for key in COMPONENTS:
            summed = [sum((row[key][i] for row in changes.values()), Decimal(0)) for i in range(len(A[key]))]
            telescoping[key] = norm(subtract(summed, subtract(values["E"][key], A[key])))/scales[key]
            require(telescoping[key] <= AGREEMENT, "Sequential difference closure failed")
        measured = {name: errors(value, hp80, scales) for name,value in values.items()}
        gates = {name: {key: value <= Decimal(LIMITS[key]) for key,value in row.items()} for name,row in measured.items()}
        diagnostics = dict(production_J=binary_tree(production["J"]),
            hp120_J=decimal_tree(hp["120"]["J_decimal"]), production_Hu=Hup,
            hp120_Hu=decimal_tree(hp["120"]["Hu_decimal"]), max_abs_production_G=str(abs(production["G"]).max()))
        dump(root/"cases"/(case+".json"), dict(status="diagnosis_complete", case=case, direction=0,
            original_candidate_status=old["status"], mechanical_admission=False,
            force_scale=SF, denominators=scales, thresholds=LIMITS, original_errors_reproduced=original_errors,
            stages=stages, selected_fields=all_fields, normalized_errors_hp120_vs_original_hp80=measured,
            comparison_to_original_gates=gates, sequential_differences=changes,
            normalized_change_magnitudes={name:{key:norm(v)/scales[key] for key,v in row.items()} for name,row in changes.items()},
            precision_agreement=precision_checks, telescoping_error=telescoping,
            production_total_minus_component_sum=subtract(A["total_force"], [a+b for a,b in zip(A["material_force"],A["regularization_force"])]),
            kinematics=diagnostics, interpretation="Ordered mixed-intermediate diagnostics, not independent error shares or new physical states."))


def plot_phase(root):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    records = [read(root/"cases"/(case+".json")) for case in CASES]
    fig, axes = plt.subplots(3, 3, figsize=(12, 9), constrained_layout=True)
    for row, data in enumerate(records):
        for col, component in enumerate(COMPONENTS):
            ax = axes[row,col]
            values = [float(data["normalized_errors_hp120_vs_original_hp80"][s][component]) for s in "ABCDE"]
            ax.semilogy(list("ABCDE"), [max(v,1e-85) for v in values], "o-", color="#156d89")
            ax.axhline(float(LIMITS[component]), color="#b53d35", linestyle="--", label="Original gate")
            ax.set_title(data["case"].replace("__near_rotation", "")+" / "+component.replace("_force", ""))
            ax.set_ylabel("Error / original denominator")
            ax.grid(True, alpha=.2)
    fig.suptitle("Saved-field diagnostic: 120-digit segments vs original HP80\nE is an oracle reconstruction, not a repaired production kernel. Exact zeros plotted at 1e-85.")
    for suffix in ("png", "svg"):
        fig.savefig(root/("segment_errors."+suffix), dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(3, 3, figsize=(14, 9), constrained_layout=True)
    with localcontext() as context:
        context.prec = 120
        for row,data in enumerate(records):
            for name,change in data["sequential_differences"].items():
                axes[row,0].plot([float(Decimal(v)/SF) for v in change["total_force"]], ".-", label=name)
            for name in "BCD":
                selected=data["selected_fields"]["120"][name]["J"]
                axes[row,1].plot([float(Decimal(v)-1) for v in flatten(selected)], ".-", label=name)
            for name in ("production_Hu", "hp120_Hu"):
                axes[row,2].plot([float(Decimal(v)) for v in flatten(data["kinematics"][name])], ".-", label=name)
            for col,title in enumerate(("Signed total-force changes / SF", "Selected J - 1", "Saved Hu components")):
                axes[row,col].set_title(data["case"].replace("__near_rotation", "")+" / "+title)
                axes[row,col].ticklabel_format(axis="y", style="sci", scilimits=(0,0))
                axes[row,col].grid(True, alpha=.2)
                axes[row,col].legend(fontsize=7)
    fig.suptitle("Ordered substitutions: vector differences telescope; norms are not additive shares")
    for suffix in ("png", "svg"):
        fig.savefig(root/("ordered_changes."+suffix), dpi=160)
    plt.close(fig)
    dump(root/"summary.json", dict(status="diagnosis_complete", cases=list(CASES), direction=0,
        new_equilibrium_paths=0, tangent_evaluations=0, mechanical_admission=False,
        reference_closure="pass", original_failures_preserved=True,
        results={d["case"]:dict(errors=d["normalized_errors_hp120_vs_original_hp80"], gates=d["comparison_to_original_gates"]) for d in records},
        scope="Three saved static fields; no new kernel, production solve, formal label or ranking."))


def prepare(repo, output):
    import importlib.metadata as metadata
    require(not output.exists(), "Output already exists; do not reset or retry this run")
    require(output.parent == repo/"hf4_c2_stable_f_validation", "Output must be a new direct child of the existing validation family")
    origin=subprocess.check_output(["git","remote","get-url","origin"],cwd=repo,text=True).strip()
    require(origin == "https://github.com/dudaxing/Compliant-TO-TMC.git", "Wrong origin")
    require(subprocess.check_output(["git","branch","--show-current"],cwd=repo,text=True).strip()=="main", "Wrong branch")
    base=repo/SOURCE; bindings=read(base/"results/output_sha256.json"); original_plan=read(base/"results/plan.json")
    sources=[]
    for case in CASES:
        for name in FILES:
            relative=case+"/"+name; path=base/"results"/relative
            require(sha(path)==bindings[relative], "Historical input mismatch: "+relative)
            sources.append((path, "inputs/"+relative))
    for name in ("hf2_precision_reference.py","hf4_split_precision_reference.py"):
        path=repo/"hf_repo/scripts"/name
        require(sha(path)==original_plan["baseline_source_files"]["hf_repo/scripts/"+name], "Historical HP source changed: "+name)
        sources.append((path, "source_snapshot/hf_repo/scripts/"+name))
    for name in ("near_rotation_field_assembly.py","run_near_rotation_segments.py"):
        sources.append((repo/"hf_repo/scripts"/name, "source_snapshot/hf_repo/scripts/"+name))
    sources.append((repo/"hf_repo/tests/test_near_rotation_field_assembly.py", "source_snapshot/hf_repo/tests/test_near_rotation_field_assembly.py"))
    for name in ("results/plan.json","results/output_sha256.json","execution_receipt.json","source_snapshot/hf_repo/scripts/validate_contact_c2_stable_f.py"):
        sources.append((base/name, "original_run/"+name))
    frozen=[dict(source=path.relative_to(repo).as_posix(),copy=relative,
                 bytes=path.stat().st_size,sha256=sha(path)) for path,relative in sources]
    output.mkdir(parents=False, exist_ok=False)
    dump(output/"preparation_bindings.json", dict(frozen_files=frozen))
    for (path,relative), row in zip(sources, frozen):
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
        require(sha(path)==sha(target)==row["sha256"], "Copy or source mismatch")
    plan=dict(schema="near-rotation-segments-plan-1", created_utc=datetime.now(timezone.utc).isoformat(),
        authorization="User: 授权执行诊断卡", baseline_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
        repo=str(repo), origin=origin, output=str(output), cases=list(CASES), direction=0,
        source_run=SOURCE, frozen_files=frozen, precision_digits=list(PRECISIONS), SF=str(SF),
        original_thresholds=LIMITS, reference_closure_and_precision_gate=str(AGREEMENT),
        total_wall_seconds=300, per_phase_wall_seconds=60, process_tree_rss_limit_bytes=2*1024**3,
        retry_allowed=False, tests_charged_to_total=True, production_kernel_changes=False,
        new_equilibrium_paths=0, formal_labels=False, commits_or_push=False,
        python=sys.version, executable=sys.executable,
        versions={name:metadata.version(name) for name in ("numpy","matplotlib","pytest","psutil","jax","jaxlib")},
        precision_semantics="Decimal string authority; binary64 inputs promoted with from_float; original HP80 force denominators fixed",
        segments={"A":"Exact promotion of saved main production force arrays; not force-only arrays or re-added components",
                  "B":"HP assembly of production F, supplied production J and production Hu",
                  "C":"HP assembly of production F, det(F) at declared precision, production Hu",
                  "D":"HP assembly of saved HP F/J and production Hu",
                  "E":"HP assembly of saved HP F/J/Hu; first closes against saved HP and frozen reference evaluator"},
        fixed_denominators="Total: original SF; each component: max(norm(original HP80 component), 1e-12 SF)",
        interpretation="B changes downstream arithmetic; B-to-C changes logJ, inverse denominator and exponential together; C-to-D changes F and consistent J; D-to-E only Hu. Difference vectors telescope, not error shares.",
        budget_scope="Preparation, synthetic tests, reference closure, segment calculations, plots and evidence finalization in one invocation; authoring/static review and later report prose excluded",
        sequence=["synthetic tests", "all E closures", *CASES, "plots and summary"],
        scientific_stop="Source mismatch, failed tests, failed E closure, nonfinite/invalid fields or budget limit stops without retry.")
    dump(output/"plan.json",plan)
    return plan


def execute(repo, output):
    import psutil
    require(not output.exists(), "Output already exists; do not reset or retry this run")
    started=time.monotonic(); plan=None
    receipt=dict(schema="near-rotation-segments-receipt-1",status="preparing",
        started_utc=datetime.now(timezone.utc).isoformat(),phases=[],peak_tree_rss_bytes=0,
        new_equilibrium_paths=0,tangent_evaluations=0)
    def save():
        (output/"execution_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    script=output/"source_snapshot/hf_repo/scripts/run_near_rotation_segments.py"
    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8", PYTHONPATH=str(script.parent),
             OMP_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",MKL_NUM_THREADS="1",MPLBACKEND="Agg",PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
             JAX_ENABLE_X64="true",JAX_PLATFORMS="cpu",JAX_ENABLE_COMPILATION_CACHE="false",
             MPLCONFIGDIR=str(output/"plot_cache"))
    commands=[("tests",["-m","pytest",str(output/"source_snapshot/hf_repo/tests/test_near_rotation_field_assembly.py"),
                       "-q","-p","no:cacheprovider","--basetemp",str(output/"test_tmp"),"--junitxml="+str(output/"tests.xml")]),
              ("reference",[str(script),"--phase","reference","--root",str(output)])]
    commands += [(case,[str(script),"--phase","case","--case",case,"--root",str(output)]) for case in CASES]
    commands += [("plots",[str(script),"--phase","plots","--root",str(output)])]
    try:
        plan=prepare(repo,output)
        receipt.update(status="running",plan_sha256=sha(output/"plan.json"))
        save()
        for label,args in commands:
            check_bound_copy(output,repo)
            remaining=300-(time.monotonic()-started)
            require(remaining>0,"Total wall budget exhausted")
            phase_started=time.monotonic(); command=[sys.executable,"-B",*args]
            row=dict(name=label,command=command,status="running");receipt["phases"].append(row);save()
            with (output/(label+".log")).open("x",encoding="utf-8") as log:
                child=subprocess.Popen(command,cwd=output,env=env,stdout=log,stderr=subprocess.STDOUT)
                process=psutil.Process(child.pid);reason=None
                while child.poll() is None:
                    family=[psutil.Process(os.getpid()),process]
                    try:
                        family.extend(process.children(recursive=True))
                    except psutil.NoSuchProcess:pass
                    except psutil.AccessDenied:reason="resource_monitor_unavailable"
                    rss=0
                    for member in family:
                        try:rss+=member.memory_info().rss
                        except psutil.NoSuchProcess:pass
                        except psutil.AccessDenied:reason="resource_monitor_unavailable"
                    receipt["peak_tree_rss_bytes"]=max(receipt["peak_tree_rss_bytes"],rss)
                    if rss>2*1024**3:reason="memory_limit"
                    if time.monotonic()-phase_started>min(60,remaining):reason="wall_limit"
                    if reason:
                        try:
                            descendants=process.children(recursive=True)
                        except psutil.NoSuchProcess:descendants=[]
                        for member in [*reversed(descendants),process]:
                            try:member.kill()
                            except psutil.NoSuchProcess:pass
                        break
                    time.sleep(.1)
                returncode=child.wait(timeout=2)
            row.update(returncode=returncode,elapsed_seconds=time.monotonic()-phase_started,
                       status=reason or ("pass" if returncode==0 else "failed"),log_sha256=sha(output/(label+".log")))
            save();print(json.dumps(row),flush=True)
            check_bound_copy(output,repo)
            require(returncode==0 and reason is None,"Stopped after phase "+label)
        receipt.update(status="diagnosis_complete")
    except Exception as error:
        receipt.update(status="stopped_preserved",error_type=type(error).__name__,error=str(error))
    finally:
        if output.exists():
            binding_path=output/"preparation_bindings.json"
            bindings=plan or (read(binding_path) if binding_path.exists() else {"frozen_files":[]})
            audit=[]
            for row in bindings["frozen_files"]:
                item=dict(source=row["source"],copy=row["copy"],expected_sha256=row["sha256"])
                for key,path in (("source",repo/row["source"]),("copy",output/row["copy"])):
                    try:item[key+"_sha256"]=sha(path)
                    except OSError as error:item[key+"_error"]=str(error)
                    item[key+"_unchanged"]=item.get(key+"_sha256")==row["sha256"]
                audit.append(item)
            dump(output/"source_preservation.json",audit)
            receipt.update(original_sources_unchanged=bool(audit) and all(row["source_unchanged"] for row in audit),
                           frozen_copy_unchanged=bool(audit) and all(row["copy_unchanged"] for row in audit))
            if not receipt["original_sources_unchanged"] or not receipt["frozen_copy_unchanged"]:
                receipt.update(status="stopped_preserved",preservation_error="Source or copy missing/changed; inspect source_preservation.json")
            # Payload manifest excludes this mutable receipt, preventing circular hashes.
            outputs={p.relative_to(output).as_posix():sha(p) for p in output.rglob("*") if p.is_file() and not p.is_relative_to(output/"plot_cache") and not p.is_relative_to(output/"test_tmp") and p.name not in ("output_sha256.json","execution_receipt.json")}
            dump(output/"output_sha256.json",outputs)
            receipt["output_manifest_sha256"]=sha(output/"output_sha256.json")
            receipt.update(elapsed_seconds=time.monotonic()-started,finished_utc=datetime.now(timezone.utc).isoformat())
            if receipt["elapsed_seconds"]>300:
                receipt.update(status="stopped_preserved",budget_error="Total wall budget exceeded including payload finalization")
            save()
            # One final receipt write is outside its own timestamp; never claim it was timed.
            receipt["receipt_write_tail_seconds"]=time.monotonic()-started-receipt["elapsed_seconds"]
            if time.monotonic()-started>300:
                receipt.update(status="stopped_preserved",budget_error="Total wall budget exceeded on receipt persistence")
            save()
    print(json.dumps(receipt),flush=True)
    return 0 if receipt["status"]=="diagnosis_complete" else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase",choices=("execute","reference","case","plots"),default="execute")
    parser.add_argument("--root",type=Path)
    parser.add_argument("--case",choices=CASES)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.phase=="execute":
        if args.output is None:parser.error("--output is required")
        return execute(Path(__file__).resolve().parents[2],args.output.resolve())
    if args.root is None:parser.error("--root is required")
    if args.phase=="reference":reference_phase(args.root.resolve())
    elif args.phase=="case":case_phase(args.root.resolve(),args.case)
    else:plot_phase(args.root.resolve())
    return 0


if __name__=="__main__":
    raise SystemExit(main())
