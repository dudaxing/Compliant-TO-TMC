"""Record actual terminal handle and the three already completed PNG inspections."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_extension_003'
STAGE = ROOT/REL
BASE = '3cf11e92bedb791855c7b01d314668eba1116ac6'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
    launch = read(STAGE/'production_launch.json')
    helper = read(STAGE/'run_001/execution_receipt.json')
    assert launch['status'] == helper['status'] == 'pass' and launch['invocations'] == 1
    assert launch['exit_code'] == 0 and launch['stop_reason'] is None and launch['all_bindings_unchanged'] is True
    assert launch['elapsed_seconds'] == 606.2997859999887
    assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    stamp = datetime.now(timezone.utc).isoformat()
    confirmation = dict(card='M-UNLOAD1',source_baseline_commit=BASE,recorded_utc=stamp,
        unified_exec_session_id=20354,root_observed_same_session_terminal=True,tool_terminal_exit_code=0,
        execution_status='pass',execution_closed=True,
        outer_sha256=sha(STAGE/'production_launch.json'),execution_receipt_sha256=sha(STAGE/'run_001/execution_receipt.json'),
        actual_HP_tests_new_solver_or_plot_calls_by_observation=0)
    write_new(STAGE/'author/root_terminal_confirmation.json',confirmation)
    image_rows = []
    for filename in ('comparison.png','distances_forces.png','peak_fields.png'):
        name = REL+'/run_001/view/'+filename
        producer = helper['outputs'][name]
        assert (ROOT/name).stat().st_size == producer['bytes']
        image_rows.append(dict(path=name,producer_declared_sha256=producer['sha256'],bytes=producer['bytes'],
            view_image_calls=1,detail='original',title_axes_labels_and_legends_legible=True))
    qa = dict(card='M-UNLOAD1',status='pass_display_with_documented_scale_limits',recorded_utc=stamp,
        inspected_by='root',images=image_rows,actual_view_image_calls=3,
        new_GIF_postrun_decode=0,render_retry_or_replot=0,scientific_postrun_array_gzip_CSV_hash_or_decode=0,
        observed_segment_PEAK_input_mm=1.1,observed_LAST_input_mm=1.05,visual_mirror_only=True,deformation_scale=1,
        observations=[
            'Three images display the actual successful suffix; segment PEAK denotes the 1.10 start, not the original 1.20 loading peak.',
            'The unsigned bottom gap in micrometres shares the distance chart scale with the roughly17.7mm left distance; use the zoom label and numerical table for small gap changes.',
            'The small Hu Fy curve is near zero on the total-force scale and partly under the force legend; numerical component values remain in the original summary and result table.',
            'The field image is the 1.10 segment-PEAK snapshot. Hu Frobenius colour is distinct from the maximum absolute Hu component reported in the scalar summary.'
        ],pressure_effective_grip_or_complete_release_qualified=False)
    write_new(STAGE/'author/pixel_QA.json',qa)
    print(json.dumps(dict(status='actual_terminal_and_three_PNG_observations_recorded',
        terminal_session=20354,pixel_QA_calls=3,new_science=0),ensure_ascii=False))


if __name__ == '__main__': main()
