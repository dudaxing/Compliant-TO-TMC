"""Display two new reference summaries; no mechanics or new qualification."""
from decimal import Decimal, localcontext
from pathlib import Path
import json


def render_partial_reference_observation(output, selected_states, accepted_indices, checkpoint):
    output = Path(output)
    assert len(selected_states) == len(accepted_indices) == 2
    states = []
    for selected, accepted_index in zip(selected_states, accepted_indices):
        checkpoint()
        index = selected['original_target_index']
        source = output / f'accepted_{index:03d}/summary.json'
        row = json.loads(source.read_bytes())
        assert row['status'] == 'pass' and row['index'] == index
        assert row['state_sha256'] == selected['state_sha256'] and row['target_mm'] == selected['d']
        checkpoint()
        entries = []
        for group, label in (('force_checks', 'Global force'), ('tangent_checks', 'PORT action')):
            for part, name in (('total', 'total'), ('material', 'material'), ('regularization', 'Hu')):
                check = row[group][part]
                entries.append(dict(label=label + ' / ' + name, source_member=group + '.' + part,
                    error=check['normalized_error'], limit=check['limit'], pass_gate=check['pass_gate']))
        for member, label in (('CSC_total_action_check', 'Saved CSC / PORT action'),
                              ('augmented_checks.force', 'KKT free-force action')):
            check = row
            for key in member.split('.'):
                check = check[key]
            entries.append(dict(label=label, source_member=member, error=check['normalized_error'],
                limit=check['limit'], pass_gate=check['pass_gate']))
        check = next(item for item in row['checks'] if item['name'] == 'hp120 relative_residual')
        entries.append(dict(label='HP120 equilibrium residual', source_member='checks:hp120 relative_residual',
            error=check['normalized_error'], limit=check['limit'], pass_gate=check['pass_gate']))
        check = row['force_checks']['total']
        entries.append(dict(label='HP80 / HP120 global total force', source_member='force_checks.total.hp80_hp120_error',
            error=check['hp80_hp120_error'], limit=check['reference_limit'], pass_gate=check['pass_gate']))
        with localcontext() as context:
            context.prec = 40  # Display arithmetic only; the inherited gates are already evaluated.
            for entry in entries:
                ratio = Decimal(entry['error']) / Decimal(entry['limit'])
                entry['display_log10_error_over_limit'] = float(ratio.log10()) if ratio else None
        states.append(dict(source=source.relative_to(output).as_posix(), accepted_source_index=accepted_index,
            original_target_index=index, state_sha256=row['state_sha256'], target_mm=selected['d'],
            leg=selected['leg'], entries=entries))
    import matplotlib.pyplot as plt
    checkpoint()
    fig, axes = plt.subplots(1, 2, figsize=(18, 6.3), sharex=True)
    try:
        values = [entry['display_log10_error_over_limit'] for state in states for entry in state['entries']
            if entry['display_log10_error_over_limit'] is not None]
        for ax, state in zip(axes, states):
            entries = state['entries']
            for position, entry in enumerate(entries):
                value = entry['display_log10_error_over_limit']
                if value is None:
                    ax.text(.02, position, '0 (exact recorded error)', transform=ax.get_yaxis_transform(), fontsize=8)
                else:
                    ax.scatter(value, position, color='#2563a6', s=45)
                ax.annotate(f"{Decimal(entry['error']):.2E} / {Decimal(entry['limit']):.0E}",
                    (.99, position), xycoords=ax.get_yaxis_transform(), ha='right', va='center', fontsize=7.5)
            ax.axvline(0, color='#bd532a', linestyle='--')
            ax.set_xlim(min(values + [0]) - 2, max(values + [0]) + 13)
            ax.set_yticks(range(len(entries)), [entry['label'] for entry in entries])
            ax.invert_yaxis()
            ax.set_xlabel('log10(recorded normalized error / original limit); gate at 0, no added floor')
            ax.set_title(f"{state['leg']}: source accepted {state['accepted_source_index']} / original {state['original_target_index']}, input {state['target_mm']:.2f} mm")
            ax.grid(axis='x', alpha=.2)
        fig.text(.5, .02, 'Original normalization retained; one PORT direction. No full-path, pressure or grip qualification.',
            ha='center', fontsize=8)
        fig.tight_layout(rect=(0, .05, 1, 1))
        image = output / 'reference_observations.png'
        assert not image.exists()
        checkpoint()
        fig.savefig(image, dpi=150)
        checkpoint()
    finally:
        plt.close(fig)
    record = dict(status='rendered_observation_only', states=states,
        original_gates_unchanged=True, new_mechanics_calls=0, mechanical_hooks_monitored=False,
        full_production_path_reference_pass=False,
        scope='Only two selected saved source states and existing new reference records; no new mathematical gate or qualification')
    with (output / 'reference_observations.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    checkpoint()
    return record
