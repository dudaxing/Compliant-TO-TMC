"""Plot new tiny-test scalar JSON only; no field or historical payload reads."""
from time import perf_counter
STARTED = perf_counter()
import argparse
from hashlib import sha256
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stop-file', type=Path, required=True)
    parser.add_argument('--time-limit', type=float, required=True)
    args = parser.parse_args()

    def check():
        if args.stop_file.exists() or perf_counter()-STARTED > args.time_limit:
            raise RuntimeError('Scalar display stop or time limit')

    check()
    raw = args.input.read_bytes()
    data = json.loads(raw)
    rows = data['rows']
    assert rows and not args.output.exists()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    check()
    series = list(dict.fromkeys(row['series'] for row in rows))
    figure, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout='constrained')
    offset = 0
    for name in series:
        selected = [row for row in rows if row['series'] == name]
        indices = list(range(offset, offset+len(selected)))
        label = name.replace('_', ' ')
        axes[0].plot([r['d_mm'] for r in selected], [r['R_input_N'] for r in selected],
                     'o-', ms=5, label=label, alpha=.8)
        axes[1].plot(indices, [r['relative_residual'] for r in selected], 'o-', ms=5,
                     label=label, alpha=.8)
        anchors = [i for i, row in enumerate(selected) if row['anchor_revalidation']]
        for i in anchors:
            axes[0].plot(selected[i]['d_mm'], selected[i]['R_input_N'], 'ks', ms=8, fillstyle='none')
            axes[1].plot(indices[i], selected[i]['relative_residual'], 'ks', ms=8, fillstyle='none')
        offset += len(selected)
    axes[0].set(xlabel='Absolute mean input d (mm)', ylabel='Actuator reaction R (N)',
                title='New saved loading / first-unload chains')
    axes[1].axhline(1e-9, color='firebrick', ls='--', label='Original residual bound 1e-9')
    axes[1].set_yscale('symlog', linthresh=1e-15)
    axes[1].set(xlabel='Accepted-state ordinal (each saved segment retained)',
                ylabel='Relative equilibrium residual', title='Accepted states; exact zero retained')
    for axis in axes:
        axis.grid(alpha=.25)
        axis.legend(fontsize=8, loc='best')
    figure.suptitle('16 cells / 50 DOF, no workpiece: API compatibility only\n'
                   'Open squares = fresh saved-anchor checks; not circle contact / grip evidence', fontsize=12)
    check()
    figure.savefig(args.output, dpi=160)
    plt.close(figure)
    check()
    manifest = dict(status='pass', rows=len(rows), series=series, input_sha256=sha256(raw).hexdigest(),
        output=args.output.name, elapsed_seconds=perf_counter()-STARTED,
        scope='One new scalar PNG from this test-window JSON only; no NPZ, old circle data or media opened')
    args.output.with_suffix('.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(manifest), flush=True)


if __name__ == '__main__':
    main()
