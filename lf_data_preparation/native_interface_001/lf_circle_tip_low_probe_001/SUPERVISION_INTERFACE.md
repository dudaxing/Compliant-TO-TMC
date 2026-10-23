# L-CTIPLOW1 supervision interface (candidate, not run)

Written 2026-10-23 following the user's explicit L-CTIPLOW1 authorization. This is a source/static interface record. No wrapper, supervisor scenario, scientific calculation, test or evidence archive has been executed to create it.

## Unique command

From `D:/hlo1_001`, with the complete protocol frozen and the independent static reviews passed:

```powershell
& 'D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe' -X utf8 -B 'D:/hlo1_001/outer_low1.py'
```

The outer accepts no arguments. It exclusively writes `root_outer_start.json` before the original launch and rejects any previous execution marker/run/outer receipt/archive. Creating this marker is an execution action; static preparation must not create it. It records entry to the outer bootstrap, not an assertion that any scientific API was called.

`outer_low1.py` launches exactly:

```text
<protocol python> -X utf8 -B D:/hlo1_001/launch_low1.py --protocol D:/hlo1_001/protocol.json
```

The launcher creates `run_001` exclusively, validates the frozen protocol through the runner, and launches one `run_low1.py` helper without arguments. Only that helper schedules the separately supervised parent child, probe child, then pure viewer. The main runner owns their CLI definitions and readiness gates. The launcher expects `helper_receipt.json` status `ready_for_visual_check` and integer `parent_process_launches`, `probe_process_launches`, `viewer_process_launches`.

## Clocks and reserve

`LOW1_ROOT_START_MONOTONIC` is the original outer start, set before the remaining outer imports and preflight. All later phases share that value. `LOW1_HELPER_DEADLINE` is the absolute original start plus 8900 seconds, not a new local window.

| Scope | Ceiling or reserved edge from original start |
| --- | ---: |
| Parent controller | 3600 seconds, unchanged at the API call |
| Probe controller | 3600 seconds, unchanged at the API call |
| Pure shared viewer | 900 seconds |
| Parent/probe separately supervised process | 3800 seconds each (controller plus import/persistence allowance) |
| Viewer supervised process | 965 seconds (900 display plus ordinary startup/persistence allowance) |
| Helper ordinary content deadline | 8900 seconds |
| Helper SUP2 process deadline | 8910 seconds |
| Helper SUP2 cleanup | At most five further seconds |
| Byte seal may start only before | 8980 seconds |
| Byte seal per-member/after-close/hash/manifest checks | Before 8990 seconds |
| Original shared helper/seal ceiling | 9000 seconds |
| Outer SUP2 process deadline | 9050 seconds |
| Outer SUP2 cleanup then final ordinary receipt allowance | Five plus five seconds, within 9060 seconds |

The main helper must test sufficient remaining time before the first scientific child (at least 8600 seconds), the probe child (at least 4800 seconds), and the viewer (at least 975 seconds). Each scientific child must retain at least its full 3600-second controller plus five seconds before entering its API; it must stop rather than lower the requested controller limit. These phase-entry checks are the runner's frozen implementation obligations, not extra scientific gates.

If the launcher itself exceptionally fails to return, outer supervision may continue solely to its 9060-second ceiling for same-instance cleanup and ordinary failure receipts. This does not open a new scientific or sealing window. A seal is skipped when the original 9000-second window no longer has its fixed margin.

## Required protocol fields

- `schema_version`: `hf-ctiplow1-protocol-1`.
- `status`: `frozen_ready_for_unique_authorized_launch`.
- `runtime_base`: `D:/hlo1_001`; `run_directory`: its `run_001`.
- `python_executable`: the pinned interpreter used in the command above.
- `parent_controller_seconds=3600`, `probe_controller_seconds=3600`, `viewer_seconds=900`, `helper_seconds=9000`, `outer_seconds=9060`.
- `parent_process_cap_seconds=3800`, `probe_process_cap_seconds=3800`, `viewer_process_cap_seconds=965`.
- `helper_content_deadline_offset_seconds=8900`, `helper_process_deadline_offset_seconds=8910`, `outer_process_deadline_offset_seconds=9050`.
- `memory_limit_bytes=64*1024**3`, `viewer_memory_limit_bytes=8*1024**3`.
- `cpu_thread_environment`: exactly OMP, OPENBLAS, MKL and NUMEXPR `_NUM_THREADS`, each string `16`.
- `bindings`: `{path,bytes,sha256}` rows including every wrapper and the unchanged local SUP2. The outer verifies its own file, launcher and supervisor before importing SUP2; launcher calls the runner's full frozen dependency validation.
- Remaining task, geometry, source, observer and comparison keys are defined by the runner/viewer and freeze record.

## Cleanup and byte archive

All three supervision layers use the unchanged SUP2 `run_owned`, accepting success only with normal exit zero, `cleanup_verified`, proof `pass`, and `job_handle_closed`. The copied SUP2 is exactly 43559 bytes, SHA256 `b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499`.

After outer-owned cleanup is proven, one `execution_evidence.zip` may capture actual BASE file bytes, including partial outputs after a terminal failure. It excludes only the archive, its manifest and its final seal receipt. It never decodes scientific arrays or repairs output. Each member identity and the whole archive identity are recorded. Any error ends this one attempt; files already written remain. A failed cleanup proof or exhausted original sealing margin skips the seal. No later repair seal or window restart is permitted.

No production source installation, HP, tests, API association, scientific retry, external force or deletion is performed by these wrappers.
