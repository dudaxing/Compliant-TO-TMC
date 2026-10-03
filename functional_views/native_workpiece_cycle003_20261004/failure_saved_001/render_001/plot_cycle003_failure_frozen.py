"""Display the closed cycle003 failure from saved data; no mechanics calls."""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter
import numpy as np
import psutil

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'hf_repo').is_dir())
HELPER = ROOT/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py'
HELPER_SHA = 'd256fe2b1541505cd5315f45c4a50462670a09436ceb91ecc8d01bbb25554169'
PEAK = 0
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def main():
    global PEAK
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'output', 'protocol'): parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    stage, output = args.input.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = dict(status='running', qualification=False, new_calls=dict(force=0, tangent=0, solver=0, HP=0, action_consumer=0, geometry_measurement=0))
    pins = {}
    def checkpoint():
        global PEAK
        info = psutil.Process().memory_info()
        PEAK = max(PEAK, info.rss, getattr(info, 'peak_wset', info.rss))
        if perf_counter()-STARTED > 120 or PEAK > 8*1024**3 or (output.parent/'stop_requested.txt').exists() or (stage/'stop_requested.txt').exists():
            raise RuntimeError('Saved failure-view budget/stop reached; no retry')
    try:
        protocol_file = args.protocol.resolve()
        protocol = json.loads(protocol_file.read_text(encoding='utf-8'))
        pins.update({ROOT/name: value for name, value in protocol['bindings'].items()})
        pins[protocol_file] = sha(protocol_file)
        assert Path(__file__).resolve() in pins and HELPER in pins and sha(HELPER) == HELPER_SHA
        assert all(sha(p) == value for p, value in pins.items()), 'Frozen failure-view bindings changed'
        spec = importlib.util.spec_from_file_location('saved_failure_helpers', HELPER)
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        model, metadata, result, receipt, states, loaded_pins, _ = helper.load_saved(stage)
        pins.update(loaded_pins)
        assert result['status'] == 'failed' and result['failure']['code'] == 'time_limit' and len(states) == 2
        assert [s['record']['d'] for s in states] == [0., .5] and result['targets_mm'] == [0., .5, 0.]
        assert result['loading_peak_reached'] is True and all(result[k] is False for k in ('path_completed', 'unload_endpoint_reached', 'task_target_executed'))
        progress_file = stage/'accepted_progress.jsonl'; pins[progress_file] = sha(progress_file)
        progress = [json.loads(line) for line in progress_file.read_text(encoding='utf-8').splitlines()]
        assert len(progress) == 2
        for i, (item, saved) in enumerate(zip(progress, states, strict=True)):
            assert item['index'] == i and all(item[k] == saved['record'][k] for k in ('d', 'R_input', 'q_in', 'q_out', 'relative_residual', 'state_sha256', 'leg', 'original_target_index'))
            assert item['workpiece'] == saved['record']['workpiece']['force_on_lower_body_N']
        rows, inlet = helper.numerical_rows(model, states)
        diagnostic = result['path_diagnostics']; history, trials = diagnostic['newton_history'], diagnostic['trials']
        checkpoint()
        coords, conn, solid = (model[k] for k in ('coordinates', 'connectivity', 'solid'))
        body = model['workpiece_cells']; medium = ~solid.copy(); medium[body] = False
        u = [(s['state']['lift']+s['state']['fluctuation']).reshape(-1, 2) for s in states]
        color = [np.linalg.norm(v, axis=1)[conn].mean(axis=1) for v in u]
        norm = Normalize(0., max(float(v.max()) for v in color))
        support = np.asarray(metadata['region_metadata']['support']['attached_nodes'], dtype=int)
        out_nodes = np.asarray(metadata['region_metadata']['ports']['output']['nodes'], dtype=int)
        max_force = max(float(np.linalg.norm(s['forces'][k].reshape(-1, 2), axis=1).max()) for s in states for k in ('input_force', 'support_reaction'))
        force_scale = max(max_force, 1e-30)/4.
        fig = plt.figure(figsize=(22, 14), layout='constrained'); grid = fig.add_gridspec(3, 3, height_ratios=[1., .14, 1.])
        def structure(ax, index, scale):
            moved = coords+scale*u[index]
            ax.add_collection(PolyCollection(moved[conn[medium]], array=color[index][medium], cmap='Oranges', norm=norm, edgecolors='none'))
            field = PolyCollection(moved[conn[solid]], array=color[index][solid], cmap='viridis', norm=norm, edgecolors='none')
            ax.add_collection(field)
            ax.add_collection(PolyCollection(coords[conn[solid]], facecolors='none', edgecolors='#999999', linewidths=.15))
            ax.add_collection(PolyCollection(coords[conn[body]], facecolors='#cccccc', edgecolors='#555555', linewidths=.15))
            for nodes, marker, color_name in ((support, '^', '#183a53'), (inlet//2, 'o', '#b84b23'), (out_nodes, 'D', '#8856a7')):
                ax.scatter(*moved[nodes].T, marker=marker, s=32, facecolors='none', edgecolors=color_name, zorder=5)
            if scale == 1:
                for key, nodes, c in (('input_force', inlet//2, '#b84b23'), ('support_reaction', support, '#216a9b')):
                    values = states[index]['forces'][key].reshape(-1, 2)[nodes]
                    ax.quiver(*moved[nodes].T, *values.T, angles='xy', scale_units='xy', scale=force_scale, color=c, width=.004, minlength=0., zorder=6)
                centre = coords[model['workpiece_nodes']].mean(axis=0)
                ax.quiver(*centre, *states[index]['record']['workpiece']['force_on_lower_body_N']['total'], angles='xy', scale_units='xy', scale=force_scale, color='#7b3294', width=.006, minlength=0., zorder=6)
            ax.set(xlim=(54, 80) if scale != 1 else (-4, 84), ylim=(24, 41) if scale != 1 else (-4, 44), aspect='equal', xlabel='x [mm]', ylabel='y [mm]',
                   title=f"Accepted {index}: d={rows[index]['d_mm']:g} mm; actual ×1" if scale == 1 else 'DISPLAY ONLY: accepted peak displacement ×4; no force arrows')
            return field
        panels = [fig.add_subplot(grid[0, i]) for i in range(3)]
        structure(panels[0], 0, 1); field = structure(panels[1], 1, 1); structure(panels[2], 1, 4)
        bar = fig.colorbar(field, ax=panels, fraction=.016, pad=.01); bar.set_label('Mechanism element mean nodal |u| [mm]; medium uses Oranges same range')
        bar.formatter = ScalarFormatter(useOffset=False); bar.update_ticks()
        legend = fig.add_subplot(grid[1, :]); legend.axis('off')
        handles = [Line2D([], [], marker=m, color=c, linestyle='none', label=l) for m,c,l in
                   [('^','#183a53','attached support; model reaction arrows'),('o','#b84b23','mean-input nodes; actuator arrows'),('D','#8856a7','free +y output measurement'),('s','#777777','fixed body overlay; purple resultant ON body')]]
        legend.legend(handles=handles, loc='center', ncol=2, fontsize=10)
        base_ax, trial_ax, text_ax = [fig.add_subplot(grid[2, i]) for i in range(3)]
        boundaries = [i for i,r in enumerate(history) if r['newton_check'] == 1]+[len(history)]
        for a,b in zip(boundaries, boundaries[1:]):
            base_ax.semilogy(np.arange(a+1,b+1), [r['relative_residual'] if r['relative_residual'] > 0 else np.nan for r in history[a:b]], 'o-', label=f"attempt d={history[a]['d']:g} mm")
        base_ax.axhline(result['settings']['tolerance'], color='red', ls='--', label='Original production residual gate')
        base_ax.text(.02,.02,'Initial completed base has exact residual 0 (not on log axis).', transform=base_ax.transAxes, fontsize=9, bbox=dict(facecolor='white',edgecolor='none'))
        base_ax.set(title='Completed Newton BASE observations\nNot an accepted-state trajectory', xlabel='Completed base observation index', ylabel='Relative residual (dimensionless)')
        base_ax.legend(fontsize=9); base_ax.grid(alpha=.2)
        kinds = [('accepted', lambda t:t['accepted'], 'o','#00875f'),('recorded range rejection', lambda t:t.get('reason')=='unsupported_arithmetic_range','x','#c62828'),('other recorded rejection',lambda t:not t['accepted'] and t.get('reason')!='unsupported_arithmetic_range','D','#db8c00')]
        for label, predicate, marker, c in kinds:
            items = [(i+1,t) for i,t in enumerate(trials) if predicate(t)]
            trial_ax.scatter([i for i,t in items],[t['factor'] for i,t in items],label=f'{label}: {len(items)}',marker=marker,color=c,s=36)
        trial_ax.set(yscale='log', title='Actual line-search trial chronology\nTrial acceptance is not path-state acceptance', xlabel='Saved trial index', ylabel='Actual factor (dimensionless)')
        trial_ax.legend(fontsize=9); trial_ax.grid(alpha=.2)
        peak = states[1]['record']; wp = peak['workpiece']; counts = result['call_counts']
        lines = ['CLOSED PRODUCTION FAILURE — UNQUALIFIED', f"Failure: {result['failure']['code']}", 'Accepted states ONLY: initial 0 and peak .5 mm.', 'RETURN ZERO NOT ACCEPTED. No hysteresis curve.', '',
                 *[f"{r['index']}: d={r['d_mm']:g} mm; R={r['R_input_N']:.9g} N; q_out(+y)={r['q_out_mm']:.9g} mm; min J={r['minimum_J']:.10g}" for r in rows], '',
                 *[f"Lower body {k}: Fx={wp['force_on_lower_body_N'][k][0]:.9g}, Fy={wp['force_on_lower_body_N'][k][1]:.9g} N" for k in ('total','material','regularization')],
                 'Force ON body = negative holding reaction on model.', 'Node-window proxies only; no boundary-distance result.',
                 f"Peak proxy bottom/left={wp['node_window_clearance_mm']['bottom']:.9g}/{wp['node_window_clearance_mm']['left']:.9g} mm", '',
                 *[f"Rollback {r['from_displacement']:g}→{r['attempted_displacement']:g} mm: {r['code']} (depth {r['depth']})" for r in diagnostic['failed_attempts']],
                 f"F started/completed={counts['force_calls']}/{counts['force_calls_completed']}; T={counts['tangent_calls']}/{counts['tangent_calls_completed']}", 'Counter deficits shown as saved; attribution not inferred.',
                 f"Wrapper elapsed={receipt['elapsed_seconds']:.6g}s; limit={receipt['seconds_limit']}s", f"COMMON arrow scale: {max_force:.8g} N = 4 display mm.", 'Small body arrow may be subpixel; read numbers above.',
                 'No new F/T/solve/HP/consumer/geometry; no pressure/contact/clamp.']
        text_ax.axis('off'); text_ax.text(0,1,'\n'.join(lines),va='top',fontsize=9.1,linespacing=1.35)
        fig.suptitle('Cycle003 CLOSED FAIL: saved accepted initial/peak structures and actual failed-return diagnostics\nNo accepted return-zero state; no fresh reference or equilibrium/contact qualification', fontsize=16, color='#9b1c1c')
        checkpoint(); fig.savefig(output/'cycle003_failure.png', dpi=150); plt.close(fig)
        with (output/'accepted_numeric_states.csv').open('x',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        (output/'saved_diagnostics.json').write_text(json.dumps(dict(path_diagnostics=diagnostic,accepted_progress=progress),indent=2,allow_nan=False)+'\n',encoding='utf-8')
        (output/'plot_cycle003_failure_frozen.py').write_bytes(Path(__file__).read_bytes())
        checkpoint(); assert all(sha(p)==value for p,value in pins.items()), 'Bound saved data changed during rendering'
        report.update(status='rendered_closed_failure',production_status=result['status'],production_failure=result['failure'],accepted_states=2,accepted_targets_mm=[0.,.5],requested_targets_mm=result['targets_mm'],
                      completed_base_observations=len(history),trial_records=len(trials),failed_attempts=diagnostic['failed_attempts'],call_counts=counts,
                      display=dict(actual_geometry_scale=1,supplementary_displacement_scale=4,supplementary_force_arrows=False,force_scale_N_per_display_mm=force_scale,interpolated_states=0,return_zero_present=False),
                      units=dict(length='mm',force='N',J='dimensionless',Hu='1/mm'),input_files_sha256={p.relative_to(ROOT).as_posix():value for p,value in pins.items()},inputs_unchanged=True,
                      helper_sha256=HELPER_SHA,source_sha256=sha(Path(__file__)),scientific_reference_qualified=False,pressure_contact_clamp_qualified=False)
    except Exception as error:
        report.update(status='failed_saved_view',error=repr(error));raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=PEAK,outputs_sha256={p.name:sha(p) for p in output.iterdir() if p.is_file()})
        (output/'view_metadata.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
