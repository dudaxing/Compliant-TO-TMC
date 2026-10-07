"""Source/JSON-only parameter and boundary interpretation; no experiment authorization."""
from pathlib import Path
import hashlib
import json
BASE=Path('D:/hf-workpiece-enlarge-author-20261007')
REPO=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
files=[REPO/'hf_repo/src/hf_eval/native_project.py',REPO/'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
       REPO/'lf_data_preparation/native_workpiece_001/enlarged_square_projection_001/run_001/task.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
task=json.loads(files[2].read_text(encoding='utf-8'))
report=dict(status='source_only_physical_inference',source_pins={str(p):sha(p) for p in files},
    actual_task=dict(material=task['material'],third_medium=task['third_medium'],regularization=task['regularization'],
        workpiece=task['workpiece'],background_symmetry=task['background_symmetry']),
    source_facts=[
        'native_project assigns factors=where(original solid,1,gamma), multiplying lambda_s and mu_s by this factor. Workpiece is a fixed kinematic overlay and preserves original phase arrays.',
        'kr=alpha*Lr^2*(kappa_s+4mu_s/3) is independent of gamma; native mechanical Hu residual is assembled on the full domain and multiplied by exp(-5J).',
        'Regularization length is an explicitly physical mm task value; construction comments require it remain physical across grids rather than silently become the analysis width.',
        'Fixed groups are solid support, solid symmetry, explicit top-background uy and all workpiece ux/uy. No automatic additional right-boundary Dirichlet group is created.',
        'The current body box ends atx80, the actual domain edge: no neighboring medium cells exist to its right. Body-edge nodes are fixed by the overlay; other uncovered right-edge nodes are constrained only when an explicit original group contains them.',
    ],
    inferences=[
        'Changing gamma alone while all other geometry/grid/constraints/alpha/Lr settings stay identical isolates parameter sensitivity of this finite boundary task; it cannot eliminate or measure domain-boundary influence.',
        'At a fixed displacement field gamma changes the medium material contribution while kr remains unchanged. A newly equilibrated field generally changesF/Hu/J too, so its material and Hu forces need not scale directly with gamma.',
        'Reported material/Hu/total components identify weak-force components, not independent contact pressure or full physical-source separation.',
    ],
    suggested_order=dict(
        transferable_force_priority='First compare added right-medium margin while preserving actual mechanism/workpiece coordinates, local1mmgrid, ports/support, E/nu/gamma/alpha and Lr80; then compare gamma on the chosen domain.',
        low_implementation_cost_priority='A gamma-only task may precede padding as a clearly domain-limited exploratory sensitivity, but cannot replace the right-margin comparison or establish boundary-independent clamp force.',
        matching_requirement='Moving or shrinking the body to gain margin changes the local contact geometry; a cleaner domain comparison keeps the body pose and extends passive medium. Refinement should keep the same physical geometry/ports/constraints and physical Lr.',
        no_permission_decision=True),
    limitations=['This is source-based reasoning, not a new equilibrium prediction, validated convergence result, executable card or permission decision. No current running reference output is read.'],
    activity=dict(candidate_imports=0,numeric_array_reads=0,F=0,T=0,solver=0,HP=0,geometry_API=0,render=0,new_cards=0,formal_writes=0))
(BASE/'physical_parameter_order_source_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],report_sha256=sha(BASE/'physical_parameter_order_source_review.json'))))
