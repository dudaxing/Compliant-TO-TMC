# L-CTIPLOW1 runner interface (static candidate; not executed)

`run_low1.py` exports `BASE`, `RUN`, `PROTOCOL`, `finite_environment`, `phase_pass`, `read_json`, `validate_protocol`, and `write_new` for the launcher. No-argument mode is the helper. `--parent-child` and `--probe-child` are the sole scientific modes. Only those children import HF. The launcher creates the fresh `run_001` directory before starting the helper.

Protocol schema `hf-ctiplow1-protocol-1`, status `frozen_ready_for_unique_authorized_launch`:

- `runtime_base`: `D:/hlo1_001`; `run_directory`: `D:/hlo1_001/run_001`.
- `candidate_source`, `python_executable`, `observer_file`, `observer_definition_path`, and `bindings` (each path/bytes/sha256; NPZ entries prohibited there).
- `geometry_file`: `BASE/geometry/geometry.json`; `task_file`: `BASE/task.json`; `high_table_file`: `BASE/high_state_table.json`. These are frozen ordinary-byte bindings before launch.
- `geometry_files`: one original NPZ byte identity with `source`, `relative_path="geometry.npz"`, `bytes`, `sha256`. The helper alone writes `BASE/geometry/geometry.npz` with `xb` in its original resource window. It never decodes it.
- `parent_targets_mm=[0,.25,.5]`, `held_input_mean_mm=.5`, `body_q_targets_mm=[0,.025]`.
- `parent_settings`: exact original tolerance1e-9, constraint_tolerance1e-10, displacement_scale_floor1e-6, force_scale_floor_factor1e-8, max_checks25, armijo_c1e-4, max_backtracks12, max_bisections4, minimum_increment.00625; clock3600.
- `parent_controller_seconds=3600`, `probe_controller_seconds=3600`, each `*_process_cap_seconds=3800`; `viewer_seconds=900`, `viewer_process_cap_seconds=965`; `helper_seconds=9000`, `outer_seconds=9060`.
- `helper_content_deadline_offset_seconds=8900`, `helper_process_deadline_offset_seconds=8910`, `outer_process_deadline_offset_seconds=9050`.
- `memory_limit_bytes=64*1024**3`, `viewer_memory_limit_bytes=8*1024**3`; the four `cpu_thread_environment` values are strings `16` for OMP/OPENBLAS/MKL/NUMEXPR `_NUM_THREADS`.

The helper receives `LOW1_HELPER_DEADLINE` from the root-start clock. Parent and probe receive separate `LOW1_PHASE_DEADLINE`. Entry reserves are parent8600/probe4800/viewer975 seconds. Each API call requires its complete3600-second controller plus5-second cleanup reserve still available after import/admission preparation. External child cap3800 covers import/persistence within the shared window; it grants no extra solver clock. Each original SUP2 cleanup is checked through same-instance proof and closed job handle.

Parent API is called once with `DisplacementSettings(**parent_settings)` and explicit `mechanical/chunk256/port_projection`; individual API clock/minincrement options are omitted. An observation wrapper calls its original `solve_native_mean` exactly once and returns the original result unchanged. Its callback only persists ordinary progress. At return, the same original loading acceptance observation reads fresh cached J and fixed lift/fluctuation sums, using `math.fsum`, for the original8e-11 fixed gate. It does not decode any NPZ or call force/tangent/solve. The module reference is restored in `finally`. Helper admission requires those measured gates and one original solver call, as well as the complete new zero-start original path. All accepted parent states are retained.

Only complete parent success enters the probe. Its selected index is `len(parent.states)-1` after full-path validation, never hard-coded2. Probe uses fresh q0 with unchanged split field hashes and signed R, one Newton check, then only q.025; original internal backtracking/bisection remains. No old high state, force or matrix is substituted.

Viewer is invoked once as:

`render_low1.py --protocol BASE/protocol.json --result run_001/probe_low/result.json --parent run_001/parent_fixed/result.json --output run_001/view`

Expected ordinary `renderer_receipt.json` keys: status `rendered_pending_visual_check`; `accepted_states=N`; `archives_decoded=N`; `fields_decoded=2*N<=34`; `new_png_count=4`; `gif_frame_count=N`; `scientific_calls=0`. New fields are only J/Hu. `LOW1_VIEWER_DEADLINE` is the minimum of viewer-launch monotonic time+900 and the original shared helper deadline. The declared display clock stays900 seconds independently of the965-second viewer process cap.

Terminal helper receipt is `run_001/helper_receipt.json`; success status `ready_for_visual_check`, with `parent_process_launches=probe_process_launches=viewer_process_launches=1`. Every terminal failure blocks downstream phases, retains whatever actual API persistence/progress exists, and exits nonzero. Only the root outer bootstrap owns the one original-window byte archive. This interface document is not an execution result.
