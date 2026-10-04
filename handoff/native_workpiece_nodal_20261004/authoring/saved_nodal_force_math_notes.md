# Saved workpiece nodal-force proposal (read-only)

Observed Git baseline: 3f0418490b3994ad0ef7c2881bc005d237cff8e1.
No source edits, mechanics imports, force/tangent/HP/solver, geometry evaluation or rendering were performed.

The smallest useful entry is `observe_workpiece_nodal_forces(model, metadata, forces)` for one already-saved, fixed lower-half square. The file loader owns result/state/archive SHA identity and accepted index/leg. The function takes plain saved arrays/dictionaries, constructs no Project, and evaluates no material, tangent, assembly, overlap or distance. Keep this separate from native_mean so old cached result files remain unchanged. Proposed names below are interface suggestions, not an assertion about the author's eventual schema.

## Force and units

For every sorted workpiece node n, store the three two-component vectors
`on_body[component][n] = -global_component_force[2*n:2*n+2]` for total/material/regularization. They have units N, with x/y signed as the model coordinates. These are finite-element weak-form nodal forces on the fixed lower body; they are not traction or pressure, and are not divided by edge length, thickness or nodal tributary area. The body remains the original-medium kinematic overlay; material versus Hu components are force-term components, not mechanism-versus-medium material classes.

`support_reaction` is the external holding force ON the model. On the workpiece DOFs it must be the opposite of the on-body total when input/spring forces on these DOFs are zero, as required by the current no-overlap model contract. Do not apply its sign to the material/Hu arrays a second time. Retain negative and tiny values; no abs, threshold clipping or manufactured zero. Require all body ux/uy fixed and no input/output DOF overlap; original source solid/material arrays stay untouched.

Store node ID, reference x/y in mm, on-body vectors, holding total, and membership flags. Fixed body reference coordinates are sufficient for the spatial plot; a path loader can bind and check zero saved body displacement. If a deformed body is later allowed, this function's initial scope must be revised explicitly.

## Topology and node ownership

Use the existing BL/BR/TR/TL incidence rule (`exposed_q1_edges`) once on the workpiece cell IDs: closed exposed edges include the y=40 cut; physical exposed edges remove only edges with BOTH reference endpoints on the mirror line. Do not drop every node with y=40: the upper left/right endpoints also belong to physical side edges.

For the current axis-aligned square, retain bottom/left/right/cut membership flags, with more than one flag allowed at a corner. Do not assign an ambiguous nodal force to one face or split it 50/50. A minimal FOUR-way disjoint accounting partition is:

1. Physical face-interior nodes (one physical face, no cut membership).
2. Physical junction nodes (bottom corners and side/cut endpoints), with their exact multi-face flags retained.
3. Cut-only nodes (on the mirror cut, not incident to a physical exposed edge).
4. Body interior nodes (not on any closed exposed edge).

All groups must be disjoint and their union must equal ALL workpiece nodes. Keep the closed/physical/cut edge arrays and all body rows, including interior and cut-only forces. Excluding the cut from a physical drawing must not silently exclude its nodes from the complete body-force accounting. No cut-edge force is labelled contact; a side/cut endpoint remains a nodal contribution with shared topology, not a face-resolved traction.

The existing region-ray module deliberately covers only bottom and left diagnostics. A nodal force map must still include the right physical side and all corners: the small force there cannot be assumed zero from geometry. Do not call SAT or face-ray routines to classify load/contact, or use their nearest corner to reassign nodal force.

## Necessary conservation / consistency

- For each of the three components, `fsum` over ALL body-node Fx/Fy must reproduce the existing `record.workpiece.force_on_lower_body_N[component]`, using the same saved global force values and node order. This is data-consistency, not a new constitutive reference.
- Sum the four disjoint groups to the all-body resultant without counting corners or the 17 background-overlap uy DOFs twice. The original global fixed-reaction partition remains WP-priority; node/face display groups must not be added again as independent constraints.
- Compare all-body total with minus saved holding on the identical DOFs, after checking no actuator/spring term on them. The current cached sign contract is unchanged.
- Record total minus (material + regularization) as a roundoff diagnostic. Saved total and component assemblies can differ in floating-point addition order; do not require their pointwise binary64 sum to be bitwise identical or alter the original scientific gates.
- Optional scalar moment about task center is `sum((x-cx)*Fy - (y-cy)*Fx)` in N mm, per component and group. Keep product residuals with math.fma plus fsum (or exact sums of stored binary64 products) if calling it compensated. Group moments must sum to the all-body moment. This is a saved nodal virtual-work measurement, not an independently qualified stress/pressure resultant. It need not vanish for the lower half.
- Mirror upper node/vector as (x, 2*cy-y)/(Fx,-Fy); whole-body net is (2*Fx,0), not (0,0). The mirrored moment about the same center changes sign. `2*abs(Fy)` is a scalar magnitude sum, never a net force or proof of clamp.

## Minimal useful saved output

One nodes CSV/NPZ per accepted state (all body nodes, no duplicate-index removal), one compact JSON of exact group memberships/resultants and comparisons, and one figure: fixed-square actual coordinates, signed Fx/Fy or shared-scale vector arrows for all three components. Visually distinguish face-interior, junction, cut-only and interior rows. A common N arrow scale across all path states makes loading/unloading comparable; no arrows or colorbar labelled pressure. Show the signed resultant beside each map and keep corner/cut legends explicit.

Bind original model/task/state/16-force archive bytes and metadata. If prior state HP passed, state that this is an extraction from that saved qualified state, not new HP coverage of pressure, per-face contact, energy, or every tangent column. Allow a future partial-path display only with its actual production status and its own reference availability; never borrow successful-cycle qualification. Minimal checks are one hand-written nodal-force/holding case, one corner-and-cut membership case, and one signed/moment/component-roundoff case, followed by the actual saved full-node extraction. No new equilibrium solve is necessary for this functionality.

## Source identities read

- `hf_repo/src/hf_eval/native_mean.py`: `186a6662c14310b4dc577591764eef849988448de132474fd6953579449cb22b`
- `hf_repo/src/hf_eval/native_project.py`: `4f1b4f772938bb870e8784fac881bad9a16f004fabf3b6e91ea9d2701c7601bc`
- `hf_repo/src/hf_eval/split_displacement.py`: `f4632beb5697e6f25f374c4de31d25f712dd0c91723fed6021f866ada60a386c`
- `hf_repo/src/hf_eval/boundary_geometry.py`: `b22a9efe9bb29cdf94746f694a721df42bd0f867ba8c2252915e072b6a73fb31`
- `hf_repo/src/hf_eval/native_region_geometry.py`: `0bc3fa706431de16761d3ffa89b37e56ef3f4782984362d14792b1f5dd26aa98`
