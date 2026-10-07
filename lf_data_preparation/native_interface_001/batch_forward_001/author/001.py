"""Freeze a reviewed fresh two-case stage, without importing or executing HF."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import ast
import json
import subprocess

HEAD = "aa072bc08ead34e88a2edf0cb4bffedba2161bbb"
STAGE = "lf_data_preparation/native_interface_001/batch_forward_001"
FUNCTIONAL = "lf_data_preparation/native_interface_001/batch_validation_001/functional_protocol.json"
MANIFEST = "lf_data_preparation/native_interface_001/batch_validation_001/example_two_case_manifest.json"
OLD = dict(canonical="lf_data_preparation/native_gripper_task_025_001",
           native_fine="lf_data_preparation/native_fine_task_025_001")
OPTIONS = dict(targets=[0., .005, .010, .025], minimum_increment=.0000625,
               time_limit_seconds=1800, response_mode="complete",
               tangent_mode="full", initial_guess="tangent")
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root-review", type=Path, required=True)
    parser.add_argument("--peer-review", type=Path, required=True)
    args = parser.parse_args()
    root, author = args.repo.resolve(), Path(__file__).resolve().parent
    stage = root/STAGE
    assert not author.is_relative_to(root) and not stage.exists()
    git = lambda *args: subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    assert git("rev-parse", "HEAD") == HEAD and git("branch", "--show-current") == "main"
    assert git("remote", "get-url", "origin") == "https://github.com/dudaxing/Compliant-TO-TMC.git"
    worker = author/"execute_batch_forward.py"
    for source in (worker, Path(__file__)):
        compile(ast.parse(source.read_text(encoding="utf-8")), str(source), "exec")
    reports = [args.root_review.resolve(), args.peer_review.resolve()]
    for report in reports:
        review = read(report)
        assert review["status"] == "pass_static_only" and not review["blocking_findings"]
        for source in (worker, Path(__file__)):
            values = {pin for name, pin in review["source_sha256"].items() if Path(name).name == source.name}
            assert values == {sha(source)}
    functional = read(root/FUNCTIONAL)
    bindings = {name: pin for name, pin in functional["bindings"].items()
                if name.startswith("hf_repo/src/")}
    assert len(bindings) == 28 and all(sha(root/name) == pin for name, pin in bindings.items())
    manifest = read(root/MANIFEST)
    assert manifest["schema_version"] == "hf-native-batch-manifest-1.0" and manifest["options"] == OPTIONS
    assert [case["label"] for case in manifest["cases"]] == list(OLD)
    expected_counts, histories = {}, {}
    shared, settings, gates = None, None, None
    inputs = [MANIFEST, FUNCTIONAL]
    for case in manifest["cases"]:
        label, base = case["label"], OLD[case["label"]]
        assert case["output"] == STAGE+"/run_001/"+label and not (root/case["output"]).exists()
        geometry, task = read(root/case["geometry"]), read(root/case["task"])
        assert task["geometry"] == {key: geometry[key] for key in ("geometry_id", "descriptor_sha256")}
        assert task["input"]["target_mm"] == .025 and task["workpiece"] is None and "path" not in task
        physical = {key: value for key, value in task.items() if key not in ("task_id", "geometry")}
        assert shared is None or shared == physical
        shared = physical
        inventory, historical, old_receipt = (read(root/base/name) for name in
            ("input_inventory.json", "result/result.json", "execution_receipt.json"))
        assert inventory["case"]["prior_task_file"] == case["task"]
        assert inventory["case"]["geometry_file"] == case["geometry"]
        assert sha(root/case["task"]) == inventory["case"]["prior_task_sha256"]
        assert sha(root/case["geometry"]) == inventory["case"]["geometry_file_sha256"]
        array_file = str(Path(case["geometry"]).with_suffix(".npz")).replace("\\", "/")
        assert sha(root/array_file) == inventory["case"]["geometry_npz_sha256"]
        actual_settings = inventory["settings"] | {"time_limit_seconds": 1800.}
        assert settings is None or settings == actual_settings
        settings = actual_settings
        assert gates is None or gates == inventory["gates"]
        gates = inventory["gates"]
        assert historical["targets_mm"] == OPTIONS["targets"] and old_receipt["status"] == "pass"
        expected_counts[label] = historical["counts"]
        histories[label] = dict(helper_seconds=old_receipt["elapsed_seconds"],
            accepted_states=historical["accepted_states"], call_counts=historical["call_counts"],
            role="Cost and constructor-size context only; no qualification inherited")
        inputs += [case["geometry"], array_file, case["task"],
                   *[base+"/"+name for name in ("input_inventory.json", "result/result.json", "execution_receipt.json")]]
    assert gates["production_residual"] == "1e-9" and gates["global_force_balance"] == "1e-6"
    assert gates["fixed_displacement_mm"] == "8e-11" and settings["minimum_increment"] == .0000625
    bindings.update({name: sha(root/name) for name in inputs})
    launcher = root/"lf_data_preparation/native_interface_001/batch_validation_001/launch_pose.py"
    assert sha(launcher) == "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
    selections = [Path(__file__).resolve(), author/"README.md", author/"author_checks.json", author/"root_static_review.py",
                  author/"context/inputs_costs.json", author/"context/inputs_costs.md", *reports]
    assert all(path.is_file() for path in selections)
    # Above: AST, ordinary file hashes/JSON and read-only Git only. No HF or NPZ imports.
    stage.mkdir(parents=True)
    (stage/"author").mkdir()
    (stage/"execute_batch_forward.py").write_bytes(worker.read_bytes())
    (stage/"launch_pose.py").write_bytes(launcher.read_bytes())
    bindings[STAGE+"/execute_batch_forward.py"] = sha(stage/"execute_batch_forward.py")
    bindings[STAGE+"/launch_pose.py"] = sha(stage/"launch_pose.py")
    archive = {}
    for index, source in enumerate(selections, 1):
        name = f"{index:03d}{source.suffix}"
        target = stage/"author"/name
        target.write_bytes(source.read_bytes())
        logical = target.relative_to(root).as_posix()
        bindings[logical] = sha(target)
        archive[name] = dict(source_name=str(source), path=logical, sha256=sha(target))
    write(stage/"author/INDEX.json", archive)
    protocol = dict(schema_version="native-real-batch-protocol-1.0", baseline_commit=HEAD,
        bindings=bindings, sampled_RSS_bytes=8*1024**3,
        phases=dict(production=dict(helper_seconds=2400, outer_seconds=2460,
            argv=[STAGE+"/execute_batch_forward.py", "--repo", ".", "--protocol", STAGE+"/production_protocol.json"])),
        manifest_file=MANIFEST, run_directory=STAGE+"/run_001", batch_directory=STAGE+"/run_001/batch",
        targets_mm=OPTIONS["targets"], options=OPTIONS, settings=settings, gates=gates,
        expected_counts=expected_counts, expected_model_fields=23, historical_costs=histories,
        science_scope="One new ordered batch; each attempted native design once; native grids differ; no workpiece/HP/JIT/LF/plots/ranking",
        resource_scope="Shared controller1800 seconds per case, whole-helper2400 and outer2460 total; sampled RSS only, no OS hard cap/force",
        prefix_scope="Original returned failed response/accepted cache retained; escaping resources may leave scalar prefix and interrupted index only",
        stop_policy="First non-success or stage/resource failure stops; no repair/retry/force/old-window extension",
        inherited_gate_scope="Original .025 inventories; independent HP gates recorded but not evaluated in production",
        qualification_scope="Actual transport and production gates only; independent reference, pressure/contact/HF5/ranking remain unqualified",
        created_utc=datetime.now(timezone.utc).isoformat())
    write(stage/"production_protocol.json", protocol)
    (stage/"EXECUTION_CARD.md").write_text("""# 两例真实 batch 执行卡

目标：用当前薄 batch 一次顺序计算 canonical 与 native_fine 原0.025 mm无工件任务，验证同一物理声明下实际构模、求解、缓存保存、response和index。HF读取原LF普通几何；不优化、不调用LF或dmftd。

输入：production_protocol.json所绑定的28个当前HF源、manifest、两份原task、geometry.json/npz以及门槛/成本来源。两设计的原生网格分别h1和h0.5；它们不是同设计细化。各例零lift/未变形开始，目标0、0.005、0.010、0.025 mm，最小增量6.25e-5 mm，complete/full/tangent保持。

执行：全批JSON预检后各例一次；继承既有controller、真实力和切线、cached writer与formatter。仅插入阶段计数、前后资源检查和原capture后的标量进度；保留原固定DOF缓存门检查。保存不得新增F/T，不持有前例大缓存进入后一例；每例API返回后单次垃圾回收清理不可达controller递归闭包，计入本段时间。原门包括production residual1e-9、原约束bound、J>0、global balance1e-6、fixed8e-11 mm。独参门仅记录。

预算：一次连续whole-helper2400秒、外层2460秒、8 GiB采样RSS；共享controller1800秒是每例求解限额，不能代替全段时钟。旧两例生产约176.48和1099.22秒仅作成本背景。合作停止/采样内存，不宣称OS硬限制，不force、不重试、不借旧卡剩余额度。

完成：两例各自原目标到达，真实delegate计数和F/T与结果对账，原生产门通过，缓存保存0额外F/T，source/input hashes不变，response与batch index身份一致。保留每例真实状态数、失败和last accepted，不能用旧14F/9T猜测新迭代次数。

停止：首非success、输入/source改变、资源越限或包装异常即结束。原已保存失败/partial不改写；资源异常继续传播，可能只留下标量接受前缀及interrupted index。不得修复后重开本卡。

输出：run_001下每例result/response、batch/index、accepted_progress.jsonl与执行回执。独立参考和实际状态图另按实际N冻结新阶段；本卡不生成图，不授予接触/压力、网格收敛、排名或HF5资格。
""", encoding="utf-8")
    write(stage/"installation_receipt.json", dict(status="installed_not_executed", baseline_commit=HEAD,
        protocol_sha256=sha(stage/"production_protocol.json"), bindings=len(bindings),
        scientific_calls=0, next="One production launch, then references/views from actual states",
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status="installed_not_executed", protocol_sha256=sha(stage/"production_protocol.json"),
                         bindings=len(bindings)), ensure_ascii=False))


if __name__ == "__main__":
    main()
