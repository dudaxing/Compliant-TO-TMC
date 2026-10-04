"""One saved-only plotting window; frozen source and actual file bindings."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import runpy
import sys

STARTED=perf_counter()
STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
sha=lambda p:sha256(p.read_bytes()).hexdigest()


def main():
    protocol=json.loads((STAGE/"protocol.json").read_text(encoding="utf-8"))
    assert not (STAGE/"render_receipt.json").exists()
    assert all(sha(ROOT/n)==p for n,p in protocol["bindings"].items())
    import psutil
    peak=0
    record=dict(status="running",invocations=1,programs_completed=0,
                new_force_calls=0,new_tangent_calls=0,new_solver_calls=0,new_HP_calls=0,
                new_action_consumer_calls=0,new_geometry_calls=0,
                call_count_basis="Saved-only plotting source paths; no mechanics hooks monitored")

    def checkpoint():
        nonlocal peak
        memory=psutil.Process().memory_info()
        peak=max(peak,memory.rss,getattr(memory,"peak_wset",memory.rss))
        assert perf_counter()-STARTED<=120 and peak<=8*1024**3
        assert not (STAGE/"stop_requested.txt").exists()

    try:
        for argv in protocol["render_programs"]:
            checkpoint()
            sys.argv=[str(ROOT/argv[0])]+[str(ROOT/a) if a.startswith(("lf_data_preparation/","functional_views/")) else a for a in argv[1:]]
            runpy.run_path(sys.argv[0],run_name="__main__")
            record["programs_completed"]+=1
            checkpoint()
        unchanged=all(sha(ROOT/n)==p for n,p in protocol["bindings"].items())
        assert unchanged and record["programs_completed"]==1
        checkpoint()
        record.update(status="pass",all_bindings_unchanged=True)
    except BaseException as error:
        record.update(status="not_pass",error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        with (STAGE/"render_receipt.json").open("x",encoding="utf-8") as stream:
            json.dump(record,stream,indent=2)
            stream.write("\n")
    print(json.dumps(record))


if __name__=="__main__":
    main()
