# x72/E1 fixed half-square tip-alignment candidate

Author/static-only candidate for `shift_square_tip_align_001`, alias `gripper_coarse_square_x72_tip`, baseline `b31003303960231c5cc6bf95c9fd6fe751f85da8`. No preparation, model construction, response, solve, HP, geometry observation or rendering has been executed by these author files.

The square has side16 mm and centre(72,40) mm. Its actual half-model box is [64,80]×[32,40] mm. The right face lies on the original native domain x80: right-side third-medium margin is **zero**. This is a new boundary-touch physical task, with no surrounding-medium or contact qualification inherited from x71. The original LF four masks, native1 mm grid, E1 MPa/nu.3/t20 mm, gamma=alpha=1e-6/Lr80 mm, +x weighted-mean input and free +y output remain unchanged. Kinematic rigid-body ux/uy are fixed; there is no additional right-edge constraint. Mirror depiction is separate from actual half-model mechanics.

The original eleven ordered targets are [0,.5,1,1.5,1.75,1.8,1.75,1.5,1,.5,0] mm. All controller constants and gates retain the old010 values, including minimum_increment=.00625 mm. Production starts from zero; it cannot reuse predecessor accepted states. The original producer is an exact251-line byte copy (`96bf1b48eebe22b1132f6736b17de2f4269d656442c8308c2822caa0ec0387ae`), including first F/T range-input observation, bare re-raise, hook restoration, cached-only saving and actual counters.

`qualified_prerequisites` separately binds complete pose002 and soft001 result/model/task, launch/protocol and fresh-reference summary/lifecycle files. `stage` is the control directory and `run_stage` is its run_001 directory. These are identity, material-choice and cost evidence, not x72 state qualification. Constructor preparation compares all27 stored fields both against old010/x70 and qualified pose002/x71: all21 intrinsic fields must match raw dtype/shape/bytes; exactly6 overlay fields may differ. The soft predecessor's material arrays are not used as the E1 construction baseline.

Pure arithmetic on saved native indices gives128 body cells,153 nodes,306 ux/uy DOFs,17 background uy overlaps,376 merged fixed and6266 free DOFs. Nine body nodes are on x80; among their original no-body DOFs only topcorner uy6641 is fixed. Every selected cell remains source passive_void and body nodes share no mechanism/support/port nodes. These are static index facts, not an executed constructor receipt. `static_native_counts.json` preserves source SHA and the exact scope.

Source freeze is old010's68 paths plus the two new preparation/production paths =70 unique basenames. Every historical capsule remains byte-exact. The sole old-source transition is split_numpy_tangent from oldfe365 to currentv5/547143, admitted by the existing bounded T44 repair protocol/launch/receipt. It does not transfer old accepted-state qualification to this new task. All other old68 live source bytes, including D5 force, B52 action consumer and native_mean/controller, are unchanged.

Preparation is one constructor/writer call under120 helper /150 outer seconds and sampled8 GiB. Production is one solver invocation under1800 helper/API /1860 outer seconds and sampled8 GiB, chosen using complete x71/E1 cost1413.35s and x71/E.5 cost1193.07s; unknown near-tip compression may still fail. The original F3 launcher samples the child tree and writes control/stop_requested.txt; both entrypoints check that and run_001/stop_requested.txt. These are cooperative limits, with no OS hard cap or forced termination. First formal failure closes the card; no repair, retry, extension or prefix reuse on it. A future reference card must read the actual complete new path/trace and independently check every accepted index with fresh80/120; its resource contract is separately authored.

From the formal Git root, after independent static review only:

```powershell
python -B D:/hf-workpiece-align-author-20261005/pose72_candidate/build_pose_card.py --repo . --mode prepare
python -B lf_data_preparation/native_workpiece_001/shift_square_tip_align_001/launch_pose.py prepare --protocol lf_data_preparation/native_workpiece_001/shift_square_tip_align_001/preparation_protocol.json
python -B D:/hf-workpiece-align-author-20261005/pose72_candidate/build_pose_card.py --repo . --mode production
python -B lf_data_preparation/native_workpiece_001/shift_square_tip_align_001/launch_pose.py production --protocol lf_data_preparation/native_workpiece_001/shift_square_tip_align_001/production_protocol.json
```

The second freezer command is admissible only after the first preparation has a real terminal pass. No command here has been executed during authoring. Relative roles in protocols and inventory refer to the complete Git root; moving the flat sources capsule alone is insufficient. No pressure, exact hard-contact, successful clamp, mesh-convergence or H2/H3 conclusion is granted by this candidate.
