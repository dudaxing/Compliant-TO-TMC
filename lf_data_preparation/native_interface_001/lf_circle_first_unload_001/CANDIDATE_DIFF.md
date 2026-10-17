# L-CUNLOAD1 candidate changes

BASE: `c78658322587499e901e654516aed62b45aa022d`.

Only candidate source: `candidate/native_resume.py` (SHA256 `68e3122950766f9cecb48a02a0f52a6d5f2efbfc466432bccc2cd48c77e2b798`). Formal source, API, CLI, response, controller and mechanics bytes are unchanged by this preparation.

- At line 58, the existing explicit extension validator accepts one additional transition: a completed terminal nonzero `load_only` source may become `ordered_cycle` by appending exactly one finite, non-boolean, nonnegative target strictly below its unchanged loading peak. The input peak remains the source peak.
- The complete canonical old target prefix remains exact. For this load-only source, only the existing four informational fields (`task_id`, `purpose`, `parameter_origin`, `description`) may vary; normalization also restores the source path kind for identity comparison. All other task, physical, source and child-suffix guards remain in place.
- A descent may equal an earlier nonadjacent loading target. Same-kind `load_only`, same-kind `ordered_cycle`, and default non-extension behavior retain their original validation branches.
- At line 257, only a cross-kind extension adds `continuation.task_transition`: `source_path_kind`, `extended_path_kind`, `first_unload`, `loading_peak_mm`, `first_unload_target_mm`. `continuation_mode` remains `explicit_task_extension`; existing whole-path and qualification flags are unchanged.
- The preserved peak is the freshly validated child anchor, not a replay of the original loading prefix. Existing response scope wording is retained as agreed.

Validation in this preparation: standard-library AST parse and source-only diff. No candidate import, installation, tests, F/T/HP, equilibrium solve or scientific payload/media read. Installation and the one finite compatibility run belong to the root-controlled authorized helper.
