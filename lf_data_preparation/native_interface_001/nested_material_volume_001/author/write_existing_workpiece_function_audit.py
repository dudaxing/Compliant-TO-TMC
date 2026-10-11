"""Read original sources and saved JSON, write an external existing-function audit."""
import hashlib
import json
from pathlib import Path
REPO=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path(__file__).resolve().parent
sources=[
 'hf_repo/src/hf_eval/native_evaluate.py',
 'hf_repo/src/hf_eval/native_mean.py',
 'hf_repo/src/hf_eval/split_displacement.py',
 'hf_repo/src/hf_eval/native_response.py',
 'hf_repo/src/hf_eval/workpiece_nodal.py',
 'hf_repo/src/hf_eval/saved_workpiece_loads.py',
 'hf_repo/src/hf_eval/native_region_geometry.py',
 'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
 'functional_views/native_api_workpiece_20261008/complete_001/saved_right_margin_views.py',
 'functional_views/native_nested_cycle_20261009/complete_001/execute_nested_views.py',
 'lf_data_preparation/native_interface_001/nested_reference_002/execute_nested_reference.py',
 'lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference/sources/core_audit_mechanical.py',
 'lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference/sources/audit_native_workpiece_cycle.py']
evidence=[
 'lf_data_preparation/native_interface_001/nested_link_001/run_001/linked_response.json',
 'lf_data_preparation/native_interface_001/nested_reference_002/run_001/reference/summary.json',
 'lf_data_preparation/native_interface_001/nested_ledger_002/run_001/execution_receipt.json',
 'functional_views/native_nested_cycle_20261009/complete_001/run_001/view/view.json']
actual_sources={}
for relative in sources+evidence:
 data=(REPO/relative).read_bytes()
 actual_sources[relative]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def read(relative):
 return json.loads((REPO/relative).read_text(encoding='utf-8'))
response,reference,ledger,view=[read(relative) for relative in evidence]
report={
 'schema_version':'existing-public-workpiece-function-readonly-audit-1.1',
 'status':'completed_readonly_existing_function_audit_no_new_execution_plan',
 'baseline_main':'7ea78ce19ba066dfce8a03892395d5604707dda6',
 'reviewer_role':'independent_volume_math_review',
 'purpose':'Preserve and reuse existing actual workpiece force/reference/view capabilities; identify the remaining physical definition and qualification gaps after M-VOLUME1 without duplicating functionality.',
 'actual_source_and_saved_evidence_SHA':actual_sources,
 'existing_capabilities':[
  {'function':'Native forward entry and saved response','sources':sources[:4],
   'implemented':'evaluate_native already performs the existing native mean path, persists original accepted states and produces compact target/peak/endpoint/last response. The saved public reader associates the matching reference and views without NPZ or a new solve.'},
  {'function':'Original total/material/Hu fixed-body loads','sources':[sources[1],sources[2]],
   'implemented':'Original signed ON-body weak nodal force is minus the original assembled internal weak force on fixed workpiece DOFs. Original global total/material/regularization(Hu) components, opposite holding reaction, and disjoint fixed-DOF partitions are already computed and saved; thickness is already included in N.',
   'limit':'These are discrete generalized weak forces. They do not supply a continuous pressure density or allocate corner action to incident faces.'},
  {'function':'Half model and mirror reporting','sources':[sources[1],sources[3]],
   'implemented':'Public total lower-half [Fx,Fy], mirrored upper [Fx,-Fy], full mirrored net [2Fx,0] and two-sided normal magnitude 2*abs(Fy) already exist.',
   'limit':'The normal magnitude is an available report under the existing weak-force convention. It remains distinct from certified effective grip and from full-body net force; mirror reporting does not solve a second half.'},
  {'function':'Nodal loads, moments and complete saved ledger','sources':[sources[4],sources[5]],
   'implemented':'The public observer already emits original total/material/Hu body-node vectors, group resultants and moments; physical/cut/intersection/interior groups keep each node once. M-LEDGER2 already reads all24 saved states and refines seven exclusive categories using original six force strings and original closure.',
   'actual_saved_receipt':{'status':ledger['status'],'selected_states':ledger['selected_states'],'calls':ledger['calls'],'shared_MLEDGER1_exact':ledger['shared_MLEDGER1_exact'],'paired_strokes':ledger['paired_strokes'],'paired_category_rows':ledger['paired_category_rows'],'all_bindings_unchanged':ledger['all_bindings_unchanged']}},
  {'function':'Actual deformation with three force components','sources':[sources[8],sources[9]],
   'implemented':'The existing24-frame actual_states.gif already overlays original total/material/Hu force-vector panels on actual deformed mechanism/body geometry, with all body nodes and a common display scale. Geometry and Fy are reflected for the visual upper half.',
   'actual_saved_manifest':{'status':view['status'],'common_nodal_force_scale':view['common_nodal_force_scale'],'mirroring':view['mirroring'],'contact_pressure_clamping_qualified':view['contact_pressure_clamping_qualified']},
   'limit':'The display is an existing weak nodal force view, not pressure recovery. A new generic two-state three-component deformation overlay would duplicate it.'},
  {'function':'Actual region and material diagnostics','sources':[sources[6]],
   'implemented':'Actual deformed-region overlap/intersection and finite-face hit diagnostics already exist. Material-only owner P trace, original material support and M-VOLUME1 selected depth contractions add local observations.',
   'limit':'Node-window clearances and region diagnostics explicitly are not certified contact or penetration measures. Material P traces omit Hu and do not qualify total pressure.'},
  {'function':'Independent saved force reference','sources':sources[10:13],
   'implemented':'M-REF2 already independently evaluates all24 original saved mechanical states at HP80/120 over all13440 elements and27378 real DOFs. Its original strict gates include signed total/material/Hu body force projections and disjoint holding projections.',
   'directional_tangent_scope':'The directional tangent check uses the actual five-node PORT direction, with fixed DOFs zero and deltaR=0. That tangent check is not a workpiece rigid-translation direction test; it does not negate the already checked full-force/body projection reference.',
   'energy_scope':'Independent analytic HP energy is archived without candidate energy comparison or energy qualification. An untested energy identity must not be presented as an existing gate, or presumed to be a required energy gradient identity for the current Hu weak residual.'}
 ],
 'actual_public_response_evidence':{
  'status':response['status'],'path':response['path'],'producer_flags':response['producer_flags'],
  'force_semantics':response['force_semantics'],
  'target_workpiece':response['target_response']['workpiece'],
  'matched_reference':response['independent_reference'],
  'original_reference_scope':reference['reference_scope'],
  'original_reference_qualification':reference['qualification'],
  'original_qualified_flags':{key:reference.get(key) for key in ['contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified']},
  'reference_energy_scope_fields':{key:value for key,value in reference.items() if 'energy_scope' in key}
 },
 'remaining_physical_function_gap':{
  'nearest_actual_gap':'A justified total interface-action/pressure interpretation including the original Hu weak term, with explicit boundary/corner meaning and physical contact/grip qualification. A total/material/Hu workpiece resultant API and its independent force reference already exist.',
  'existing_reusable_primitives':'Retain original response, original same-state body total/material/Hu vectors, holding partitions, mirror convention, existing independent force references and existing actual-state viewer. State their present discrete generalized-load meaning clearly while developing any stronger pressure or effective-grip claim.',
  'Hu_boundary_dependency':'The original Hu residual contracts higher displacement gradients with a state-dependent quadrature scale. Adding a scalar Hu contribution to P@N would not by itself define a total ordinary pressure. Recovering face/derivative/corner actions requires a consistent discrete boundary/virtual-work definition.',
  'corner_dependency':'Original nodal corner action and owner-specific material P samples do not uniquely determine pressure on each incident face; a recovery choice needs an explicit definition and validation.',
  'qualification_dependency':'Pressure/contact/effective grip and mesh/domain physical stability remain excluded from original mechanical reference qualification. Existing geometry diagnostics and one fixed-square h0.5 cycle cannot silently become those stronger claims.',
  'coarse_route':'First retain and document the already independently checked fixed-body total weak action as a discrete generalized load including Hu, then resolve the total boundary interpretation and choose the minimum physical qualification study required by the intended report. Reuse existing visible response/views; no automatic repeat of the24-state ledger, body-force HP reference or DD reconstruction.',
  'virtual_work_or_energy_caution':'A new rigid-body virtual-work interpretation, if selected, must address a specific unverified boundary meaning. Simple projection of already HP-checked full force is not a new missing force implementation. The PORT tangent scope and archived energy limitation alone do not establish a solver defect or justify a duplicate HP campaign.',
  'planning_limit':'Future route basis only. M-VOLUME1 closure is current work; no execution card, new calculation or authorization is created by this audit.'
 },
 'do_not_repeat':['total/material/Hu workpiece force API','holding reaction and disjoint partitions','half/mirror/full-net/normal-magnitude report','matched saved response/reference/view link','all24 saved nodal ledger','generic three-component force/deformation overlays','independent body-force projection already covered by the actual HP reference'],
 'activities':{'source_and_existing_JSON_only':True,'raw_source_evidence_SHA':True,'NPZ_decodes':0,'public_API_calls':0,'new_HP_calls':0,'new_scientific_numerical_values':0,'new_integrals':0,'new_fsum_calls':0,'new_plot_calls':0,'repository_mutations':0,'new_execution_cards':0},
 'audit_limit':'Read-only source/saved-record audit; no existing capability is rerun or requalified, and no contact/pressure/clamp/HF5 flag is changed.'
}
path=OUT/'existing_workpiece_function_audit.json'
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},ensure_ascii=False))