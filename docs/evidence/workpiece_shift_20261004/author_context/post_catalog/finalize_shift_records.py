"""Collect closed saved evidence and write living records; no mechanics imports."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--master', required=True)
    p.add_argument('--fit', required=True)
    a = p.parse_args(); root = a.repo.resolve(); pins = {}
    def read(name):
        q = root/name; pins[name] = sha256(q.read_bytes()).hexdigest()
        return json.loads(q.read_text(encoding='utf-8'))
    master = read(a.master+'/view/view.json'); fit_view = read(a.fit+'/view/fit_view.json')
    assert master['status'] == fit_view['status'] == 'pass'
    stages = [('old010', 'coarse_square_cycle_010', '', 'coarse_square_cycle010_ref_003'),
              ('pose002', 'shift_square_pose_002', '/run_001', 'shift_square_pose_002'),
              ('soft001', 'shift_square_soft_001', '/run_001', 'shift_square_soft_001')]
    cases = {}
    for label, name, run, ref_name in stages:
        control = 'lf_data_preparation/native_workpiece_001/'+name
        directory = control+run
        result_file = directory+'/result/result.json'
        r = read(result_file); e = read(directory+'/execution_receipt.json')
        launch = read(control+'/production_launch.json')
        ref_control = 'lf_data_preparation/native_workpiece_001/'+ref_name
        ref = read(ref_control+'/reference/summary.json')
        ref_launch = read(ref_control+'/reference_launch.json'); life = read(ref_control+'/reference/lifecycle.json')
        view = read(a.master+'/view/'+label+'/summary.json'); local = read(a.fit+'/view/'+label+'_fit.json')
        assert r['status'] == 'success' and r['path_completed'] and r['unload_endpoint_reached']
        assert all(x['status'] == 'pass' for x in (e, launch, ref, ref_launch, life))
        n = r['accepted_states']; assert ref['accepted_states'] == n and ref['HP_calls_completed'] == 2*n
        peak = max(range(n), key=lambda i: r['states'][i]['d'])
        assert view['reference_available'] and view['accepted_states'] == n and local['index'] == peak
        assert local['state_sha256'] == r['states'][peak]['state_sha256'] == view['rows'][peak]['state_sha256']
        diag = r['path_diagnostics']
        cases[label] = dict(stage=control, result_file=result_file, result_sha256=pins[result_file],
            N=n, actual_d_mm=[x['d'] for x in r['states']], original_targets_mm=r['targets_mm'],
            call_counts=r['call_counts'], newton_history=len(diag['newton_history']), trials=len(diag['trials']),
            failed_attempts=diag['failed_attempts'], linear_diagnostics=len(diag['linear_solve_diagnostics']),
            production=dict(helper_seconds=e['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
                helper_RSS_bytes=e['sampled_peak_RSS_bytes'],tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
                bindings_unchanged=launch['all_bindings_unchanged']),
            reference=dict(fresh_HP=ref['HP_calls_completed'],checks=ref['checks_completed'],
                helper_seconds=ref['elapsed_seconds'],outer_seconds=ref_launch['elapsed_seconds'],
                helper_RSS_bytes=ref['sampled_peak_RSS_bytes'],tree_RSS_bytes=ref_launch['peak_sampled_tree_RSS_bytes'],
                bindings_unchanged=ref_launch['all_bindings_unchanged']),
            peak=view['rows'][peak], return_to_zero=view['rows'][-1], local_fit=local,
            original_production_qualification={k:r[k] for k in ('equilibrium_qualified','independent_HP_qualified','HF_qualified')})
    output = dict(schema_version='workpiece-shift-softness-summary-1.0', created_utc=datetime.now(timezone.utc).isoformat(),
        status='completed_case_comparison', project_complete=False, cases=cases,
        master_view=a.master+'/view', local_fit_view=a.fit+'/view',
        master_counts={k:master[k] for k in ('geometry_started','geometry_completed','nodal_started','nodal_completed')},
        source_input_bindings=pins, new_F_T_model_solver_HP_calls=0,
        scope='Only closed saved evidence, cached observations and derived Green strain; no new mechanics or qualification',
        pressure_hard_contact_free_clamping_qualified=False)
    destination = root/'docs/evidence/workpiece_shift_20261004/final_comparison.json'
    with destination.open('x',encoding='utf-8') as f: json.dump(output,f,indent=2,ensure_ascii=False,allow_nan=False); f.write('\n')
    print(json.dumps({k:dict(N=v['N'],reference=v['reference'],peak=v['peak'],
        local_strain_max=v['local_fit']['adjacent_solid_Green_principal_max']) for k,v in cases.items()},ensure_ascii=False))


if __name__ == '__main__': main()
