"""Saved cycle007 arithmetic review only: no mechanics/reference/consumer imports."""
from time import perf_counter
STARTED=perf_counter()
from pathlib import Path
from decimal import Decimal, localcontext, Inexact
import gzip, hashlib, json
import numpy as np
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE=ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_007'
REF=STAGE/'reference'
OUT=Path(__file__).with_name('cycle007_actual_saved_math_review.json')
PINS={}
COUNTS=dict(local_vector_gates=0,global_vector_gates=0,scalar_gates=0,workpiece_gates=0,saved_global_differences=0)
MAX={}
PARTS=('total','material','regularization')
FORCE=('internal_decimal','material_internal_decimal','regularization_internal_decimal')
ACTION=('tangent_action_decimal','material_tangent_action_decimal','regularization_tangent_action_decimal')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p,expected=None):
 p=p.resolve();actual=sha(p);assert expected is None or actual==expected,(p,'fileSHA');assert p not in PINS or PINS[p]==actual
 PINS[p]=actual;return actual
def read(p,expected=None):bind(p,expected);return json.loads(p.read_text(encoding='utf-8'))
def gz(p,expected=None):bind(p,expected);return json.loads(gzip.decompress(p.read_bytes()))
def archive(p,decl=None):
 bind(p,None if decl is None else decl['sha256'])
 with np.load(p,allow_pickle=False) as a:out={k:a[k].copy() for k in a.files}
 if decl:
  assert set(out)==set(decl['fields']) or set(out)=={'data','indices','indptr','shape','format'}
  for k,v in decl['fields'].items():assert dict(dtype=out[k].dtype.name,shape=list(out[k].shape),sha256=hashlib.sha256(out[k].tobytes()).hexdigest())==v,(p,k)
 return out
def canonical(x):
 if isinstance(x,dict):return {k:canonical(v) for k,v in x.items()}
 if isinstance(x,list):return [canonical(v) for v in x]
 if isinstance(x,float):return (0. if x==0. else x).hex()
 return x
def semantic(x):return hashlib.sha256(json.dumps(canonical(x),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def descriptor(x):assert semantic({k:v for k,v in x.items() if k!='descriptor_sha256'})==x['descriptor_sha256']
def decs(x):return [Decimal(a) for a in x]
def D(x):return Decimal.from_float(float(x))
def norm(x):return sum((a*a for a in x),Decimal(0)).sqrt()
def update(key,x,index,element=None):
 if key not in MAX or x>Decimal(MAX[key]['value']):MAX[key]=dict(value=str(x),where=dict(index=index,**({} if element is None else {'element':element})))
def compare(actual,a,b,den,record,limit,index,label,element=None,diffs=None):
 diff=[D(x)-y for x,y in zip(actual,a,strict=True)]
 error=norm(diff)/den;agreement=norm([x-y for x,y in zip(a,b,strict=True)])/den
 assert Decimal(record['denominator'])==den,(index,label,'denominator')
 assert Decimal(record['normalized_error'])==error,(index,label,'error')
 assert Decimal(record['hp80_hp120_error'])==agreement,(index,label,'HPagreement')
 assert Decimal(record['limit'])==Decimal(limit) and Decimal(record['reference_limit'])==Decimal('1e-40')
 assert record['pass_gate'] is True and error.is_finite() and agreement.is_finite() and error<=Decimal(limit) and agreement<=Decimal('1e-40')
 update(label+'_normalized_error',error,index,element);update(label+'_HP80_120_error',agreement,index,element)
 if diffs is not None:assert decs(diffs)==diff,(index,label,'savedDifference');COUNTS['saved_global_differences']+=1
 return diff

def references(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v:bind(REF/v['path'],v['sha256'])
  for a in v.values():references(a)
 elif isinstance(v,list):
  for a in v:references(a)

inventory=read(STAGE/'input_inventory.json');freeze=read(STAGE/'source_freeze.json',inventory['source_freeze_sha256'])
protocol=read(STAGE/'protocol.json');receipt=read(STAGE/'execution_receipt.json')
production=read(STAGE/'production_launch.json');launch=read(STAGE/'reference_launch.json');life=read(REF/'lifecycle.json')
summary=read(REF/'summary.json')
assert len(protocol['bindings'])==186
for k,v in protocol['bindings'].items():bind(ROOT/k,v)
assert len(freeze['sources'])==68 and receipt['sources']==freeze['sources']==summary['source_bindings']
for k,v in freeze['sources'].items():
 bind(ROOT/k,v);bind(STAGE/'sources'/Path(k).name,v);bind(REF/'sources'/Path(k).name,v)
for k,v in summary['input_bindings'].items():bind(ROOT/k,v)
for l in (production,launch):
 assert l['status']=='pass' and l['exit_code']==0 and l['invocations']==1 and l['all_bindings_unchanged'] and l['stop_reason'] is None
 assert l['protocol_sha256']==sha(STAGE/'protocol.json')
assert receipt['status']=='pass' and receipt['sources_unchanged'] and receipt['inputs_unchanged']
counts=receipt['call_counts']
assert receipt['force_calls']==receipt['observed_force_calls']==counts['force_calls']
assert receipt['observed_force_calls_completed']==counts['force_calls_completed']
assert receipt['tangent_calls']==receipt['observed_tangent_calls']==receipt['observed_tangent_calls_completed']==counts['tangent_calls']==counts['tangent_calls_completed']
assert receipt['solver_calls']==receipt['invocations']==1 and receipt['HP_calls']==receipt['JIT_calls']==0
assert receipt['first_tangent_range_input'] is None
assert receipt['force_hook_restored'] and receipt['tangent_hook_restored']
result=read(STAGE/'result/result.json',receipt['result_sha256']);descriptor(result)
assert sha(STAGE/'result/result.json')==summary['result_sha256']
assert result['call_counts']==receipt['call_counts']
assert summary['status']==life['status']=='pass' and summary['HP_calls_started']==summary['HP_calls_completed']==life['HP_calls_started']==life['HP_calls_completed']==2*len(result['states'])
assert summary['checks_completed']==life['checks_completed'] and type(summary['checks_completed']) is int and summary['checks_completed']>0
accounting=summary['counter_accounting'];assert accounting['counts']==counts
assert counts['force_calls']-counts['force_calls_completed']==len(accounting['rejected_range_trials']) and accounting['all_Newton_base_and_tangent_calls_completed'] is True
assert summary['tangent_observation']['first_tangent_range_input'] is None and summary['tangent_observation']['all_tangent_calls_completed'] is True
if receipt['first_force_range_input'] is None:
 assert not accounting['rejected_range_trials'] and summary['first_force_range_input'] is None and not (STAGE/'first_force_range_input').exists()
else:
 observer=read(STAGE/'first_force_range_input/observation.json')
 assert observer==receipt['first_force_range_input'] and observer['code']=='unsupported_arithmetic_range'
 captured=archive(STAGE/'first_force_range_input/input.npz',dict(sha256=observer['input_npz_sha256'],fields=observer['fields']))
 assert len(captured)==16 and accounting['rejected_range_trials'] and summary['first_force_range_input'] is not None
assert summary['gates']==inventory['gates'] and summary['full_element_and_DOF_coverage'] and not summary['HP_matrix_columns_exhaustively_checked']
assert summary['candidate_force_calls']==summary['tangent_calls']==summary['solver_calls']==0
assert not any(summary[k] for k in ('contact_qualified','clamp_qualified','pressure_qualified'))
GATES=summary['gates'];origin=STAGE/'result'
modelmeta=read(origin/result['model']['descriptor_path'],result['model']['descriptor_file_sha256']);descriptor(modelmeta)
model=archive(origin/result['model']['arrays_path'],modelmeta['arrays'])
assert len(model)==27 and sha(origin/result['model']['arrays_path'])==receipt['model_sha256']=='a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049'
assert semantic(modelmeta['task'])==result['task_sha256']==receipt['task_sha256']
free=model['free_dofs'];fixed=model['fixed_dofs'];edofs=model['edofs'];ne,ndof=len(edofs),len(model['b_in'])
assert (ne,ndof,len(fixed),len(free))==(3200,6642,376,6266)
for k,p in modelmeta['source_geometry']['snapshot'].items():bind(origin/'model'/p,modelmeta['source_geometry']['descriptor_file_sha256' if k=='descriptor' else 'arrays_sha256'])
targets=[0.,.5,1.,1.5,1.,.5,0.]
assert result['targets_mm']==inventory['case']['targets_mm']==modelmeta['task']['path']['targets_mm']==targets
assert modelmeta['task']['input']['target_mm']==1.5 and result['path_completed'] and result['task_target_executed']
states=result['states'];assert len(states)==len(summary['states'])==summary['accepted_states']==life['accepted_states_completed'] and len(states)>=len(targets)
originals=[r for r in states if r['is_original_target']]
assert [r['d'] for r in originals]==targets and [r['original_target_index'] for r in originals]==list(range(len(targets)))
assert states[0]['d']==states[-1]['d']==0. and states[0]['original_target_index']==0 and states[-1]['original_target_index']==len(targets)-1
for r in states:
 target_index=r['original_target_index'];assert r['leg']==('origin' if target_index==0 else 'loading' if targets[target_index]>targets[target_index-1] else 'unloading')
assert len({r['descriptor_path'] for r in states})==len(states)
assert [r['state_sha256'] for r in states]==receipt['state_sha256']
STATE_RECORDS=[]
for index,(row,audit) in enumerate(zip(states,summary['states'],strict=True)):
 references(audit)
 assert audit['index']==index and audit['state_sha256']==row['state_sha256'] and audit['HP_calls']==2
 assert audit['elements_compared']==ne and audit['global_DOFs_compared']==ndof and audit['full_matrix_entries_assembly_checked']==ne*64
 stored=read(origin/row['descriptor_path'],row['descriptor_file_sha256']);descriptor(stored)
 assert stored=={k:v for k,v in row.items() if k not in ('descriptor_path','descriptor_file_sha256')}
 state=archive(origin/row['state']['path'],row['state']);forces=archive(origin/row['forces']['path'],row['forces'])
 tensors=archive(origin/row['tangents']['path'],row['tangents']);matrix=archive(origin/row['matrix']['path'],row['matrix'])
 assert (len(state),len(forces),len(tensors),len(matrix))==(2,16,3,5) and 'material_energy' not in forces
 h=hashlib.sha256(b'split_displacement_v1'+np.asarray(ndof,dtype='<i8').tobytes()+state['lift'].astype('<f8',copy=False).tobytes()+state['fluctuation'].astype('<f8',copy=False).tobytes())
 assert h.hexdigest()==row['state_sha256']==row['assembler_state_sha256']
 assert not np.any(state['lift']) and not np.any(state['fluctuation'][fixed]) and np.all(forces['J']>0.)
 assert row['matrix']['units']=='N/mm' and row['matrix']['symmetrized'] is False
 fixture=archive(REF/audit['raw_fixture']['path'])
 assert np.array_equal(fixture['actual_edofs'],edofs) and np.array_equal(fixture['actual_lift'],state['lift']) and np.array_equal(fixture['actual_fluctuation'],state['fluctuation'])
 for k in ('lift','fluctuation'):assert np.array_equal(fixture[k],state[k][edofs].ravel())
 actions=archive(REF/audit['actions']['path']);direction=actions['direction']
 assert np.array_equal(fixture['actual_direction'],direction) and np.array_equal(fixture['direction'],direction[edofs].ravel())
 assert np.count_nonzero(direction[fixed])==0 and float(actions['multiplier_direction'])==0.
 hp={}
 for p,ref in zip((80,120),audit['references'],strict=True):
  raw=gz(REF/ref['path'],ref['sha256']);assert raw['precision']==p and raw['real_state_sha256']==row['state_sha256']
  hp[p]={k:decs(raw['values'][k]) for k in (*FORCE,*ACTION)}
  assert all(len(v)==ne*8 for v in hp[p].values())
  assert all(Decimal(x)>0 for cell in raw['values']['J_decimal'] for x in cell)
 globalraw=gz(REF/audit['global_references']['path']);glob={p:{k:decs(v) for k,v in globalraw[str(p)].items()} for p in (80,120)}
 assert all(len(v)==ndof for p in glob.values() for v in p.values())
 gates=gz(REF/audit['exact_element_gates']['path']);eq=gz(REF/audit['equations']['path']);differences=gz(REF/audit['global_differences']['path'])
 body=gz(REF/audit['workpiece_checks']['path'])
 with localcontext() as context:
  context.prec=120
  floor=Decimal('1e-8')*D(model['force_scale_per_length'])*max(abs(D(row['target_origin'])+D(row['d'])),Decimal('1e-6'))
  assert Decimal(eq['independent_equations']['120']['force_scale_floor'])==floor
  act, spring=(decs(eq['independent_equations']['80'][k]) for k in ('actuator','spring'))
  SF=max(norm([glob[80][FORCE[0]][i] for i in free]),norm([act[i] for i in free]),norm([spring[i] for i in free]),floor)
  assert SF==Decimal(eq['independent_equations']['80']['force_scale'])==Decimal(audit['metrics']['force_scale_N'])
  for kind,keys in (('force',FORCE),('tangent',ACTION)):
   assert gates[kind]['component_order']==list(PARTS)
   for element in range(ne):
    span=slice(8*element,8*element+8);localSF=max(norm(hp[80][FORCE[0]][span]),floor)
    for col,(part,key) in enumerate(zip(PARTS,keys,strict=True)):
     a,b=hp[80][key][span],hp[120][key][span]
     den=(localSF if part=='total' else max(norm(a),Decimal('1e-12')*localSF)) if kind=='force' else max(norm(a),Decimal('1e-10'))
     actual=forces['element_'+part+'_force'][element] if kind=='force' else actions['element_'+part+'_action'][element]
     limit=GATES[part+'_force' if kind=='force' else part+'_tangent']
     compare(actual,a,b,den,gates[kind]['per_element'][col][element],limit,index,'local_'+part+'_'+kind,element)
     COUNTS['local_vector_gates']+=1
  for col,part in enumerate(PARTS):
   a,b=glob[80][FORCE[col]],glob[120][FORCE[col]];den=SF if part=='total' else max(norm(a),Decimal('1e-12')*SF)
   compare(forces['global_'+part+'_force'],a,b,den,audit['force_checks'][part],GATES[part+'_force'],index,'global_'+part+'_force',diffs=differences[part+'_force']);COUNTS['global_vector_gates']+=1
   a,b=glob[80][ACTION[col]],glob[120][ACTION[col]];den=max(norm(a),Decimal('1e-10'))
   compare(actions['global_'+part+'_action'],a,b,den,audit['tangent_checks'][part],GATES[part+'_tangent'],index,'global_'+part+'_tangent',diffs=differences[part+'_tangent']);COUNTS['global_vector_gates']+=1
  compare(actions['csc_total_action'],glob[80][ACTION[0]],glob[120][ACTION[0]],max(norm(glob[80][ACTION[0]]),Decimal('1e-10')),audit['CSC_total_action_check'],GATES['total_tangent'],index,'CSC_total_tangent',diffs=differences['CSC_total_tangent']);COUNTS['global_vector_gates']+=1
  ar=eq['augmented_reference_force'];a,b=[decs(v) for v in ar];af,bf=([v[i] for i in free] for v in (a,b))
  compare(actions['augmented_force_action'][free],af,bf,max(norm(af),Decimal('1e-10')),audit['augmented_checks']['force'],GATES['augmented_force_tangent'],index,'KKT_force');COUNTS['global_vector_gates']+=1
  dg=Decimal(eq['augmented_reference_constraint'])
  compare([float(actions['augmented_constraint_action'])],[dg],[dg],max(abs(dg),Decimal('1e-6')),audit['augmented_checks']['constraint'],GATES['augmented_constraint_tangent'],index,'KKT_constraint');COUNTS['global_vector_gates']+=1
  for g in audit['checks']:
   value=Decimal(g['normalized_error']);limit=Decimal(g['limit']);assert value.is_finite() and value<=limit and g['pass_gate'] is True
   COUNTS['scalar_gates']+=1
  for part,key in zip(PARTS,FORCE,strict=True):
   refs={}
   for p in (80,120):
    with localcontext() as exact:
     exact.prec=3000;exact.traps[Inexact]=True
     sums=[sum((glob[p][key][i] for i in model['workpiece_dofs'] if i%2==c),Decimal(0)) for c in (0,1)]
    refs[p]=[-x for x in sums]
    assert refs[p]==decs(body['signed_body_reference_N'][part][str(p)])
   den=SF if part=='total' else max(norm(glob[80][key]),Decimal('1e-12')*SF)
   compare(row['workpiece']['force_on_lower_body_N'][part],refs[80],refs[120],den,body['checks'][part+'_body_force'],GATES[part+'_force'],index,'body_'+part+'_force')
  for key,g in body['checks'].items():
   assert g['pass_gate'] is True and Decimal(g['normalized_error'])<=Decimal(g['limit']) and Decimal(g['hp80_hp120_error'])<=Decimal('1e-40') and Decimal(g['reference_limit'])==Decimal('1e-40')
   COUNTS['workpiece_gates']+=1
  for p in (80,120):
   measured=eq['independent_equations'][str(p)];residual=decs(measured['residual']);scale=Decimal(measured['force_scale'])
   assert norm([residual[i] for i in free])/scale==Decimal(measured['relative_residual'])
   assert norm(decs(measured['balance']))/Decimal(measured['balance_scale'])==Decimal(measured['relative_force_balance'])
  assert Decimal(audit['metrics']['independent_relative_residual'])==Decimal(eq['independent_equations']['120']['relative_residual'])
 STATE_RECORDS.append(dict(index=index,original_target_index=row['original_target_index'],leg=row['leg'],d_mm=row['d'],state_sha256=row['state_sha256'],R_input_N=row['R_input'],q_out_mm=row['q_out'],minimum_J=row['minimum_J'],metrics=audit['metrics'],force_floor_N=str(floor),body_force_on_lower_half_N=row['workpiece']['force_on_lower_body_N'],maximum_absolute_displacement_component_mm=float(abs(state['fluctuation']).max())))
 del hp,raw,globalraw,glob,gates,eq,differences,body,forces,tensors,matrix,state,fixture,actions
 print(json.dumps(dict(saved_state_review_complete=index,elapsed_seconds=perf_counter()-STARTED)),flush=True)
assert COUNTS['local_vector_gates']==3200*6*len(states) and COUNTS['global_vector_gates']==9*len(states) and COUNTS['saved_global_differences']==7*len(states)
assert all(sha(p)==v for p,v in PINS.items())
report=dict(schema_version='cycle007-actual-saved-math-readonly-review-1.0',status='pass',numerical_reference_not_reexecuted=True,
 stage=STAGE.relative_to(ROOT).as_posix(),baseline_commit=inventory['baseline_commit'],
 production=dict(force_started=counts['force_calls'],force_completed=counts['force_calls_completed'],tangent_started=counts['tangent_calls'],tangent_completed=counts['tangent_calls_completed'],solver_invocations=counts['solver_invocations'],accepted_states=len(states),helper_seconds=receipt['elapsed_seconds'],outer_seconds=production['elapsed_seconds'],first_force_range_input=receipt['first_force_range_input'],first_tangent_range_input=receipt['first_tangent_range_input'],counter_accounting=accounting),
 independent_reference=dict(status=summary['status'],actual_terminal_exit_code=launch['exit_code'],fresh_HP_started=summary['HP_calls_started'],fresh_HP_completed=summary['HP_calls_completed'],accepted_states=len(states),original_checks_completed=summary['checks_completed'],helper_seconds=summary['elapsed_seconds'],helper_peak_bytes=summary['sampled_peak_RSS_bytes'],outer_seconds=launch['elapsed_seconds'],outer_tree_peak_bytes=launch['peak_sampled_tree_RSS_bytes']),
 saved_review_scope=dict(**COUNTS,all_local_global_error_denominator_and_HPagreement_reproduced=True,norm_precision=120,saved_difference_vectors_exact_reproduced=True,
 body_projection='Exact3000-digit saved-global component sums with Inexact trap then enclosing120-digit negation, as in frozen workpiece checker',
 remaining_scalar_and_workpiece_gates='All saved value/limit/HPagreement records checked; no new producer/equation invocation',
 full_reference_fixture_matches_actual_state=True,local_reference_entries_per_component=25600,global_reference_entries_per_component=6642,
 source_closure=68,protocol_bindings=len(protocol['bindings']),unique_files_SHA_checked=len(PINS),all_end_SHA_unchanged=True,
 original_checks='Original reference identity/metadata/math assertion count is recorded dynamically; this saved reviewer rechecks enumerated numerical and identity evidence, not all original assertions',
 CSC_storage_qualification=dict(original_total_tensor_coefficients=ne*64*len(states),scope='Original assembly checks retained, matrix files SHA/raw fields verified; no new assembly or CSC action'),
 HP_energy='Archived analytic reference output only; candidate auxiliary energy absent and not independently qualified'),
 gates=GATES,maximum_saved_errors=MAX,accepted_states=STATE_RECORDS,requested_targets_mm=targets,
 identity={name:sha(STAGE/name) for name in ('input_inventory.json','source_freeze.json','protocol.json','execution_receipt.json','production_launch.json','reference_launch.json','result/result.json','reference/summary.json','reference/lifecycle.json')},
 scope=summary['qualification'],restrictions=['Only saved NumPy arrays and Decimal strings read; no production or HP reference imports',
 'No new force/tangent/action consumer/constitutive HP/solver/assembly/scatter/geometry/plot/test evaluation',
 'One PORT direction and deltaR=0, not all matrix columns','No auxiliary energy, stress HP, old rejected trial/T25, pressure/contact/clamp/H2/H3/HF5 qualification'],
 reviewer_new_calls={k:0 for k in ('force','tangent','consumer','HP','solve','assembly','scatter','geometry','plot','test')},elapsed_seconds=perf_counter()-STARTED)
with OUT.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status='pass',output=str(OUT),sha256=sha(OUT),counts=COUNTS,elapsed_seconds=report['elapsed_seconds']),ensure_ascii=False),flush=True)
