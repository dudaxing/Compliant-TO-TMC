"""Render saved action errors only; no tensor contraction or mechanics calls."""
from pathlib import Path
from time import perf_counter
from decimal import Decimal
import gzip
import hashlib
import json

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
BASE = 'lf_data_preparation/native_workpiece_001/'
PARTS = ('total', 'material', 'regularization')
PEAK = 0

def main():
    global PEAK
    import numpy as np
    import psutil
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    def checkpoint():
        global PEAK
        info = psutil.Process().memory_info()
        PEAK = max(PEAK, info.rss, getattr(info, 'peak_wset', info.rss))
        if perf_counter()-STARTED > 60 or PEAK > 8*1024**3 or (STAGE/'stop_requested.txt').exists():
            raise RuntimeError('Saved renderer resource/stop limit reached; no retry')
    output = STAGE/'evidence'
    output.mkdir()
    report = dict(status='running', qualification=False, new_calls=dict(force=0, tangent=0, HP=0, solver=0, action_consumer=0),
                  scope='Saved-error rendering only; no new mechanics, reference evaluation or physical qualification')
    try:
        protocol_path = STAGE/'protocol.json'
        protocol = read(protocol_path); pins = dict(protocol['bindings'])
        pins[protocol_path.relative_to(ROOT).as_posix()] = sha(protocol_path)
        newdir = ROOT/(BASE+'matmul320_action_requalification_001/evidence')
        olddir = ROOT/(BASE+'matmul320_saved_action_diagnostic_001/evidence')
        oldref = ROOT/(BASE+'matmul320_candidate_001/check/reference/result.json')
        consumer = ROOT/'hf_repo/src/hf_eval/tangent_action.py'
        required = [Path(__file__), consumer, newdir/'result.json', newdir/'checks.json.gz',
                    olddir/'result.json', olddir/'element_classification.json.gz', oldref]
        assert all(path.resolve().relative_to(ROOT).as_posix() in pins for path in required)
        assert all(sha(ROOT/path) == pin for path, pin in pins.items()), 'Before-render bindings changed'
        new, old = read(newdir/'result.json'), read(olddir/'result.json')
        assert new['status'] == 'pass' and new['local_gate_count'] == 19200 and new['global_gate_count'] == 9
        assert new['new_call_counts'] == dict(force=0, tangent=0, HP=0, solver=0, JIT=0) and new['action_consumer_started'] == new['action_consumer_completed'] == 3
        assert old['status'] == 'diagnostic_completed' and read(oldref)['status'] == 'fail'
        assert new['files']['checks.json.gz'] == sha(newdir/'checks.json.gz') and new['bindings']['hf_repo/src/hf_eval/tangent_action.py'] == sha(consumer)
        with gzip.open(newdir/'checks.json.gz', 'rt', encoding='utf-8') as stream: checks = json.load(stream)
        with gzip.open(olddir/'element_classification.json.gz', 'rt', encoding='utf-8') as stream: classifications = json.load(stream)
        actions = [r for r in checks if r['scope'] == 'local' and r['kind'] == 'action']
        indexed = {(r['component'], r['element']): r for r in actions}
        assert len(checks) == 19209 and all(r['pass_gate'] for r in checks) and len(actions) == len(indexed) == len(classifications) == 9600
        rows = []
        for row in classifications:
            gate = indexed[(row['component'], row['element'])]
            assert Decimal(row['original_limit']) == Decimal(gate['limit'])
            rows.append(dict(element=row['element'], component=row['component'], old_error=row['saved_error'], new_error=gate['normalized_error'], limit=gate['limit'],
                             old_exceeds=row['saved_exceeds_original_gate'], new_exceeds=Decimal(gate['normalized_error']) > Decimal(gate['limit'])))
        assert len({(r['component'], r['element']) for r in rows}) == 9600
        checkpoint(); plt.rcParams.update({'font.size': 17})
        fig, axes = plt.subplots(1, 3, figsize=(26, 9.5), layout='constrained')
        counts = {}
        for part, ax in zip(PARTS, axes, strict=True):
            data = sorted((r for r in rows if r['component'] == part), key=lambda r: r['element'])
            assert [r['element'] for r in data] == list(range(3200))
            counts[part] = dict(old_exceeds=sum(r['old_exceeds'] for r in data), new_exceeds=sum(r['new_exceeds'] for r in data))
            for key, label, color in [('old_error', 'Original saved contraction', '#d95f02'), ('new_error', 'Compensated consumer', '#1f77b4')]:
                ax.scatter([r['element'] for r in data], np.maximum([float(r[key]) for r in data], 1e-30), s=7, alpha=.65, color=color, label=label)
            ax.axhline(float(data[0]['limit']), color='red', ls='--', lw=2, label='Original action gate')
            name = 'Hu regularization' if part == 'regularization' else part.capitalize()
            ax.set(title=f"{name}: over gate {counts[part]['old_exceeds']} → {counts[part]['new_exceeds']}", xlabel='Element index (all 3200)', ylabel='Normalized error', yscale='log', ylim=(1e-31, None))
            ax.legend(fontsize=14, loc='lower right'); ax.grid(alpha=.25)
        fig.suptitle('Saved tangent actions: original contraction vs compensated consumer\nInherited HP80/120 data; no new mechanics or reference evaluation', fontsize=21)
        fig.supxlabel('Display floor 1e-30 only; numeric errors are unchanged. Old diagnostic: HP120; new recorded gates: HP80.', fontsize=14)
        fig.savefig(output/'requalified_action_errors.png', dpi=100); plt.close(fig)
        with gzip.open(output/'plotted_error_data.json.gz', 'xt', encoding='utf-8') as stream: json.dump(rows, stream)
        checkpoint(); assert all(sha(ROOT/path) == pin for path, pin in pins.items()), 'After-render bindings changed'
        report.update(status='rendered', input_bindings=pins, counts=counts, rows=9600, display_floor=1e-30, PNG_pixels=[2600, 950], inherited_requalification_status='pass', original_reference_status='fail_preserved')
    except Exception as error:
        report.update(status='fail', error=repr(error)); raise
    finally:
        report.update(elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=PEAK, outputs={p.name:sha(p) for p in output.iterdir() if p.is_file()})
        (output/'view_metadata.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
