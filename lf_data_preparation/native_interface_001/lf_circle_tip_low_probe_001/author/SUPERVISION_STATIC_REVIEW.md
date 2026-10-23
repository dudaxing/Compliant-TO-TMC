# L-CTIPLOW1 监督包装独立静审

2026-10-23。**PASS，12/12项，无阻断项；尚未执行。**

审阅者 `/root/low_viewer`。本报告审查launcher／outer／原SUP2接口及runner相关预算、CLI、准入和终止分支；viewer作者独立性限制明确：viewer本身不在本报告独立结论范围，交root与runner作者另审。

冻结协议：`16609` bytes，SHA256 `e4148293f4bbb1d800d3dec73b8bee3afa3fe8ae1b72c9d9fe98463f5b4ba1d8`；67份绑定普通／源码字节逐一一致，status=`frozen_ready_for_unique_authorized_launch`。审查时run_001和root_outer_start均不存在。

|项|结论|说明|
|---|---|---|
|S01 Authorized frozen resource and task identity|PASS|Frozen protocol status/schema, exact two3600 controllers, parent[0,.25,.5], held.5, q[0,.025], original9000/9060,67 ordinary/executable bindings all pass finite identity checks. No execution marker or run exists.|
|S02 Supervisor unchanged and syntax finite|PASS|Copied SUP243559 bytes and required SHA match. AST parsing only for launch, outer, runner and SUP2 succeeds; no module imported or code executed.|
|S03 One outer attempt and exclusive marker|PASS|outer accepts no alternate arguments; rejects prior marker/run/log/archive/receipt and writes root_outer_start.json with exclusive x before launch. Existing attempt is never deleted, reset or reopened.|
|S04 Outer original start and maximum window|PASS|STARTED is set before remaining outer imports/preflight. Outer run_owned receives original STARTED+9050 and seconds9050, followed by SUP2 shared cleanup<=5 and ordinary-receipt allowance5 within9060. No new scientific window is opened during cleanup.|
|S05 Launcher and helper CLI compatibility|PASS|Outer invokes launch_low1.py --protocol exact BASE/protocol.json; launcher requires exactly that argument. Launcher creates RUN exclusively and invokes noargument run_low1 helper. Exported BASE/RUN/PROTOCOL/finite_environment/phase_pass/read_json/validate_protocol/write_new names exist. Helper status and launch-count names align.|
|S06 Helper content and process ceilings|PASS|LOW1_HELPER_DEADLINE is original rootstart+8900. Helper supervisor ends by rootstart+8910, with original SUP2 five-second cleanup; launcher gates original9000, never extends it. Timing minima are absolute monotonic values inherited through environments.|
|S07 Full phase opportunities and original controller clocks|PASS|Runner requires8600 before parent,4800 before probe and975 before viewer. Parent/probe process caps3800 preserve stage reserves; each child checks full controller3600+5 after imports. Viewer own900 clock is shared with launch+900 env and original helper deadline; process cap965 grants no scientific clock. A missed reserve stops, not compresses/retries.|
|S08 Sequential first-terminal-error stop|PASS|One parent child then only validated complete parent one probe child, then only validated complete probe one viewer. Any process, cleanup, API uniqueness, production gate or receipt failure raises out of helper and suppresses downstream work. Original internal solver backtracking/bisection is unaffected.|
|S09 Same-instance cleanup and signal/handle proof|PASS|Every phase_pass requires normal_exit/0, cleanup_verified, proof.pass and job_handle_closed. Original SUP2 suspends before Job assignment/resume, tracks creation-time identities/handles, terminates Job in finally, drains complete membership and requires root wait/handle release. No PID-absence substitution or cleanup repair is introduced.|
|S10 Memory, CPU and viewer interface|PASS|Four thread variables exactly16; JAX CPU mode. Outer/helper/science sampled64GiB and viewer8GiB. Viewer CLI protocol/result/parent/output names match candidate; expected receipt four PNG, actual N GIF, N archives,2N<=34 fields and scientific_calls0 matches. No old-array/media decode occurs in these supervisory wrappers.|
|S11 One original-window complete or partial byte seal|PASS|Only outer owns archive. Cleanup proof is mandatory. Seal starts only before original8980; per-member, after-close, archive-hash and manifest checks use8990; successful completion checked before9000. Zip opens x once and captures bytes only; no NPZ decode. Failure retains written partial archive and records failed_once_no_retry; cleanup/window exhaustion produces explicit skipped status. Partial scientific outputs after terminal error may be sealed without scientific rerun.|
|S12 Receipts, scope and qualifications|PASS|Original journals/receipts preserve reasons, exit codes, actual partial observations and byte hashes. No wrapper runs tests, HP, installer, production edits, external retry/force/delete/rollback. Source static pass is not numerical, cleanup-runtime or image qualification; actual run must establish those separately.|

## 源字节

|文件|bytes|SHA256|
|---|---:|---|
|launch_low1.py|4234|`023305996fc7be9e43a305da48e72496a06f0151af3e9e18634cb81dbe607ca5`|
|outer_low1.py|7415|`01c62259f50281ec9aca96cd600c1b5ace4650aadbcf1bc081325762331c5faf`|
|run_low1.py|32522|`4f1d3642adf07ede1b482a373a336226e883e8a8c157ad62be5f15cce96bea6b`|
|windows_owned_process_sup2.py|43559|`b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499`|
|SUPERVISION_INTERFACE.md|5705|`2d9fb65586d57541bdcd4679bee2aebb6f6f12e6955ebf6846e232b7da7f88df`|
|RUNNER_INTERFACE.md|4744|`8a5f8b5c05ac45e3a7d9027cff93fcf5ca9e047ed714fcf89d1c87ee95dc9303`|

仅标准库普通字节读取、JSON、AST静核；没有调用包装、SUP2场景、科学导入、新测试、HP、NPZ解码或媒体内容读取。该结论不冒称真实数值、清理、绘图、封存已经成功；必须由后续唯一真实运行的原始回执建立。
