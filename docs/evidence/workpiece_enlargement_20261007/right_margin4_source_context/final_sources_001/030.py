"""Source/closed-JSON plan note, no HF imports or candidate execution."""
import ast
import json
from hashlib import sha256
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT=Path('D:/hf-margin4-author-20261007')
BASE=ROOT/'lf_data_preparation/native_workpiece_001'
source_paths=[ROOT/'hf_repo/src/hf_eval/analysis_domain.py',ROOT/'hf_repo/src/hf_eval/native_project.py',
    BASE/'right_margin_preparation_001/author/prepare_right_margin.py',BASE/'right_margin_preparation_001/author/build_right_margin_card.py']
sha=lambda p:sha256(p.read_bytes()).hexdigest()
for path in source_paths:
    content=path.read_text(encoding='utf-8');ast.parse(content);compile(content,str(path),'exec')
protocol_path=BASE/'right_margin_preparation_001/preparation_protocol.json'
geometry_path=BASE/'right_margin_cycle_001/run_001/result/model/source_geometry/geometry.json'
model_path=BASE/'right_margin_cycle_001/run_001/result/model/model.json'
protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
geometry=json.loads(geometry_path.read_text(encoding='utf-8'))
model=json.loads(model_path.read_text(encoding='utf-8'))
assert geometry['grid']['shape_yx']==[40,82] and geometry['grid']['extent_mm']==[82.,40.]
assert geometry['processing']['whole_grid_is_LF_native'] is False
assert len(geometry['provenance']['hf_analysis_domain_derivations'])==1
assert geometry['provenance']['hf_analysis_domain_derivations'][0]['old_grid']['shape_yx']==[40,80]
assert model['task']['background_symmetry']['points_mm']==[[0.,40.],[82.,40.]]
assert model['task']['regularization']==dict(alpha=1e-6,length_mm=80.)
assert sha(source_paths[0])=='f0929fb8949ca3155b32badf8eabe4b6a563a2541a220a6616c96efc26f179e6'
counts=dict(cells=40*84,nodes=41*85,dofs=2*41*85,solid_cells=1086,medium_cells=40*84-1086,
    solid_incident_nodes=1337,fixed_dofs=450+2,free_dofs=2*41*85-452)
assert counts==dict(cells=3360,nodes=3485,dofs=6970,solid_cells=1086,medium_cells=2274,solid_incident_nodes=1337,fixed_dofs=452,free_dofs=6518)
report=dict(status='feasible_static_plan_only',blocking_findings=[],baseline_commit='3305fe0c3a640bf22e0f89ea4386a41bdef96aa4',
    source_and_closed_metadata_pins={str(p):sha(p) for p in source_paths+[protocol_path,geometry_path,model_path]},
    physical_delta='Use unchanged API on qualified82mm HF-derived geometry, adding2 more passive-medium columns to84mm. Total body-right margin4mm, incremental margin2mm.',
    necessary_wrapper_adaptations=[
        'Choose actual right_margin_cycle_001 parent model/task/direction/sourcegeometry and its completed production/reference source identities; do not start from80mm baseline or borrow its equilibrium.',
        'Keep original80to82 derivation element byte-equivalent, append82to84 derivation with old_shape40x82/new40x84,parent_slice[[0,40],[0,82]],right_columns2,margin_mm2. Declare cumulative rightmedium margin4 separately.',
        'Keep LFv2 original80mm provenance/native masks/tags as historical source and whole_grid_is_LF_nativeFalse; no converter contract relaxation, resampling or LF optimization.',
        'Compare full82-column parent masks and model fields: cell j*82+i maps to j*84+i; node j*83+i maps to j*85+i; dof2node+component. Include alreadyadded80to82 medium columns, not onlyoriginal80.',
        'Rebuild connectivity/edofs/material masks/solid/body/constraint indices and free list. Added columns82,83 passivevoid only; added lam/mu/gamma equal original medium.',
        '10 operator/scalar fields raw exact including kr,grad,hessian,points,weights,hx,hy,thickness,kout,force_scale;17 array/index fields physically mapped across fullparent82.',
        'Extend only appliedtask backgroundtop endpoint82to84; preserve LF/source background80 history and entity/support tags. Addedtopuy expected6967/6969; fixed452/free6518 are expected, not actual.',
        'Keep E1/nu.3/plane-strain/thickness20,gamma1e-6,alpha1e-6,Lr80 andkr raw; do not substitute domainLx84 as regularization length.',
        'Keep fixedsquare center71/40/side18 physicalbox62..80 x31..40. Expectedbody162cells/190nodes/380DOF/19top overlap, no new body/solid/port/support sharing.',
        'Port coordinates unchanged: inputx0,y38..40 and outputx80,y28..30 with.25/.5/.25 weights. Rebuild6970 direction=maxnormalizedbin, allmergedfixedzero, deltaR0. Tip remains coordinate80/30; expectednode2630, no hardcoded tip in observer.',
        'Original builder inherits current25 HFcore alreadyincludinganalysis_domain; update old24 assertion and avoid duplicate API role. Unchanged API/CLI/test source pins and closed5test proof may be reused as API evidence, no test rerun or newequilibrium labels.',
        'New preparation stage/baseline/current sources/protocol/helper pins and once-first-error stop rule; never overwrite/reopen existing preparation/production/reference/view cards.'],
    expected_only=dict(grid_shape_yx=[40,84],extent_mm=[84.,40.],counts=counts,body_counts=[162,190,380,19],tip_reference_mm=[80.,30.],tip_node=2630,
        input_nodes=[3230,3315,3400],output_nodes=[2460,2545,2630],added_top_uy_dofs=[6967,6969]),
    stage_limits=dict(prepare_helper_seconds=120,prepare_outer_seconds=150,sampled_RSS_bytes=8*1024**3,invocations=1,
        scope='One new geometry/model construction and writers plus mappeddirection;0F/T/solver/HP/JIT/LFoptimization, no equilibrium qualification.'),
    future_cost_basis=dict(production_predecessor_helper_seconds=2485.747854700079,element_ratio=3360/3280,
        estimate_seconds=2485.747854700079*(3360/3280)*1.5+90,proposed_window_seconds=[4500,4560],
        reference_predecessor_helper_seconds=554.0963570999447,
        reference_scope='Freeze only after actual full newproduction; use actualN rather than assuming24 and fresh2N HP. Size/cost extrapolation is an estimate, not a pass or completion promise.'),
    planned_scientific_gates='Inherited F/T/controller/J/Armijo/convergence/HP gates and force definitions remain unchanged; only fresh newcase inputs and dimensions adapt after actual preparation passes.',
    qualification='No candidate run, new count, newequilibrium or sensitivity/convergence result is established by this static note.',
    activity=dict(candidate_imports=0,NPZ_array_reads=0,constructors=0,F_T_solver_HP=0,geometry_nodal_render=0,formal_writes=0))
path=OUT/'margin4_stage_static_note.json'
path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],file=str(path),sha256=sha(path),production_estimate_seconds=report['future_cost_basis']['estimate_seconds']),ensure_ascii=False))
