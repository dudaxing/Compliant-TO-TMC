"""Run the raw coordinate-selected viewer once within one whole-helper window."""
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import argparse
import json
import runpy
import sys

STARTED = perf_counter()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    for name in ("repo", "protocol", "output", "stop-file"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--time-limit", type=float, required=True)
    args, _ = parser.parse_known_args()
    root, output = args.repo.resolve().parent, args.output.resolve()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    assert args.time_limit == protocol["phases"]["view"]["helper_seconds"] == 180
    import psutil
    process = psutil.Process()
    peak = 0
    saved, failure = {}, None

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, "peak_wset", memory.rss))
        assert perf_counter() - STARTED <= 180 and peak <= 8 * 1024**3, "Saved-view helper time/RSS budget"
        assert not args.stop_file.exists(), "Saved-view supervisor requested stop"

    try:
        checkpoint()
        original_argv = sys.argv[:]
        viewer = Path(__file__).with_name("saved_right_margin_views.py")
        try:
            sys.argv = [str(viewer), *original_argv[1:]]
            runpy.run_path(str(viewer), run_name="__main__")
        finally:
            sys.argv = original_argv
        saved = json.loads((output / "view.json").read_text(encoding="utf-8"))
        assert saved["status"] == "pass" and saved["new_F_T_model_solver_HP_calls"] == 0
        expected = protocol["expected_observations_each"]
        assert all(saved[key] == expected for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed"))
        checkpoint()
        assert all(sha256((root / name).read_bytes()).hexdigest() == pin for name, pin in protocol["bindings"].items())
        checkpoint()
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        if output.exists():
            outputs = {p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest()
                for p in output.rglob("*") if p.is_file()}
            late_error = None
            previous_failure = failure
            try:
                checkpoint()
            except Exception as error:
                late_error = error
                failure = failure or repr(error)
            report = dict(schema_version="right-margin-saved-view-phase-1.0", status="pass" if failure is None else "failed", failure=failure,
                mode=protocol["mode"], original_view_sha256=sha256((output / "view.json").read_bytes()).hexdigest() if (output / "view.json").exists() else None,
                original_observation_counts={key: saved.get(key) for key in ("geometry_started", "geometry_completed", "nodal_started", "nodal_completed")},
                new_geometry_nodal_F_T_model_solver_HP_calls_outside_raw_viewer=0,
                elapsed_seconds=perf_counter() - STARTED, sampled_peak_helper_RSS_bytes=peak,
                final_resource_check_passed=late_error is None, final_resource_error=repr(late_error) if late_error else None,
                scope="Raw761a9f saved viewer only; no new mechanics or physical qualification.",
                outputs=outputs)
            with (output / "phase_view.json").open("x", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, ensure_ascii=False, allow_nan=False); handle.write("\n")
            if late_error is not None and previous_failure is None:
                raise late_error


if __name__ == "__main__":
    main()
