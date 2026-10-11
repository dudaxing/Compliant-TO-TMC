"""Source/metadata and symbolic derivation only; no candidate imports or science calculations."""
import ast
import hashlib
import json
from pathlib import Path
REPO=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path(__file__).resolve().parent
paths=[
 'hf_repo/src/hf_eval/tmc_kernel.py',
 'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
 'hf_repo/src/hf_eval/compensated_invariants.py',
 'hf_repo/src/hf_eval/tmc.py',
 'hf_repo/src/hf_eval/native_project.py',
 'hf_repo/src/hf_eval/native_mean.py',
 'hf_repo/src/hf_eval/saved_material_support.py',
 'hf_repo/src/hf_eval/workpiece_nodal.py',
 'hf_repo/src/hf_eval/native_response.py']
anchors={paths[0]:['def operators(','def _residual_with_aux(','regularization =','_jacobian_with_aux ='],
 paths[1]:['def _response(','action_pair =','exponential =','scale =','regularization_pair =','residual_pair =','_jacobian_with_aux =','def batch_response_split_mechanical_numpy('],
 paths[2]:['def kinematics_pairs(','Hu = dd_add','def hessian_action_pair('],
 paths[3]:['self.edofs =','self.ops ='],
 paths[4]:['kr = alpha','dof_order='],
 paths[5]:['def _workpiece_observations(','observations =','arrays = dict(element_total_force='],
 paths[6]:['GROUPS =','assigned[int(cell)] = "corner_only"'],
 paths[7]:['def observe_workpiece_nodal_forces('],
 paths[8]:['def summarize_saved_native_result(']}
source_records=[]
for relative in paths:
 data=(REPO/relative).read_bytes()
 content=data.decode('utf-8')
 tree=ast.parse(content)
 lines=content.splitlines()
 selected={token:next(index for index,line in enumerate(lines,1) if token in line) for token in anchors[relative]}
 source_records.append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
  'AST_parse':'pass_without_import','line_anchors':selected})
report={
 'schema_version':'Q1-Hu-generalized-boundary-source-physical-basis-1.0',
 'status':'completed_source_only_symbolic_basis_no_new_numerical_gate',
 'baseline_main':'0d83b18b2bb320f137b1c4c3295805dc7c15aa65',
 'scope':'Read actual Q1/Hu and accepted-force storage source; distinguish original weak residual from an energy gradient and define the smallest nonduplicate generalized edge/corner observation. No NPZ, candidate/API, HP, new integral, plot or formal repository mutation.',
 'actual_source_records':source_records,
 'tensor_and_operator_contract':{
  'nodes':['BL','BR','TR','TL'],
  'element_dofs':'uxBL,uyBL,uxBR,uyBR,uxTR,uyTR,uxTL,uyTL; edofs=(2*connectivity[...,None]+[0,1]).reshape(ne,8)',
  'derivative_coordinates':'Undeformed physical reference X,Y. Rectangles are equal, axis aligned; hx and hy are their widths.',
  'quadrature_order':'q=3*xi_index+eta_index, each index ordered(-1,0,+1): xi varies slowly and eta quickly. Top eta=+1 is q2,5,8.',
  'shapes':{'grad':'(9,4,2), grad[q,a,J]','hessian':'(4,2,2), H[a,J,K]','P':'(...,9,2,2), P[q,i,J]','Hu':'(...,2,2,2), Hu[i,J,K]; no q axis','weights':'(9,), includes thickness and reference area'},
  'gradX':'[(eta-1),(1-eta),(1+eta),(-1-eta)]/(2*hx)',
  'gradY':'[(xi-1),(-1-xi),(1+xi),(1-xi)]/(2*hy)',
  'Hessian':'H[a,X,Y]=H[a,Y,X]=s_a/(hx*hy), s=[+1,-1,+1,-1]; H[a,X,X]=H[a,Y,Y]=0.',
  'weights':'w_q=(thickness*hx*hy/36)*sxi*seta, with Simpson factors[1,4,1]. Sum(w)=thickness*hx*hy.',
  'split_authority':'Lift and fluctuation are accumulated separately into retained DD kinematic pairs. Material P and Hu are DD through original weak contractions. Exported observations are independently rounded binary64.'},
 'original_weak_residual':{
  'mathematical_symbols':'u_ai=lift_ai+fluctuation_ai symbolically; F_qiJ=delta_iJ+sum_a u_ai grad_qaj; J_q=det F_q; h_i=(uBL_i-uBR_i+uTR_i-uTL_i)/(hx*hy).',
  'Hu':'Hu_iXY=Hu_iYX=h_i and Hu_iXX=Hu_iYY=0; Hu is constant within each reference Q1 rectangle.',
  'material':'r_material[a,i]=sum_q w_q P[q,i,J] grad[q,a,J]. P=mu F+(lambda logJ-mu)F^(-T), evaluated by the original compensated arithmetic.',
  'coefficient':'c_e(u)=kr*sum_q w_q exp(-5 J_q). This is element-local despite scalar model kr, and includes original thickness. c_e is not exported by native_mean capture.',
  'Hu_force':'r_Hu[a,i]=c_e*sum_JK Hu[i,J,K]*H[a,J,K]. Both XY and YX contribute: no factor-one replacement is valid.',
  'total':'r_total=r_material+r_Hu in original DD before export rounding; the saved three force observations are not interchangeable by a new binary64 total=material+Hu gate.',
  'virtual_action':'For a Q1 virtual nodal field v, r_e dot v_e = sum_q w_q P_q:grad(v_q) + c_e Hu:D2(v_e). This is a weak covector evaluated at the actual state, not a declaration that it is d(total_energy).',
  'on_body_sign':'Existing ON-body force is minus the internal element/global weak covector. Holding reaction uses the opposite convention.'},
 'energy_gradient_judgment':{
  'conclusion':'The actual general Hu force is not the gradient of the naive scalar E_Hu=one_half*c_e(u)*||Hu(u)||_F^2. The general residual is not supplied as a total potential gradient by this code.',
  'naive_energy_variation':'dE_Hu[v]=c_e Hu:D2v + one_half*||Hu||_F^2*dc_e[v]. The original force contains only the first term.',
  'dc_e':'dc_e[v]=-5 kr sum_q w_q exp(-5J_q) (cof(F_q):grad(v_q)). No such J-derivative force term appears in either original residual source.',
  'actual_tangent':'AD differentiates the actual residual c_e H^T Hu, so its directional derivative includes dc_e[v]*H^T Hu + c_e H^T D2v. This tangent contribution is different from adding the omitted energy-gradient term to force.',
  'generic_integrability':'With constant K=H^T H, Dr_Hu=c_e K+(Ku) outer grad(c_e). Its antisymmetric part is (Ku) outer grad(c_e)-grad(c_e) outer (Ku), generally nonzero. An affine virtual field has H v=0 but can change J/c_e when Hu is nonzero; a mixed Q1 field changes Hu. Thus general symmetry/integrability cannot be inferred.',
  'special_cases':'kr=0, Hu=0, a frozen c_e, or special state/direction restrictions may remove an offending term locally. This source-only derivation does not calculate antisymmetry for any actual saved state or matrix.',
  'material_energy_caution':'Material P has the standard Neo-Hookean constitutive interpretation, but the near-zero exported auxiliary energy uses a truncated stable remainder and is explicitly not used for P or residual Jacobian. Mechanical mode omits that energy entirely. Existing HP energy is archived without candidate energy qualification.',
  'implementation_consequence':'Do not add the omitted energy-gradient term as a repair and do not compare original total reaction to a naive total-energy finite difference. Either would change the model or use an inapplicable oracle. Use the original residual virtual action for generalized boundary meaning.'},
 'canonical_element_Hu_corner_identity':{
  'beta_definition':'beta_ei=2*c_e*h_i/(hx*hy), units N.',
  'internal_vertex_covector':'[r_Hu_BL,r_Hu_BR,r_Hu_TR,r_Hu_TL]=[+beta,-beta,+beta,-beta] for each displacement component.',
  'on_body_vertex_covector':'For selected body vertices, negate the corresponding internal entry; do not include unselected vertices.',
  'action':'W_Hu(v)=beta dot(vBL-vBR+vTR-vTL). This represents the original Q1 action at element vertices, and is a concrete signed generalized corner action. Element vertices include ordinary assembled interface nodes; this is not a claim that forces exist only at macroscopic workpiece corners.',
  'full_rigid_translation':'For vBL=vBR=vTR=vTL=constant, W_Hu=0. All four vertex internal vectors sum to zero symbolically.',
  'side_pair_translation':'Any adjacent pair of vertices has opposite Hu signs. A common translation on that selected pair and zero virtual field on the other pair has zero Hu action, because its Q1 shape sum is affine and D2chi=0.',
  'single_vertex':'A corner_only support element selecting one body vertex retains its signed beta action; single-node basis is not affine.',
  'matrix_or_scalar_pressure_limit':'A beta vector is force N conjugate to the vertex value combination. It is not a scalar pressure MPa, and choosing its normal component does not establish pressure or effective-grip qualification.'},
 'element_local_hyperstress_representations':{
  'quadrature_representation':'M_qiJK=kr exp(-5J_q) Hu_iJK satisfies sum_q w_q M_q:D2v=c_e Hu:D2v for Q1 v. This is a quadrature weak representation, not evidence of a known true continuous hyperstress trace.',
  'constant_Q1_equivalent':'Choose Mbar_eiJK=(c_e/(thickness*hx*hy))*Hu_iJK. Then thickness*integral_rectangle Mbar:D2v dA equals the same original Q1 Hu action, because D2v and Hu are constant.',
  'density_units':'Mbar is MPa*mm=N/mm; its thickness-weighted boundary derivative action has force units N. beta=2*thickness*Mbar_iXY.',
  'uniqueness_limit':'The constant representation is a declared Q1-equivalent reconstruction. It is not the original pointwise kr exp(-5J) Hu field, and no original unique continuous field or boundary trace follows from the finite nodal covector. Other fields with the same quadrature/virtual action can have different traces.',
  'generic_integration_by_parts':'For a chosen sufficiently smooth P(X),M(X), W=thickness*integral[P_iJ v_i,J+M_iJK v_i,JK]dA. Let A_iJ=P_iJ-partial_K M_iJK, b_iJ=n_K M_iJK. On each oriented edge, edge_value_traction=n_J A_iJ-partial_s(tau_J b_iJ), edge_normal_derivative_action=n_J b_iJ, and endpoint action=[tau_J b_iJ*v_i]_start^end; interior term is -partial_J A_iJ*v_i.',
  'constant_Q1_specialization':'For constant offdiagonal Mbar on an axis-aligned rectangle, Div(Mbar)=0, edge normal-derivative action Mbar_nn=0, and tangent b_s is constant. Its Hu action reduces to four oriented endpoint/corner terms; with CCW edges it is +2*thickness*Mbar_iXY at BL/TR and -2*thickness*Mbar_iXY at BR/TL.',
  'no_pressure_addition':'This canonical constant Hu choice produces endpoint/derivative action, not an ordinary Hu pressure added to P@N. Discarding the endpoint terms would discard original virtual work.'},
 'interface_edges_and_corner_support':{
  'outside_bottom_owner':'Body pair is local TL/TR on outer-cell top edge. Internal pair is[-beta,+beta]; ON-body in left-to-right order is[+beta,-beta]. Its action is beta dot(v_left-v_right).',
  'outside_left_owner':'Body pair is local BR/TR on outer-cell right edge. ON-body bottom-to-top is[+beta,-beta].',
  'outside_right_owner':'Body pair is local BL/TL on outer-cell left edge. ON-body bottom-to-top is[-beta,+beta].',
  'assembled_edge_node':'After assembling neighbouring owner endpoints, signed differences of owner beta values can act at an interior body-edge node. This is a discrete owner endpoint/jump observation; it does not establish the trace or jump of a true continuous hyperstress field.',
  'net_Hu_condition':'For the complete fixed lower-half square topology already encoded in saved_material_support: body cells have all four fixed zero displacement vertices and Hu=0; every noncorner outside owner contributes a selected adjacent pair with zero symbolic resultant. Consequently the whole signed body Hu resultant is supplied by the remaining corner_only single-node support elements, in exact mathematical arithmetic.',
  'actual_value_limit':'No actual Hu field, coefficient, beta, endpoint cancellation, owner jump or corner resultant has been read or computed in this source-only preparation. Export rounding/scatter order must be respected by any future observation; this conclusion is conditional on the actual fixed-square topology and original operator contract, not an observed numerical equality.',
  'corner_attribution_limit':'A macroscopic corner node also receives side-owner endpoints and corner_only element terms. All must remain owner-resolved; the original net node force cannot be uniquely called pressure on either incident face.'},
 'material_P_and_total_boundary_limit':{
  'current_material_data':'Nine saved P owner samples plus original material nodal weak force exist. They do not uniquely specify a true continuous P field or its divergence.',
  'material_action_not_just_trace':'For any chosen smooth P reconstruction, material weak force equals the full boundary nodal traction integral minus its interior Div(P) virtual-field integral. A single body-facing P@N trace is not generally the selected nodal material weak action.',
  'possible_declared_reconstruction':'A tensor-product biquadratic interpolant through the nine Simpson points is one explicit choice. For Q1 test fields, products P_h*grad(v), edge(P_h*v), and Div(P_h)*v have degrees within tensor Simpson exactness, yielding a symbolic discrete integration-by-parts identity. This would be a new interpolation/derivative/integration observation with its own scope, not the true DivP or an established physical cause.',
  'minimal_route':'Do not introduce that P reconstruction just to complete the Hu corner function. Reuse authoritative saved material/total weak node forces; add only owner-resolved Hu endpoint/corner meaning where needed. A stronger total face-pressure claim still requires an explicit material recovery, Hu boundary convention and physical qualification.'},
 'minimum_nonduplicate_implementable_function':{
  'proposed_capability':'A saved-state Q1 Hu owner endpoint/corner weak-action observer: trace original element regularization force to body vertices, distinguish side-owner adjacent pairs from corner_only single vertices, retain signs/owner identity, and expose what cancels for body translation and what remains at corners. Integrate or link this explanation with the existing total/material/Hu response and actual-state viewer.',
  'authoritative_input':'Prefer original saved element_regularization_force plus original connectivity/edofs and existing body/owner/corner metadata. native_mean.capture already stores element_regularization_force and global_regularization_force. The original accepted storage exports rounded J and Hu but not retained J/Hu pairs or c_e; do not rebuild exp(-5*roundedJ) and multiply roundedHu then present it as original DD force.',
  'minimum_new_read_scope_if_selected':'Original model connectivity/edofs plus body node/cell/fixed IDs and existing trace owner records, selected saved element_regularization_force and corresponding original global_regularization_force/nodal ledger. Additional P/J/Hu/kinematics or a force-kernel call are unnecessary to observe original Hu local action. Actual scope and count remain for root/author to decide in a future concrete card.',
  'output_meaning':'Original element vertex internal and ON-body force values in N, owner edge/corner classification, selected adjacent-pair and corner actions, original nodal association. Clearly distinguish element vertices from macroscopic workpiece corners and weak derivative action from pressure.',
  'possible_verification':'Replay the unchanged original C-order regularization scatter against the saved global vector if that operation is selected and authorized; copied local-to-node association is a data provenance check. Original rounded-force pair patterns and future local regrouping need explicitly justified tolerances or descriptive differences. This basis does not introduce a numerical gate or assume exact reconstructed beta equality.',
  'avoid_duplicates':'No new general body resultant API,24-state ledger, existing three-component deformed GIF, body-force HP projection, DD/P reconstruction or total-energy check is needed for this minimal Hu interpretation function.',
  'formal_qualification':'It advances the total generalized boundary interpretation, but leaves contact/pressure/effective-grip and mesh/domain stability flags unchanged. None of this alone makes a qualified physical pressure or effective holding force.'},
 'activities':{'source_AST_and_raw_SHA_only':True,'symbolic_derivations_only':True,'NPZ_decodes':0,'candidate_imports':0,'API_calls':0,'HP_calls':0,'new_scientific_numerical_values':0,'new_integrals':0,'new_fsum_calls':0,'plot_calls':0,'formal_repo_mutations':0,'new_execution_cards':0}
}
path=OUT/'physical_basis.json'
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},ensure_ascii=False))