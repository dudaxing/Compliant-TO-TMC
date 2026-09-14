# Vendored frozen AuTO source (E005)

This directory holds a **byte-exact copy** of the one upstream file the `dmftd` kernel executes
at runtime, together with the upstream license, so that a plain `git clone` (or a source ZIP)
runs the optimizer without initializing the `third_party/AuTO` submodule.

| Item | Value |
| --- | --- |
| Upstream repository | https://github.com/UW-ERSL/AuTO.git |
| Upstream commit | `ba3c0c5dfc9acb7daff802aaf0bb41105296ad98` (2023-07-19), the same commit the submodule and the M0–M3 contracts pin |
| File | `models/utilfuncs.py`, 22,901 bytes, CRLF line endings preserved (`.gitattributes`: `third_party/AuTO_frozen/** -text`) |
| SHA-256 | `0aa90e8479e545ffab7e5022ac30433fbd64e2207b4fe57634444ff2e36b69c2` (identical to `FROZEN_UTILFUNCS_SHA256` in `src/dmftd/mma_adapter.py` and to the M3 contract) |
| Last upstream change of the file | commit `2f017801af71f7c9183374c1d613b03c23ad44a6` (2022-06-07) |
| License | GNU General Public License v3.0, `LICENSE` in this directory (byte copy of the upstream file, SHA-256 `230184f60bae2feaf244f10a8bac053c8ff33a183bcc365b4d8b876d2b7f4809`) |
| Modifications | none |
| Copied on | 2026-09-13 |

`dmftd.mma_adapter.load_frozen_utilfuncs` looks here first and falls back to the submodule path;
both are hash-checked against the value above before the bytes are compiled.  The submodule is
still needed only to replay the M0 reference generation (`scripts/run_auto_reference.py`), which
executes the upstream notebook.

Distributing this repository distributes GPL-3.0 code; see `THIRD_PARTY_NOTICES.md` for the
consequences for the repository license, which the owner has not chosen yet.
