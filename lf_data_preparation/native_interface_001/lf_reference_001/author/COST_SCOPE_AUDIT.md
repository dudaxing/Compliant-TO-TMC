# L-REF1 cost and inherited-method scope audit

Source/ordinary-record audit only; no authorization or scientific execution. Helper 900 seconds, outer 960 seconds and sampled 8 GiB are a reasonable proposed fresh window for two saved states / four HP80/120 calls, two original math/body checks and one pure observation plot. This is supported by three comparable closed runs, not by leftover time or a guarantee for the new LF topology.

| Existing closed reference | States / HP calls | Outer seconds | Child wall seconds | Peak tree RSS bytes |
| --- | --- | --- | --- | --- |
| M-AREF1 | 2 / 4 | 193.35030270001153 | 192.32251390002784 | 1278435328 |
| M-EREF1 | 1 / 2 | 99.37017110001761 | 98.64665289997356 | 1277128704 |
| M-PREF1 | 2 / 4 | 178.64134569995804 | 177.04476130002877 | 1280548864 |

Their selected state summaries cover 13440 elements and 27378 DOFs. M-PREF1 recorded 4/4 HP, 2 math states, 2 body states, one plot and 161513 checks; its final seal elapsed was 175.54304769996088 seconds. The new LF mesh size is comparable, but geometry/masks, saved state deformation, sparse matrix pattern, system load, validation, imports and sealing may change cost. A fresh earliest helper/outer clock, RSS sampling, first-error stop and actual child wait remain required. Budget exhaustion preserves actual partial output and forbids extra HP calls, repair/retry or late scientific hashing.

`core_audit_mechanical.py:276–300` can be inherited byte-for-byte as a method. Pass the real global original index 13 or 16 to run_state; its special undeformed/zero-multiplier test applies only to index zero. Relabeling the first selected nonzero state as zero is incompatible. The saved lift must still satisfy the original zero-lift representation assertion. The old general loader/CLI is not portable unchanged: old geometry/fixed-node identities are specific, and its CLI has a 180-second ceiling. Reuse the M-PREF1 thin actual-source loader and explicitly bound 900-second supervisor; do not invoke or alter the old mathematics CLI.

The 15 original gate values remain exact (recorded in JSON). Lines 322–335 validate every saved unsymmetrized CSC coefficient against local cached tensors; lines 338–434 compare actions only along the actual normalized input PORT direction with deltaR=0, including augmented force and mean-constraint KKT checks. This is not exhaustive HP testing of all matrix columns. Lines 355–360 make exactly one 80 and one 120 call per selected state.

`audit_native_workpiece_cycle.py:269–320` can also be inherited byte-for-byte as workpiece_checks. It projects the same HP force references onto actual body DOFs, keeps total/material/regularization denominators and limits, verifies disjoint holding partitions, signed weak forces and the dummy undeformed body field. The thin loader must derive actual model/body/groups/ports from the new source snapshot; old hardcoded geometry/node identities must not be reused. No fresh production F/T, equilibrium solve or model construction is required.

The proposed reference scope is only loading index13/d1.20 and unloading index16/d1.05 from the new successful LF result. Old reference passes do not transfer. Full25 reference, public full-result reference matching, all-column HP, pressure, effective clamp/release, stability and HF5 remain unqualified. M-PREF1 truthfully records JAX loaded while wrapper AD/JIT calls are zero; do not claim that importing the inherited modules never loads JAX.

Only the listed ordinary JSON/PY files and their raw identities were read. No NPZ, gzip, CSV, media bytes/header/hash, HF imports, tests, HP, solver, plot or new timing run was used. This report independently audits prior reference cost/method scope and does not certify the reviewer's own future source publisher.
