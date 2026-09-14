"""Inspect frozen prerequisite evidence and document the conditional HF3 decision."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy import sparse

root = Path(__file__).resolve().parents[1]
out, repo = root/'hf3_results', root/'hf_repo'
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec = repo/'configs/hf3/validation_spec.json'
freeze = read(out/'production_source_freeze.json')
for name, digest in freeze['files'].items():
    assert sha(repo/'src/hf_eval'/name) == digest
evidence = [out/'production_source_freeze.json', out/'regression_final.xml',
    out/'near_zero_v3_final_001/summary.json', out/'small_kernel_v3_001/summary.json',
    out/'strong_kernel_v3_001/summary.json', out/'bridge_001/summary.json', out/'bridge_hp_001/summary.json',
    out/'detached/summary.json', out/'detached_receipt.json']
suite = ET.parse(out/'regression_final.xml').getroot().find('testsuite')
assert int(suite.attrib['failures']) == int(suite.attrib['errors']) == 0
assert int(suite.attrib['tests']) - int(suite.attrib['skipped']) == 311
for path in evidence[2:-1]:
    assert read(path)['status'] == 'pass', path
assert read(out/'detached_receipt.json')['dataset_files_unchanged']
assert read(out/'near_zero_v3_final_001/summary.json')['kernel_sha256'] == freeze['files']['tmc_kernel.py']
bridge = read(out/'bridge_001/summary.json')
assert bridge['implementation_sha256'] == freeze['source_sha256']
hp = read(out/'bridge_hp_001/summary.json')
assert hp['completed_states'] == hp['expected_states'] == 6 and hp['failed_states'] == 0
for path in (out/'bridge_hp_001').glob('run_*/state_????.json'):
    row = read(path)
    assert row['precision_crosscheck']['status'] == 'pass'
    evidence.append(path)
interpretation = {}
for family, case in bridge['cases'].items():
    bias = case['linear_reference']['A_vs_B_model_bias']
    assert bias['status'] == 'below_diagnostic_flag_threshold'
    assert not any(bias['signed_response_changes'].values())
    folder = out/'bridge_001'/family/'linear'
    with np.load(folder/'unit_responses.npz', allow_pickle=False) as z:
        u, R = z['K0_u'], float(z['K0_R'])
    components = {}
    for name in ('solid_material', 'medium_material', 'HuHu'):
        path = folder/f'K0_{name}_full.npz'
        K = sparse.load_npz(path)
        components[name] = float(u @ (K @ u))/R
        evidence.append(path)
    assert components['solid_material'] > 0.99
    interpretation[family] = dict(initial_stiffness_bias=bias['comparisons']['input_stiffness']['relative_error'],
        output_gain_bias=bias['comparisons']['output_gain']['relative_error'],
        component_virtual_work_fraction_at_K0_solution=components,
        interpretation='The saved unit K0 solution retains more than 99% solid-material virtual work; medium/HuHu do not dominate initial input stiffness. Signs unchanged and all pilot bias flags below 5%. This is an initial-state interpretation, not a finite-path physical-accuracy guarantee.')
jobs = [read(p) for p in (out/'resource_jobs').glob('*.json')]
used_hp = sum(x['wall_seconds'] for x in jobs if x['category'] == 'hp')
assert used_hp < 200
assert not any(x['category'].endswith('_path') and x['process_started'] for x in jobs)
gate = dict(status='front_gate_pass_full_paths_authorized', recorded_utc=datetime.now(timezone.utc).isoformat(),
    authorization='User approved continuing the proposed HF3 plan; each original 40-target path may run once after these prerequisites. No further permission is needed for this conditional step.',
    source_sha256=freeze['source_sha256'], spec_sha256=sha(spec), model_interpretation=interpretation,
    previous_bridge_hp_seconds=used_hp, remaining_hp_seconds=600-used_hp,
    path_limit_each_seconds=480, full_paths_each_maximum_attempts=1, HF4_authorized=False,
    evidence=[dict(relative_to_gate=p.relative_to(out).as_posix(), sha256=sha(p)) for p in evidence])
path = out/'full_path_gate.json'
assert not path.exists()
path.write_text(json.dumps(gate, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(status=gate['status'], interpretation=interpretation), ensure_ascii=False))
