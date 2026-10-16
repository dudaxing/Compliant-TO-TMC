# L-BFWD1 finite actual read-only review

Status: **pass_finite_actual_readonly_review**. No substantive execution or scientific blocker was found.

Both independent fine/wave cases completed zero-start load-only [0, 0.25, 0.5] mm with three accepted states each; each recorded 27/27 force calls, 15/15 tangent calls and one solver invocation. The batch, original API and cache gates passed. Outer/helper times were 1744.4946828/1743.7285967 s. Shared display completed in 24.8220262 s.

Across six saved rows the largest relative residual is 1.4914221396596871e-12 (limit 1e-9), absolute average constraint residual 6.938893903907228e-18 mm (within each original bound), and relative global balance 3.3095795326523335e-15 (limit 1e-6). Original cached maximum fixed split sum is zero (limit 8e-11 mm); no arrays were reopened to recalculate it. Saved numerator/scale and constraint-bound scalar associations, accepted index/SHA/order, body component projections and convergence raw-history associations were checked.

Fine endpoint: R=0.07624835727107876 N; q_out=0.4792732955273436 mm; solid/medium minimum J=0.9891806659477834/0.5177396181452025; bottom finite-face ray=0.5210256544012282 mm; lower-body total Fy=0.00034791873300466907 N. Wave endpoint: R=0.08593082815865576 N; q_out=0.4811512138551336 mm; solid/medium minimum J=0.9879518030952109/0.5164004668740174; bottom ray=0.5191397665813575 mm; lower-body total Fy=0.0003512425565784398 N. These are saved observations, not new geometry or mechanics evaluations.

The original 82-file/113621059-byte whole-run seal and 38-file display subset agree; all current file sizes and run membership match. Scientific NPZ/CSV/media and raw geometry/nodal payloads were not opened or rehashed. Parent's ordinary pixel-QA record is linked; this reviewer did not inspect pixels. Source/input identities and explicit settings remain associated with the original protocol.

The earlier read-only assertion that raw manifest options must equal normalized batch options was a reviewer assumption: the API adds neutral defaults while retaining the full explicit 1800 s settings. It did not constitute a scientific failure or retry. No original trace or result was changed.

No fresh HP, full-column tangent, energy, contact/pressure/grip, unloading/release, HF5, ranking or public-replay qualification is granted. Default API views/reference remain not_provided; the research layer provides saved-display associations. The loading endpoint must not be described as a return. Full identities, scope and saved endpoint decompositions are in ACTUAL_REVIEW.json.
