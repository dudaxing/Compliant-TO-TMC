"""One authorized install, six finite tests, two LF preparations and one view."""
from time import perf_counter
STARTED = perf_counter()
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
read = lambda p: json.loads(p.read_bytes())
protocol = read(STAGE / 'protocol.json')
OUTPUT = ROOT / protocol['output_directory']
events, counts, installed, outputs = [], {}, [], {}
peak = 0
read_opens, load_calls = [], []


def checkpoint(event='checkpoint'):
    global peak
    peak = max(peak, psutil.Process().memory_info().rss)
    if (perf_counter() - STARTED > protocol['helper_seconds'] or peak > protocol['sampled_RSS_bytes']):
        raise RuntimeError('L-BPREP1 helper resource boundary reached')
    events.append(event)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path, mode = Path(os.fsdecode(args[0])), args[1]
        if path.suffix.lower() == '.npz' and isinstance(mode, str) and 'r' in mode:
            read_opens.append(str(path.resolve()))


def bindings():
    for name, pin in (protocol['input_bindings'] | protocol['source_bindings']).items():
        checkpoint()
        assert sha256((ROOT / name).read_bytes()).hexdigest() == pin, name


def command(argv, log_name):
    checkpoint(log_name + '_started')
    with (STAGE / log_name).open('xb') as log:
        result = subprocess.run(argv, cwd=protocol['working_directory'], env=dict(os.environ,
            PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
            PYTHONPATH=str(ROOT / 'hf_repo/src'), HF_BATCH_TEST_REPO=str(ROOT),
            L_BPREP_TEST_ROOT=protocol['test_root']), stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
    checkpoint(log_name + '_completed')
    if result.returncode != 0:
        raise RuntimeError(log_name + ' exited ' + str(result.returncode))


def checks_and_view():
    import numpy as np
    original_load = np.load

    def load(file, *args, **kwargs):
        load_calls.append(str(Path(file).resolve()))
        return original_load(file, *args, **kwargs)

    np.load = load
    index = read(OUTPUT / 'index.json')
    batch = read(OUTPUT / 'batch_manifest.json')
    source_list = read(ROOT / protocol['source_manifest'])
    sources = read(STAGE / 'author/SOURCES.json')
    template = read(ROOT / source_list['task_template'])
    assert index['status'] == 'prepared' and index['batch_preflight']['status'] == 'pass'
    assert len(index['cases']) == len(batch['cases']) == 2
    assert batch['options'] == source_list['options']
    assert not (OUTPUT / 'evaluation_index').exists() and not (OUTPUT / 'evaluations').exists()
    rows, views, grids = [], [], []
    mapping = dict(solid='solid', design='design_domain', passive_solid='passive_solid', passive_void='passive_void')
    for i, (case, key) in enumerate(zip(source_list['cases'], ('fine', 'wave'))):
        checkpoint('check_case_started')
        directory = OUTPUT / 'prepared' / f'{i:03d}'
        old = sources['LF_packages'][key]['prepared']
        source_file = ROOT / case['source_descriptor']
        native = read(directory / 'native_geometry/geometry.json')
        derived = read(directory / 'derived_geometry/geometry.json')
        bound = read(directory / 'task.json')
        single = read(directory / 'input_manifest.json')
        assert single['status'] == index['cases'][i]['status'] == 'success'
        assert native['geometry_id'] == old['native_geometry']['identity']['geometry_id']
        assert derived['geometry_id'] == old['analysis_geometry']['identity']['geometry_id']
        assert {k: v for k, v in bound.items() if k != 'geometry'} == {k: v for k, v in template.items() if k != 'geometry'}
        assert bound['geometry'] == {k: derived[k] for k in ('geometry_id', 'descriptor_sha256')}
        assert len(bound['path']['targets_mm']) == 25
        for name in ('design.json', 'design.npz'):
            assert (directory / 'native_geometry/sources' / name).read_bytes() == source_file.with_name(name).read_bytes()
        field_checks = {}
        with np.load(source_file.with_name('design.npz'), allow_pickle=False) as original, np.load(
                directory / 'native_geometry/geometry.npz', allow_pickle=False) as converted, np.load(
                directory / 'derived_geometry/geometry.npz', allow_pickle=False) as padded:
            assert set(original.files) == set(mapping.values())
            assert set(converted.files) == set(padded.files) == set(mapping)
            for name, source_name in mapping.items():
                assert np.array_equal(converted[name], original[source_name].astype(np.uint8))
                assert np.array_equal(padded[name][:, :160], converted[name])
                assert padded[name].shape == (80, 168)
                assert np.all(padded[name][:, 160:] == (1 if name == 'passive_void' else 0))
                field_checks[name] = dict(native_equal=True, derived_parent_equal=True, right_padding_equal=True)
            solid = padded['solid'].copy()
        geometry_path, task_path = directory / 'derived_geometry/geometry.json', directory / 'task.json'
        actual_case = batch['cases'][i]
        assert set(actual_case) == {'label', 'geometry', 'task', 'output'}
        assert (ROOT / actual_case['geometry']).resolve() == geometry_path.resolve()
        assert (ROOT / actual_case['task']).resolve() == task_path.resolve()
        assert not (ROOT / actual_case['output']).exists()
        grids.append(derived['grid'])
        rows.append(dict(label=case['label'], status='success', native_geometry_id=native['geometry_id'],
            analysis_geometry_id=derived['geometry_id'], fields=field_checks,
            native_solid_cells=int(solid[:, :160].sum()), task_fields_except_geometry_equal=True,
            task_targets=25, prepared=str(directory.relative_to(ROOT)).replace('\\', '/'), future_evaluation_created=False))
        views.append((case['label'], solid, derived, bound))
        checkpoint('check_case_completed')
    assert grids[0] == grids[1]
    write(OUTPUT / 'checks.json', dict(status='pass', rows=rows, shared_full_grid=grids[0],
        existing_batch_preflight=index['batch_preflight'], real_preparations=2, future_batch_executions=0,
        qualification_upgraded=False, note='New descriptor/task byte identities are location dependent; old geometry IDs only are compared'))
    checkpoint('plot_started')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.8), sharex=True, sharey=True)
    colors = dict(support='#0072B2', symmetry='#CC79A7', input='#D55E00', output='#009E73')
    for ax, (label, solid, geometry, task) in zip(axes, views):
        ax.imshow(solid, extent=[0, 84, 0, 40], origin='lower', interpolation='nearest', cmap='Greys', vmin=0, vmax=1)
        ax.axvspan(80, 84, color='#56B4E9', alpha=.2, label='added medium, 4 mm')
        ax.axvline(80, color='#777777', linestyle=':', linewidth=1)
        for name, tag in geometry['region_tags'].items():
            points = np.asarray(tag['points_mm'])
            ax.plot(points[:, 0], points[:, 1], color=colors[name], lw=3, label=name + ' declaration')
            if 'direction' in tag:
                at = points.mean(axis=0)
                direction = np.asarray(tag['direction'])
                ax.annotate('', xy=at + 4 * direction, xytext=at,
                    arrowprops=dict(arrowstyle='->', color=colors[name], lw=1.5))
        body = task['workpiece']
        cx, cy = body['center_mm']; side = body['side_mm']
        ax.add_patch(Rectangle((cx-side/2, cy-side/2), side, side/2, fill=False,
            edgecolor='#E69F00', hatch='///', linewidth=1.8, label='fixed square, lower half'))
        ax.set(xlim=(-2, 86), ylim=(-2, 43), xlabel='x [mm]', title=label)
        ax.set_aspect('equal')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('y [mm], lower half')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=9, frameon=False)
    fig.suptitle('Undeformed input declarations | no model, applied loads or force response', fontsize=14)
    fig.subplots_adjust(top=.83, bottom=.25, left=.05, right=.98, wspace=.08)
    fig.savefig(OUTPUT / 'prepared_inputs.png', dpi=150)
    plt.close(fig)
    checkpoint('plot_completed')
    text = '''# LF batch input preparation: manual review\n\nTwo ordinary LF packages are prepared under one unchanged task. The diagram shows undeformed declarations; no model, force, tangent, equilibrium or HP calculation was run. Arrows show port directions only.\n\n![Prepared inputs](prepared_inputs.png)\n\n| Case | Status | Native solid cells | Grid | Targets |\n| --- | --- | ---: | --- | ---: |\n'''
    for row in rows:
        text += f"| {row['label']} | {row['status']} | {row['native_solid_cells']} | 80 x 168, h=0.5 mm | 25 |\n"
    text += '\n[Source list](../source_manifest.json) · [Preparation index](index.json) · [Batch manifest](batch_manifest.json) · [Exact data checks](checks.json)\n\n'
    for i, row in enumerate(rows):
        text += f"- {row['label']}: [geometry](prepared/{i:03d}/derived_geometry/geometry.json), [task](prepared/{i:03d}/task.json), [source and epoch](prepared/{i:03d}/input_manifest.json).\n"
    text += '\nCheck port/support locations, the fixed square outline and native/added-domain boundary. The square is shown only within the lower-half analysis domain. No future evaluation directory has been created. Future clock/budget must be specified before batch execution. Existing qualification and failed history are unchanged; pressure, effective grip, release, stability, formal labels, ranking and HF5 remain unqualified.\n'
    (OUTPUT / 'REVIEW.md').write_text(text.rstrip() + '\n', encoding='utf-8', newline='\n')
    checkpoint('review_written')


def seal():
    result = {}
    for path in sorted(OUTPUT.rglob('*')):
        if path.is_file() and path.name != 'execution_receipt.json':
            checkpoint()
            raw = path.read_bytes()
            result[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    checkpoint()
    return result


def main():
    global outputs
    auth = read(STAGE / 'author/authorization.json')
    assert auth['card'] == protocol['card'] == 'L-BPREP1'
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['protocol_sha256'] == sha256((STAGE / 'protocol.json').read_bytes()).hexdigest()
    assert not OUTPUT.exists() and not Path(protocol['test_root']).exists()
    sys.addaudithook(audit)
    status, error, identity_seal, unchanged = 'not_pass', None, 'not_complete', False
    try:
        bindings()
        for target, candidate in protocol['candidate_installations'].items():
            checkpoint('installation_started')
            path = ROOT / target
            with path.open('xb') as stream:
                stream.write((ROOT / candidate).read_bytes())
            installed.append(target)
            checkpoint('installation_completed')
        counts['test_invocations'] = 1
        command([sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', 'discover', '-s', str(ROOT/'hf_repo/tests'),
                 '-p', 'test_lf_native_batch_inputs.py', '-v'], 'tests_stdout.log')
        assert 'Ran 6 tests' in (STAGE/'tests_stdout.log').read_text(encoding='utf-8')
        counts['test_methods_passed'] = 6
        counts['CLI_invocations'] = 1
        command([sys.executable, '-X', 'utf8', '-B', str(STAGE/'audit_cli.py'), str(STAGE/'cli_reads.json'),
            str(ROOT/'hf_repo/scripts/prepare_native_lf_batch_inputs.py'), '--repo', str(ROOT),
            '--manifest', protocol['source_manifest'], '--output', protocol['output_directory']], 'cli_stdout.log')
        counts['real_cases_prepared'] = 2
        checks_and_view()
        counts['new_PNGs'] = 1
        bindings()
        for target, candidate in protocol['candidate_installations'].items():
            assert (ROOT/target).read_bytes() == (ROOT/candidate).read_bytes()
        unchanged = True
        outputs = seal()
        identity_seal = 'complete_inside_original_helper_window'
        status = 'pass'
    except BaseException as failure:
        error = dict(type=type(failure).__name__, message=str(failure))
        if perf_counter() - STARTED <= protocol['helper_seconds']:
            try:
                outputs = seal()
                identity_seal = 'actual_partial_inside_original_helper_window'
            except BaseException:
                identity_seal = 'not_complete_before_resource_close'
    OUTPUT.mkdir(parents=True, exist_ok=True)
    receipt = dict(card='L-BPREP1', status=status, error=error, counts=counts, installed_files=installed,
        output_identity_seal=identity_seal, outputs=outputs, all_bindings_unchanged=unchanged,
        elapsed_seconds=perf_counter()-STARTED, helper_seconds=protocol['helper_seconds'],
        sampled_peak_RSS_bytes=peak, sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        protocol_sha256=auth['protocol_sha256'], working_directory=str(Path.cwd()), events=events,
        helper_NPZ_read_opens=read_opens, helper_numpy_load_calls=load_calls,
        CLI_array_events=read(STAGE/'cli_reads.json') if (STAGE/'cli_reads.json').exists() else None,
        array_read_scope='NPZ file read opens counted separately from numpy.load calls/byte-buffer decodes; checksum reads included',
        mechanics_basis='Pinned preparation, metadata validation and test sources; no universal dynamic mechanical hooks',
        new_model_F_T_HP_solver_calls=0, future_batch_executions=0, old_geometry_NPZ_or_media_reads=0,
        original_scientific_gates_changed=False, qualifications_upgraded=False,
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(OUTPUT/'execution_receipt.json', receipt)
    checkpoint('receipt_written')
    print(json.dumps(dict(status=status, counts=counts, installed=len(installed), output_files=len(outputs), error=error)), flush=True)
    if status != 'pass':
        raise RuntimeError('L-BPREP1 closed not_pass; no retry')


if __name__ == '__main__':
    main()
