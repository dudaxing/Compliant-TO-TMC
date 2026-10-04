"""Read terminal receipts and saved files only; no evaluator or measurement."""
from pathlib import Path
from hashlib import sha256
import json
from PIL import Image

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
VIEW = ROOT/'functional_views/native_workpiece_cycle010_20261004'
REF2 = MECH.with_name('coarse_square_cycle010_ref_002')
REF3 = MECH.with_name('coarse_square_cycle010_ref_003')
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
digest = lambda p: sha256(p.read_bytes()).hexdigest()

def main():
    stages = [(MECH,'prepare',None),(MECH,'production',MECH/'execution_receipt.json'),
        (MECH,'reference',MECH/'reference/lifecycle.json'),
        (REF2,'tests',REF2/'tests_001/tests_receipt.json'),
        (REF2,'reference',REF2/'reference/lifecycle.json'),
        (REF3,'reference',REF3/'reference/lifecycle.json'),
        (VIEW/'region_saved_001','measure',VIEW/'region_saved_001/measurement_001/regions_measurements.json'),
        (VIEW/'nodal_saved_001','observe',VIEW/'nodal_saved_001/observation_001/summary.json'),
        (VIEW/'saved_render_001','render',VIEW/'saved_render_001/render_receipt.json'),
        (VIEW/'saved_render_001','node_render',VIEW/'saved_render_001/nodes_001/key_states.json'),
        (VIEW/'saved_render_001','geometry_render',VIEW/'saved_render_001/geometry_001/view_metadata.json')]
    rows = []
    for stage,phase,helper_path in stages:
        launch = read(stage/(phase+'_launch.json'))
        assert launch['invocations'] == 1 and launch['all_bindings_unchanged']
        helper = read(helper_path) if helper_path else {}
        rows.append(dict(stage=stage.relative_to(ROOT).as_posix(),phase=phase,launch=launch,
            helper_receipt=helper_path.relative_to(ROOT).as_posix() if helper_path else None,
            helper_elapsed_seconds=helper.get('elapsed_seconds'),
            helper_peak_RSS_bytes=helper.get('sampled_peak_RSS_bytes',helper.get('peak_sampled_RSS_bytes',helper.get('sampled_self_peak_RSS_bytes')))))
    result = read(MECH/'result/result.json')
    before = MECH.with_name('coarse_square_cycle_009')/'result'
    same = []
    for index in range(5):
        for name in ('state.npz','forces.npz','tangents.npz','total_matrix.npz'):
            old,new = before/f'accepted/{index:03d}'/name,MECH/f'result/accepted/{index:03d}'/name
            assert old.read_bytes() == new.read_bytes()
            same.append(dict(path=new.relative_to(ROOT).as_posix(),sha256=digest(new)))
    gifs = []
    for name in ('animation_001/cycle010_actual_path.gif','nodes_001/nodal_force_path.gif'):
        path = VIEW/'saved_render_001'/name
        with Image.open(path) as image:
            frames = image.n_frames; durations = []
            for index in range(frames): image.seek(index); durations.append(image.info.get('duration'))
        assert frames == len(result['states']) == 12
        gifs.append(dict(path=path.relative_to(ROOT).as_posix(),frames=frames,durations_ms=durations,sha256=digest(path)))
    value = dict(status='saved_file_review_pass',phase_receipts=rows,
        first5_states_four_complete_archives_byte_identical_to009=same,
        gifs=gifs,new_mechanics_HP_solver_geometry_nodal_observation_calls=0,
        scope='File identities/receipt reads/GIF metadata only, not another scientific qualification')
    with (AUTHOR/'root_delivery_facts.json').open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False); stream.write('\n')
    print(json.dumps(dict(status=value['status'],phases=len(rows),same_archives=len(same),gifs=gifs)))

if __name__ == '__main__': main()
