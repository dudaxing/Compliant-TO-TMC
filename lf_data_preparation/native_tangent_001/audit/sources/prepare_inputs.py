"""Prepare two dimensionless directions on one saved checker state; no mechanics."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    source = json.loads((ROOT / 'lf_data_preparation/native_force_001/input_inventory.json').read_text(encoding='utf-8'))
    prior = next(row for row in source['cases'] if row['alias'] == 'gripper_canonical' and row['state_name'] == 'checker')
    with np.load(ROOT / prior['prior_model_file'], allow_pickle=False) as archive:
        model = {name: archive[name] for name in archive.files}
    with np.load(ROOT / prior['state_file'], allow_pickle=False) as archive:
        state = {name: archive[name] for name in archive.files}
    ny, nx = 40, 80
    i, j = np.meshgrid(np.arange(nx+1), np.arange(ny+1))
    directions = {}
    for name, component, phase in (('vx_stripe', 0, i), ('vy_checker', 1, i+j)):
        value = np.zeros(len(state['lift']))
        value[component::2] = (phase % 2).ravel()
        value[model['fixed_dofs']] = 0.
        directions[name] = value
    path = STAGE / 'directions.npz'
    with path.open('xb') as stream:
        np.savez_compressed(stream, **directions)
    edofs = (2*model['connectivity'][..., None]+[0, 1]).reshape(-1, 8)
    common = b''.join(model[name].tobytes() for name in ('kr', 'grad', 'hessian', 'weights'))
    groups = []
    for name, direction in directions.items():
        classes = {}
        for e, dofs in enumerate(edofs):
            key = common + state['lift'][dofs].tobytes() + state['fluctuation'][dofs].tobytes()
            key += model['lam'][e:e+1].tobytes() + model['mu'][e:e+1].tobytes() + direction[dofs].tobytes()
            classes.setdefault(key, []).append(e)
        if len(classes) > 64 or sum(map(len, classes.values())) != len(edofs):
            raise RuntimeError('Unexpected direction input class bound')
        groups.append(dict(name=name, file=path.relative_to(ROOT).as_posix(), sha256=digest(path),
            array_sha256=sha256(direction.tobytes()).hexdigest(), exact_input_classes=len(classes),
            class_member_counts={sha256(key).hexdigest(): len(members) for key, members in classes.items()},
            units='dimensionless nodal shape; perturbation parameter in mm', fixed_dofs_exactly_zero=True))
    keys = ('alias', 'geometry_file', 'geometry_file_sha256', 'geometry_npz_file', 'geometry_npz_sha256',
            'geometry_id', 'task_file', 'task_file_sha256', 'prior_model_file', 'prior_model_sha256',
            'state_file', 'state_file_sha256', 'elements', 'dofs')
    case = {key: prior[key] for key in keys}
    case.update(state_name='checker', result_directory='result', directions=groups)
    inventory = dict(schema_version='native-tangent-input-inventory-1.0',
        baseline_commit='8373a9bde066a98d0514d9bbc78a425735be17e2', cases=[case],
        scope='One coarse saved supplied-displacement state; two directions; no equilibrium or task actuation',
        physical_authority='exact D(lift)+D(fluctuation); lift fixed during differentiation',
        matrix_semantics='K_ij = d f_i / d w_j, N/mm, full DOFs, unsymmetrized',
        matrix_coverage='All local entries and CSC assembly; HP directional verification only for the two declared directions',
        directions_definition=dict(vx_stripe='vx=ix%2,vy=0', vy_checker='vx=0,vy=(ix+iy)%2',
            fixed_DOFs='Zeroed on the actual merged fixed set'),
        thresholds=dict(total='1e-10', material='1e-9', regularization='1e-9', HP80_HP120='1e-40'),
        denominator='max(norm(reference Jv),1e-10 N/mm), separately per element/global/CSC component',
        execution_limits=dict(production_seconds=120, reference_seconds=120, sampled_RSS_bytes=8*1024**3),
        recovery='One public CLI replay under 120s/8GiB; compare full tensor/model/state/CSC storage, no new HP')
    with (STAGE / 'input_inventory.json').open('x', encoding='utf-8', newline='\n') as output:
        json.dump(inventory, output, indent=2)
        output.write('\n')
    print(json.dumps(dict(classes=[row['exact_input_classes'] for row in groups],
        HP_calls_planned=2*sum(row['exact_input_classes'] for row in groups), tangent_calls=0, force_calls=0)))


if __name__ == '__main__':
    main()
