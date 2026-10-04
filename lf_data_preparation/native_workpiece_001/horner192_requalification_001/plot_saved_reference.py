"""Plot saved F16 reference gates and energy diagnostics; no mechanics calls."""
from pathlib import Path
from time import perf_counter
from decimal import Decimal
import gzip
import hashlib
import json

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import psutil

    result_file = STAGE/'check/reference/result.json'
    summary = json.loads(result_file.read_text(encoding='utf-8'))
    candidate_file = STAGE/'check/candidate/result.json'
    candidate = json.loads(candidate_file.read_text(encoding='utf-8'))
    assert summary['status'] == candidate['status'] == 'pass'
    assert sha(candidate_file) == summary['candidate_result_sha256']
    data = {}
    for name in ('checks.json.gz', 'auxiliary_energy_differences.json.gz'):
        source = result_file.with_name(name)
        assert sha(source) == summary['files'][name]
        with gzip.open(source, 'rt', encoding='utf-8') as stream:
            data[name] = json.load(stream)
    checks, energy = data['checks.json.gz'], data['auxiliary_energy_differences.json.gz']
    assert len(checks) == 19209 and all(row['pass_gate'] for row in checks)
    output = STAGE/'saved_reference_view'
    output.mkdir()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
    parts, labels = ['total', 'material', 'regularization'], ['Total', 'Material', 'Hu regularization']
    plotted = []
    for ax, kinds, title in ((axes[0, 0], ['force'], 'Complete weak force'),
                            (axes[0, 1], ['action', 'CSC_action'], 'Declared direction Jv')):
        for kind in kinds:
            for scope in (['global'] if kind == 'CSC_action' else ['local', 'global']):
                rows = [max((row for row in checks if row['kind'] == kind and
                    row['scope'] == scope and row['component'] == part),
                    key=lambda row: float(row['normalized_error'])) for part in parts]
                values = [float(row['normalized_error'])/float(row['limit']) for row in rows]
                plotted.extend(dict(scope=scope, kind=kind, component=part,
                    normalized_error=row['normalized_error'], limit=row['limit'], error_over_gate=value)
                    for part, row, value in zip(parts, rows, values, strict=True))
                ax.plot(labels, np.maximum(values, 1e-30), 'o-', label=scope+' '+kind)
        ax.axhline(1, color='#bb3333', ls=':', label='original acceptance boundary')
        ax.set(yscale='log', ylim=(1e-30, 10), title=title,
               ylabel='worst saved normalized error / original gate')
        ax.grid(True, axis='y', alpha=.25)
        ax.legend(fontsize=8)
    ax = axes[1, 0]
    energy_rows = {}
    for key, label in (('candidate_minus_HP120', 'Candidate - HP120'),
                       ('HP80_minus_HP120', 'HP80 - HP120')):
        raw = energy[key]
        assert len(raw) == 3200
        values = np.abs(np.array([float(value) for value in raw]))
        ax.plot(np.arange(3200), np.maximum(values, 1e-130), '.', ms=2, label=label)
        energy_rows[key] = dict(max_absolute_difference=str(max(abs(Decimal(value)) for value in raw)),
            exact_zero_count=sum(Decimal(value) == 0 for value in raw), units='N mm')
    ax.set(yscale='log', xlabel='original element index', ylabel='absolute auxiliary energy difference [N mm]',
           title='Energy diagnostic only: no new acceptance gate')
    ax.grid(True, axis='y', alpha=.25)
    ax.legend(fontsize=8)
    ax = axes[1, 1]
    ax.axis('off')
    ax.text(.01, .98, 'PASS: one captured trial and one declared direction\n\n'
        '3200 elements / 6642 DOFs / 376 fixed DOFs\n'
        '1 complete F + 1 cached T + 3 compensated Jv\n'
        '2 fresh references: HP80 and HP120\n'
        '19200 local + 9 global gates; original limits\n'
        '614400 tensor contributions checked in full CSC\n\n'
        'F16 was a rejected unloading trial, not equilibrium.\n'
        'This does not qualify the later T25 state,\n'
        'the complete unloading path, stress or contact.\n\n'
        'Display floors only: error ratio 1e-30; energy 1e-130.\n'
        'All raw saved values remain unchanged.', va='top', fontsize=10, linespacing=1.5)
    fig.suptitle('F16 Horner192: complete response vs independent HP80/120', fontsize=14)
    image = output/'reference_error_gates.png'
    fig.savefig(image, dpi=180)
    plt.close(fig)
    info = psutil.Process().memory_info()
    peak, elapsed = max(info.rss, getattr(info, 'peak_wset', info.rss)), perf_counter()-STARTED
    assert elapsed <= 120 and peak <= 8*1024**3 and not (STAGE/'stop_requested.txt').exists()
    report = dict(status='pass', scope='Saved reference display only; no new numerical mechanics/geometry',
        new_mechanics_calls=0, elapsed_seconds=elapsed, sampled_peak_RSS_bytes=peak,
        script_sha256=sha(Path(__file__)), source_result_sha256=sha(result_file),
        candidate_result_sha256=sha(candidate_file),
        input_payloads={name:summary['files'][name] for name in data},
        plotted_rows=plotted, energy_diagnostics=energy_rows,
        display_floor_error_over_gate=1e-30, display_floor_energy_N_mm=1e-130,
        image_sha256=sha(image))
    (output/'view_metadata.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('status', 'elapsed_seconds', 'sampled_peak_RSS_bytes', 'new_mechanics_calls')}))


if __name__ == '__main__':
    main()
