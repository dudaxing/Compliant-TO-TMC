"""Prepare six supplied displacement tests from saved models; no mechanics."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
AMPLITUDE = 2.0**-10


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    previous = json.loads((ROOT / 'lf_data_preparation/native_model_001/input_inventory.json').read_text(encoding='utf-8'))
    cases = []
    for source in previous['cases']:
        alias = source['alias']
        model_file = ROOT / f'lf_data_preparation/native_model_001/models/{alias}/model.npz'
        with np.load(model_file, allow_pickle=False) as archive:
            model = {name: archive[name] for name in archive.files}
        indices = np.rint(model['coordinates'] / [float(model['hx']), float(model['hy'])]).astype(np.int64)
        for name in ('stripe', 'checker'):
            lift = np.zeros(len(model['b_in']), dtype=np.float64)
            fluctuation = np.zeros_like(lift)
            phase = indices[:, 0] if name == 'stripe' else indices.sum(axis=1)
            fluctuation[0::2] = AMPLITUDE * (phase % 2)
            fluctuation[model['fixed_dofs']] = 0.
            state_path = STAGE / 'states' / alias / (name + '.npz')
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with state_path.open('xb') as stream:
                np.savez_compressed(stream, lift=lift, fluctuation=fluctuation)
            # Full raw local inputs: no change of origin or displacement.
            classes = {}
            public = b''.join(model[key].tobytes() for key in ('kr', 'grad', 'hessian', 'weights'))
            edofs = (2 * model['connectivity'][..., None] + [0, 1]).reshape(-1, 8)
            for element, dofs in enumerate(edofs):
                key = (public + lift[dofs].tobytes() + fluctuation[dofs].tobytes()
                       + model['lam'][element:element+1].tobytes() + model['mu'][element:element+1].tobytes())
                classes.setdefault(sha256(key).hexdigest(), []).append(element)
            if len(classes) > 32 or sum(map(len, classes.values())) != len(edofs):
                raise RuntimeError('Manufactured raw-input class bound differs')
            row = {key: source[key] for key in ('alias', 'geometry_file', 'geometry_file_sha256',
                    'geometry_npz_sha256', 'geometry_id', 'task_file', 'task_file_sha256')}
            row.update(state_name=name, geometry_npz_file=str(Path(source['geometry_file']).with_suffix('.npz')).replace('\\', '/'),
                prior_model_file=model_file.relative_to(ROOT).as_posix(), prior_model_sha256=digest(model_file),
                state_file=state_path.relative_to(ROOT).as_posix(), state_file_sha256=digest(state_path),
                displacement_amplitude_mm=AMPLITUDE, exact_input_classes=len(classes), elements=len(edofs), dofs=len(lift),
                result_directory=f'results/{alias}/{name}', fixed_dofs_exactly_zero=True,
                class_member_counts={key: len(value) for key, value in classes.items()})
            cases.append(row)
    inventory = dict(schema_version='native-force-input-inventory-1.0',
        baseline_commit='524ffc0998f7dff578df890f45a97bc4b7c9928a', cases=cases,
        scope='Six supplied displacement tests; not equilibrium, task actuation, contact or study qualification',
        physical_authority='exact D(lift)+D(fluctuation)', displacement_amplitude_mm=AMPLITUDE,
        stripe='ux=a*(ix%2), uy=0, lift=0; actual fixed DOFs set to zero; piecewise affine, Hu=0',
        checker='ux=a*((ix+iy)%2), uy=0, lift=0; actual fixed DOFs set to zero; Hu nonzero',
        global_force_thresholds=dict(total='1e-11', material='1e-9', regularization='1e-9'),
        local_force_thresholds=dict(total='1e-11', material='1e-9', regularization='1e-9'),
        hp80_hp120_threshold='1e-40',
        force_scale='max(norm(total internal force), 1e-8*Et*max(a,1e-6)); component=max(norm(component),1e-12*SF)',
        local_scale='Same formula on each 8-DOF element, never the global force norm',
        execution_limits=dict(production_seconds=120, reference_seconds=300, sampled_RSS_bytes=8*1024**3),
        recovery='After push, independently replay six CLI force calls once in new directories; no new HP; compare all arrays exactly')
    with (STAGE / 'input_inventory.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(inventory, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps(dict(states=len(cases), elements=sum(row['elements'] for row in cases),
        classes=[row['exact_input_classes'] for row in cases], force_calls=0, HP_calls=0)))


if __name__ == '__main__':
    main()
