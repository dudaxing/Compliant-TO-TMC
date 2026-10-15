# L-USE1 incremental delivery source

This external publisher has not been invoked. Source writing and AST parsing are preparation evidence, not execution, publication, or restoration evidence.

The fixed parent is main `c9ca9a23464bed01aff3ee7a6a0410a09c933d9e`. Its ordinary repository manifest is inherited exactly: SHA256 `6e6cd66da5fea65b339ea91993b8d66bc8ce6942b379796a9732407d043757bb`, 20672 entries, 11310476880 bytes, science version 0.5.0, science baseline `b1334bb6a83ba9a0efab7bdba7bd39722146f024`.

All new paths must belong to `lf_data_preparation/native_interface_001/lf_saved_consumer_001/`. The only old content changes permitted are `docs/CURRENT_STATUS.md` and `docs/RESUME_DEVELOPMENT.md`. Each must retain its entire parent raw content contiguously once, with exact offsets and hashes in `author/execution_documentation_receipt.json`. No `hf_repo` change is allowed.

The publisher accepts the actual `use_launch.json` and helper `run_001/execution_receipt.json`, actual direct-human authorization, the closed output seal, and an independent final review mapping every delivery delta path except the review JSON itself. Runtime fields are the agreed L-USE1 schema: helper 120 seconds, outer 180 seconds, sampled 1 GiB, exactly one consumption, exactly three old ordinary JSON reads, 25 rows, selected indices 13 and 16, and two matched reference rows. It does not execute the consumer, tests, HF APIs, mechanics, HP, or plotting.

Existing manifest entries are inherited without reopening their content. Five media paths are checked against inherited identities and file size only. No science or media bytes, headers, hashes, or decoded pixels are read by the publisher. Delta hashes are restricted to JSON, Python, Markdown, text, and log files.

From the external directory, after actual execution, records, independent final review, and exact staging:

```text
python -X utf8 -B publisher_execution.py preview --repo FORMAL_ROOT
python -X utf8 -B publisher_execution.py finalize --repo FORMAL_ROOT
```

Preview writes one external preview receipt and does not change the manifest. Finalize writes the incremental manifest and one external delta receipt. The manifest must be staged afterward; ordinary Git whitespace checking, a single normal main commit, push, and fast-forward restoration are performed separately by the root agent.

After actual commit/push/restoration, `verify --repo FORMAL_ROOT --restore RESTORE_ROOT` checks exact main/origin identity, clean source and restore, remote main, the exact commit delta, all new ordinary bytes in both trees, old inherited manifest entries, closed result/approval records, and five media sizes. It writes one external publication receipt. It does not update old source evidence or restart the consumer. All three modes are one-write operations for their own external receipt; they do not delete, roll back, force, or repair outputs.

Actual result, exact file counts, timings, resource observations, and publication commit are deliberately not predicted here.
