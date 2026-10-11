"""Record the root agent's completed inspection of the two original PNGs.

Ordinary PNG header/hash reads only. No rendering, numerical reconstruction,
candidate import, NPZ decoding or image modification.
"""
from pathlib import Path
from hashlib import sha256
import json
import struct

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
RUN = ROOT / REL / 'run_001'
OUTPUT = EXT / 'visual_review.json'

def image_record(name, expected, observations, limitations):
    raw = (RUN / name).read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR'
    width, height = struct.unpack('>II', raw[16:24])
    assert (width, height) == expected
    return dict(path=f'{REL}/run_001/{name}', sha256=sha256(raw).hexdigest(),
                original_width=width, original_height=height,
                inspected_original_pixels=True, observations=observations,
                limitations=limitations)

report = dict(
    status='pass_actual_images_inspected_with_limits',
    source_commit='eb68c00d50b28de89a475c18a0879be4a4482f68',
    reviewer='root agent, actual original-pixel view_image inspection in this execution turn',
    recorded_date='2026-10-11',
    images=[
        image_record('Q1_Hu_endpoint_actions.png', (2400, 1500), [
            'Two rows show the original loading 0.85 and 1.20 mm states; three columns show reference cells 10371, 10407 and 10408.',
            'Reference coordinates in mm, signed N labels and independent arrow scales are visible.',
            'Red selected body vertices and other grey-blue vertices are distinguished. Other vertices are negative local covectors, not workpiece loads.',
            'Cell 10407 has opposite nonzero selected TL/TR actions; the two corner-only cells have one selected vertex each.',
            'Cell, state, displacement and numerical labels are legible in the original image.'
        ], [
            'Some arrows cross numerical text blocks, particularly in the lower middle/right panels. Text remains legible at original resolution; no redraw was performed.',
            'Arrow lengths use an independent scale in each panel. Compare absolute magnitudes using signed labels and selected_endpoints.csv.',
            'This is a reference-coordinate force-source diagram, not a newly computed deformation or a continuous pressure field.'
        ]),
        image_record('Hu_owner_node_comparison.png', (2400, 1800), [
            'Two states and signed Fx/Fy panels have visible state/displacement, N units and category labels.',
            'Dotted separators distinguish five owner-role columns, two corner owners plus the original whole result, and seven original node-category columns.',
            'Zero side/body owner totals coexist with nonzero original boundary-node categories; this difference between partitions is visible.',
            'Bars retain signed numerical annotations and all axis labels fit the original canvas.'
        ], [
            'Very small bars are difficult to distinguish near zero; annotations and CSV preserve their values.',
            'Panel scales are independent. Bar heights alone cannot compare magnitudes between panels.',
            'The three column blocks are distinct comparisons, not one additive partition. Corner-only owners do not mean physical-corner node categories.',
            'No continuous total pressure or effective-grip qualification is established by these plots.'
        ])
    ],
    actual_deformation_reference='functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif',
    actions=dict(new_candidate_runs=0, new_NPZ_decodes=0,
                 new_force_tangent_HP_equilibrium_calls=0,
                 new_integrals_fsum_or_projection=0, new_image_renders=0,
                 new_image_modifications=0),
    scope='Manual visual readability/meaning review of actual existing pixels; no new scientific acceptance gate.',
    entire_HF5_complete=False
)
with OUTPUT.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(dict(status=report['status'], images=len(report['images']),
                     sha256=sha256(OUTPUT.read_bytes()).hexdigest())))
