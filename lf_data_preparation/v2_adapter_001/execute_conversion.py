"""One three-package native data conversion; no LF or HF mechanics execution."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "hf_repo/src"))
from hf_eval.data import load_geometry
from hf_eval.lf_v2 import convert_lf_v2


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    inventory = json.loads((ROOT / "source_inventory.json").read_text(encoding="utf-8"))
    paths = [REPO / "hf_repo/src/hf_eval" / name for name in ("lf_v2.py", "data.py", "regions.py", "__init__.py")]
    paths += [REPO / "hf_repo/scripts" / name for name in ("import_lf_v2.py", "plot_lf_v2_conversion.py")]
    paths += [REPO / "hf_repo/tests/test_lf_v2.py", ROOT / "review_conversion.py", Path(__file__)]
    source_dir = ROOT / "sources"
    source_dir.mkdir(exist_ok=False)
    bindings = []
    for path in paths:
        copied = source_dir / path.name
        shutil.copyfile(path, copied)
        bindings.append(dict(name=path.name, sha256=digest(path), path=str(path.relative_to(REPO))))
        assert digest(copied) == bindings[-1]["sha256"]
    started, process = perf_counter(), psutil.Process()
    receipt = dict(schema_version="lf-v2-conversion-execution-1.0", status="running",
        started_utc=datetime.now(timezone.utc).isoformat(), baseline_commit=inventory["baseline_commit"],
        continuous_seconds=120, sampled_RSS_limit_bytes=8*1024**3, sources=bindings, cases=[],
        LF_imports=0, FE_calls=0, force_calls=0, HP_calls=0, solver_calls=0,
        scope="Three selected native packages only; no formal HF qualification or bulk candidate evaluation")
    write(ROOT / "execution_receipt.json", receipt)

    def checkpoint():
        if perf_counter() - started > 120.:
            raise RuntimeError("Data conversion stage exceeds120 seconds")
        if process.memory_info().rss > 8*1024**3:
            raise RuntimeError("Sampled data conversion RSS exceeds8GiB")

    try:
        for row in inventory["selected"]:
            checkpoint()
            source = ROOT / "inputs" / row["alias"] / "design.json"
            assert digest(source) == row["descriptor_sha256"]
            assert digest(source.with_name("design.npz")) == row["NPZ_sha256"]
            before = perf_counter()
            result = convert_lf_v2(source, ROOT / "converted" / row["alias"],
                                  expected_descriptor_sha256=row["descriptor_sha256"])
            geometry = load_geometry(result)
            receipt["cases"].append(dict(alias=row["alias"], status="pass", invocations=1,
                elapsed_seconds=perf_counter()-before, HF_geometry_id=geometry.geometry_id,
                descriptor=str(result.relative_to(ROOT)), descriptor_sha256=digest(result),
                array_sha256=digest(result.with_name("geometry.npz")),
                native_shape_yx=geometry.grid["shape_yx"], solid_cells=int(geometry.solid.sum())))
            write(ROOT / "execution_receipt.json", receipt)
            checkpoint()
        for path, binding in zip(paths, bindings):
            assert digest(path) == binding["sha256"] == digest(source_dir / path.name)
        for row in inventory["selected"]:
            source = ROOT / "inputs" / row["alias"] / "design.json"
            assert digest(source) == row["descriptor_sha256"]
            assert digest(source.with_name("design.npz")) == row["NPZ_sha256"]
        assert not any(name == "dmftd" or name.startswith("dmftd.") for name in sys.modules)
        assert not any(name in sys.modules for name in ("hf_eval.project", "hf_eval.tmc", "hf_eval.evaluation"))
        checkpoint()
        receipt.update(status="pass", completed_cases=3, input_and_source_identity_checked=True)
    except Exception as error:
        receipt.update(status="stopped", failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        memory = process.memory_info()
        receipt.update(elapsed_seconds=perf_counter()-started,
            peak_working_set_bytes=getattr(memory, "peak_wset", memory.rss),
            budget_mode="Cooperative sampled checks, not hard OS supervision")
        write(ROOT / "execution_receipt.json", receipt)
    print(json.dumps(dict(status=receipt["status"], cases=receipt["completed_cases"],
                         elapsed_seconds=receipt["elapsed_seconds"])))


if __name__ == "__main__":
    main()
