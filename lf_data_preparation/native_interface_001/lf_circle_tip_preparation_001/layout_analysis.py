"""Resident undeformed circle-layout comparison; no file inputs or mechanics.

The helper supplies its one newly constructed Project. The x74 baseline is
reselected on that same grid, never constructed as another mechanical model.
Distances concern finite staircase boundaries, not signed gaps or contact.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np

from hf_eval.boundary_geometry import boundary_distances, exposed_q1_edges


TIP_REFERENCE_MM = (80., 30.)


def _tip_boundary(point, xy, edges):
    """The S1 viewer's point/finite-segment projection, retaining exact ties."""
    a, delta = xy[edges[:, 0]], xy[edges[:, 1]] - xy[edges[:, 0]]
    parameter = np.clip(np.sum((point-a)*delta, axis=1) / np.sum(delta*delta, axis=1), 0., 1.)
    nearest = a + parameter[:, None]*delta
    distances = np.linalg.norm(point-nearest, axis=1)
    index = int(np.argmin(distances))
    return dict(distance_mm=float(distances[index]), point_mm=nearest[index].tolist(),
        workpiece_edge_index=index, workpiece_nodes=edges[index].tolist(),
        segment_parameter=float(parameter[index]),
        tied_workpiece_edge_indices=np.flatnonzero(distances == distances[index]).tolist(),
        scope='Unsigned fixed reference tip to actual undeformed Q1 boundary; not contact')


def analyze_layout(project, baseline_workpiece, check, checkpoint):
    """Return JSON-ready observations; caller check(name, condition) fails closed."""
    record_check = check

    def check(condition, name):
        record_check(name, bool(condition))

    checkpoint()
    model, grid, meta = project.model, project.geometry.grid, project.region_metadata
    xy, conn = model.coordinates, model.connectivity
    solid = np.asarray(model.solid, dtype=bool)
    passive_void = np.asarray(project.geometry.arrays['passive_void'], dtype=bool).ravel(order='C')
    ny, nx = grid['shape_yx']
    x0, y0 = map(float, grid['origin_mm'])
    dx, dy = map(float, grid['cell_size_mm'])
    width, height = map(float, grid['extent_mm'])
    right, top = x0+width, y0+height
    check(grid['shape_yx'] == [80, 184] and grid['origin_mm'] == [0., 0.]
          and grid['cell_size_mm'] == [.5, .5] and grid['extent_mm'] == [92., 40.],
          'Resident native analysis grid is unchanged 184x80, h=.5, domain [0,92]x[0,40] mm')
    check(len(conn) == nx*ny and len(xy) == (nx+1)*(ny+1)
          and np.array_equal(np.min(xy, axis=0), [x0, y0])
          and np.array_equal(np.max(xy, axis=0), [right, top]),
          'Resident coordinate/connectivity sizes and actual bounds match the declared grid')
    candidate = project.task['workpiece']
    expected_base = dict(kind='fixed_rigid', shape='circle', center_mm=[74., 40.],
                         radius_mm=9., fixed_components=[0, 1])
    expected_candidate = dict(expected_base, center_mm=[80., 40.])
    check(baseline_workpiece == expected_base and candidate == expected_candidate,
          'Only the declared x74 to x80 circle placement is analyzed; radius9 and y40 unchanged')
    check(project.task['background_symmetry'] == dict(points_mm=[[0., 40.], [92., 40.]], components=[1]),
          'Original full top uy background symmetry is retained')
    solid_nodes = np.unique(conn[solid])
    tip_ids = np.flatnonzero(np.all(xy == TIP_REFERENCE_MM, axis=1))
    check(len(tip_ids) == 1 and np.isin(tip_ids[0], solid_nodes),
          'Reference tip (80,30) is one unique original-solid node')
    tip_node = int(tip_ids[0])
    centers = xy[conn].mean(axis=1)
    mechanism_edges = exposed_q1_edges(conn, np.flatnonzero(solid), xy, symmetry_y_mm=top)
    check(len(mechanism_edges) > 0, 'Original mechanism has nonempty physical exposed Q1 edges')
    nonbody_fixed = np.unique(np.concatenate([np.asarray(meta[name]['dofs'], dtype=np.int64)
        for name in ('support', 'entity_symmetry', 'background_symmetry')]))
    check(np.array_equal(np.union1d(nonbody_fixed, meta['workpiece']['dofs']), model.fixed_dofs),
          'Candidate merged fixed DOFs equal the original three constraint groups plus body overlay')
    right_nodes = np.flatnonzero(xy[:, 0] == right)
    port_nodes = np.union1d(meta['ports']['input']['nodes'], meta['ports']['output']['nodes'])
    support_nodes = np.asarray(meta['support']['selected_nodes'], dtype=np.int64)
    observations = {}
    masks = {}
    for name, definition in (('baseline', baseline_workpiece), ('candidate', candidate)):
        checkpoint()
        center = np.asarray(definition['center_mm'], dtype=float)
        radius = float(definition['radius_mm'])
        mask = np.sum((centers-center)**2, axis=1) <= radius**2
        cells = np.flatnonzero(mask)
        check(len(cells) > 0 and np.all(passive_void[cells]) and not np.any(solid[cells]),
              name+': nonempty circle overlay selects only original passive-void medium cells')
        nodes = np.unique(conn[cells])
        dofs = (2*nodes[:, None]+np.arange(2)).ravel()
        check(not np.intersect1d(nodes, solid_nodes).size
              and not np.intersect1d(nodes, support_nodes).size
              and not np.intersect1d(nodes, port_nodes).size,
              name+': body shares no original solid, support or input/output port node')
        top_nodes = nodes[xy[nodes, 1] == top]
        check(len(top_nodes) > 0 and np.all(np.isin(2*top_nodes+1, meta['background_symmetry']['dofs'])),
              name+': all body top nodes retain the original background uy symmetry')
        lower, upper = xy[nodes].min(axis=0), xy[nodes].max(axis=0)
        check(center[1] == top and center[0]-radius >= x0 and center[0]+radius <= right
              and center[1]-radius >= y0 and np.all(lower >= [x0, y0]) and np.all(upper <= [right, top]),
              name+': complete analytic lower half and actual selected-cell boundary fit the unchanged domain')
        closed = exposed_q1_edges(conn, cells, xy)
        physical = exposed_q1_edges(conn, cells, xy, symmetry_y_mm=top)
        cut = closed[np.all(xy[closed, 1] == top, axis=1)]
        check(len(physical) > 0 and len(closed) == len(physical)+len(cut),
              name+': physical body edges exclude only the y40 symmetry cut')
        if name == 'candidate':
            check(np.array_equal(cells, np.asarray(meta['workpiece']['cells']))
                  and np.array_equal(nodes, np.asarray(meta['workpiece']['nodes']))
                  and np.array_equal(dofs, np.asarray(meta['workpiece']['dofs'])),
                  'Candidate circle reconstruction matches the one constructed Project overlay exactly')
        boundary = boundary_distances(xy, mechanism_edges, physical)
        checkpoint()
        check(boundary['minimum_boundary_distance_mm'] is not None
              and boundary['minimum_boundary_distance_mm'] > 0.
              and not boundary['intersects'] and not boundary['roundoff_near_touch'],
              name+': undeformed physical Q1 boundaries are separated without crossing or near-touch')
        tip = dict(reference_node_id=tip_node, reference_point_mm=list(TIP_REFERENCE_MM),
                   **_tip_boundary(xy[tip_node], xy, physical))
        relation = dict(tip_equals_global_minimum_exact=bool(tip['distance_mm'] == boundary['minimum_boundary_distance_mm']),
            tip_minus_global_mm=float(tip['distance_mm']-boundary['minimum_boundary_distance_mm']),
            reported_global_mechanism_witness_is_tip=bool(np.array_equal(
                boundary['closest_pair']['mechanism_point_mm'], xy[tip_node])),
            global_witness_scope='Original public first nearest pair; positive-distance global ties are not exhaustively enumerated',
            tip_tie_scope='All exactly tied body edges for the fixed reference tip projection are retained',
            interpretation='Exact equality places the tip on the same minimum-distance level; not a unique closest point or first-contact prediction')
        observations[name] = dict(definition=deepcopy(definition), cells=cells.tolist(), nodes=nodes.tolist(),
            dofs=dofs.tolist(), counts=dict(cells=len(cells), nodes=len(nodes), body_dofs=len(dofs),
                closed_edges=len(closed),
                physical_edges=len(physical), symmetry_cut_edges=len(cut)),
            actual_body_bounds_mm=dict(lower=lower.tolist(), upper=upper.tolist()),
            closed_edges=closed.tolist(), physical_edges=physical.tolist(), symmetry_cut_edges=cut.tolist(),
            boundary=boundary, tip=tip, distance_relation=relation,
            reconstruction_scope='Body geometry on the same new92 resident grid; no old84 FE model or boundary response reconstructed')
        if name == 'baseline':
            check(float(upper[0]) == 83., 'Reconstructed x74 body right extent matches the historical x83 geometry')
        else:
            fixed = np.union1d(nonbody_fixed, dofs)
            ux_free = ~np.isin(2*right_nodes, fixed)
            uy_free = ~np.isin(2*right_nodes+1, fixed)
            top_right = xy[right_nodes, 1] == top
            check(np.all(ux_free) and np.all(uy_free[~top_right]) and np.all(~uy_free[top_right]),
                  'Candidate newx92 ux and non-top uy are free; only original top uy is fixed')
            body_right = float(upper[0])
            column_start = (body_right-x0)/dx
            check(column_start.is_integer() and int(column_start) < nx,
                  'Candidate actual body right boundary leaves whole positive native medium columns')
            column_ids = np.arange(int(column_start), nx, dtype=np.int64)
            strip_cells = (np.arange(ny)[:, None]*nx+column_ids).ravel()
            strip_ok = ~solid[strip_cells] & ~mask[strip_cells] & passive_void[strip_cells]
            check(np.all(strip_ok) and len(strip_cells) == ny*len(column_ids)
                  and np.all(np.diff(column_ids) == 1) and int(column_ids[-1]) == nx-1,
                  'Candidate right strip is continuous full-height nonbody passive-void medium through the new boundary')
            check(body_right == 89. and right-body_right == 3. and len(column_ids) == 6
                  and len(strip_cells) == 480 and np.all(xy[nodes, 0] <= 89.),
                  'Candidate actual body/fixed-body right extent89 leaves exactly six columns x80rows=480 medium cells')
            observations[name]['right_medium'] = dict(actual_body_right_mm=body_right, outer_right_mm=right,
                width_mm=float(right-body_right), column_ids=column_ids.tolist(),
                row_count=ny, column_count=len(column_ids), cell_count=len(strip_cells),
                cells=strip_cells.tolist(), all_nonbody_nonsolid_passive_void=bool(np.all(strip_ok)),
                continuous_to_outer_boundary=True, fixed_dof_union_scope='Current candidate Project merged fixed groups at newx92, not oldx84 boundary status',
                outer_nodes=right_nodes.tolist(), ux_free=ux_free.tolist(), uy_free=uy_free.tolist(),
                top_uy_fixed_nodes=right_nodes[top_right].tolist(),
                meaning='Nonbody medium existence; body-shared nodes remain constrained. No boundary-insensitivity qualification')
        masks[name] = mask.reshape(ny, nx)
    shift = (candidate['center_mm'][0]-baseline_workpiece['center_mm'][0])/dx
    check(shift == 12., 'Body translation is exactly twelve native columns without resampling')
    shift = int(shift)
    shifted = np.zeros_like(masks['baseline'])
    shifted[:, shift:] = masks['baseline'][:, :-shift]
    translated = bool(not masks['baseline'][:, -shift:].any()
                      and np.array_equal(shifted, masks['candidate']))
    check(translated, 'Actual candidate body mask is the complete twelve-column translation of baseline')
    checkpoint()
    return dict(schema_version='native-circle-tip-layout-1.0',
        scope='One resident undeformed native Project; baseline reselected on the same grid; no second model',
        coordinate_definition='Original native coordinates in mm, scale one, modeled lower half only; no mirror',
        grid=deepcopy(grid), mechanism_physical_edges=mechanism_edges.tolist(),
        symmetry_cut_excluded_y_mm=top, tip_reference_mm=list(TIP_REFERENCE_MM),
        baseline=observations['baseline'], candidate=observations['candidate'],
        historical_geometry_margin=dict(old_center_mm=[74., 40.], old_domain_right_mm=84.,
            old_body_right_mm=83., width_mm=1.,
            scope='Previously saved undeformed x74/old84 geometric margin only; not new92 baseline strip or old boundary DOF reconstruction'),
        translation=dict(dx_mm=6., native_columns=shift, masks_equal_after_complete_shift=translated),
        interpretation=dict(boundaries='Finite straight Q1 staircase edges; analytic circle is reference display only',
            nearest_and_tip='Distinct unsigned distances, not signed normal gaps or pressure',
            right_boundary='No imposed right ux clamp; right uy fixed only at the original top symmetry node',
            material='Body is a fixed kinematic overlay; right strip remains original medium, not a new material',
            containment_tested=False, boundary_influence_qualified=False, contact_qualified=False),
        mechanics=dict(force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
            zero_basis='Only resident array selection and the two declared boundary observations; no dynamic mechanical hooks'))


def plot_layout(project, layout, output_png, checkpoint):
    """Write one new four-panel PNG from resident arrays and layout, no reads."""
    checkpoint()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection, PolyCollection
    from matplotlib.patches import Arc, Rectangle

    output = Path(output_png)
    if output.exists():
        raise FileExistsError('Choose a new layout PNG: '+str(output))
    xy, conn = project.model.coordinates, project.model.connectivity
    solid = project.model.solid
    colors = {'baseline': '#21807c', 'candidate': '#ba5528'}
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)

    def draw(ax, *, circles=False):
        ax.add_collection(PolyCollection(xy[conn[solid]], facecolors='#517d9d',
            edgecolors='none', rasterized=True))
        for name in ('baseline', 'candidate'):
            item = layout[name]
            edges = np.asarray(item['physical_edges'], dtype=np.int64)
            ax.add_collection(LineCollection(xy[edges], colors=colors[name], linewidths=1.2,
                linestyles='--' if name == 'baseline' else '-', label=name+' actual Q1 boundary'))
            if circles:
                ax.add_patch(Arc(item['definition']['center_mm'], 18., 18., theta1=180., theta2=360.,
                    color=colors[name], linestyle=':', linewidth=.9, label=name+' analytic reference'))
        ax.axhline(40., color='#777777', ls=':', lw=.7)
        ax.axvline(80., color='#777777', ls='--', lw=.7, label='Original LF right x80')
        ax.axvline(84., color='#777777', ls='--', lw=.7, label='Previous HF right x84 (historical reference)')
        ax.axvline(92., color='#222222', lw=.9, label='New analysis right x92')
        ax.set_aspect('equal')
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')

    try:
        ax = axes[0, 0]
        draw(ax)
        ax.scatter(*TIP_REFERENCE_MM, color='#d49a12', s=22, label='Reference tip (80,30)', zorder=5)
        for name, length in (('input', 2.), ('output', 1.5)):
            port = project.region_metadata['ports'][name]
            point = np.mean(np.asarray(port['points_mm']), axis=0)
            direction = np.asarray(port['direction'])*length
            ax.annotate('', xy=point+direction, xytext=point,
                arrowprops=dict(arrowstyle='->', color='#792d7e', lw=1.3))
            ax.text(*(point+direction), name+' reference', fontsize=7)
        ax.set_xlim(-2., 94.)
        ax.set_ylim(-1., 42.)
        ax.set_title('Undeformed full domain | x1 | lower half, no mirror')
        ax.legend(fontsize=7, loc='lower right')
        checkpoint()
        ax = axes[0, 1]
        draw(ax, circles=True)
        for name in ('baseline', 'candidate'):
            item = layout[name]
            pair = item['boundary']['closest_pair']
            points = np.asarray([pair['mechanism_point_mm'], pair['workpiece_point_mm']])
            ax.plot(*points.T, '-.', color=colors[name], linewidth=1.3,
                label=f"{name} nearest {item['boundary']['minimum_boundary_distance_mm']:.6g} mm")
            points = np.asarray([TIP_REFERENCE_MM, item['tip']['point_mm']])
            ax.plot(*points.T, '--', color=colors[name], linewidth=.9,
                label=f"{name} tip {item['tip']['distance_mm']:.6g} mm")
        ax.scatter(*TIP_REFERENCE_MM, color='#d49a12', s=22, zorder=5)
        ax.set_xlim(63., 93.)
        ax.set_ylim(27., 41.)
        ax.set_title('Actual finite-edge witnesses | both distances unsigned')
        ax.legend(fontsize=6.5, loc='lower left')
        checkpoint()
        ax = axes[1, 0]
        draw(ax)
        item = layout['candidate']
        strip = item['right_medium']
        ax.add_patch(Rectangle((89., 0.), 3., 40., facecolor='#d8ecd4', edgecolor='none',
            alpha=.7, label='Six-column nonbody medium strip'))
        for x in np.arange(89.5, 92., .5):
            ax.axvline(x, color='#76a66a', lw=.6)
        nodes = np.asarray(item['nodes'], dtype=np.int64)
        ax.scatter(*xy[nodes].T, s=2, c=colors['candidate'], label='Fixed body nodes')
        outer = np.asarray(strip['outer_nodes'], dtype=np.int64)
        upper = xy[outer, 1] == 40.
        ax.scatter(*xy[outer[~upper]].T, s=9, facecolors='none', edgecolors='#348a40',
            label='Outer nodes: ux/uy free')
        ax.scatter(*xy[outer[upper]].T, s=22, color='#6b3a9b', marker='s',
            label='Top outer node: ux free, uy symmetry')
        ax.set_xlim(85., 93.)
        ax.set_ylim(28., 41.)
        ax.set_title('Right upper zoom | all 80 rows checked, no right clamp')
        ax.legend(fontsize=6.5, loc='lower left')
        checkpoint()
        ax = axes[1, 1]
        ax.axis('off')
        lines = ['SAVED UNDEFORMED LAYOUT COMPARISON', '',
                 'Quantity                    x74 / old x84     x80 / new x92']
        for label, key in (('Body cells', 'cells'), ('Body nodes', 'nodes'),
                           ('Body ux/uy DOFs', 'body_dofs'), ('Physical edges', 'physical_edges')):
            lines.append(f"{label:27s} {layout['baseline']['counts'][key]:>12d} {layout['candidate']['counts'][key]:>17d}")
        for label, getter in (
            ('Nearest unsigned (mm)', lambda v: v['boundary']['minimum_boundary_distance_mm']),
            ('Tip unsigned (mm)', lambda v: v['tip']['distance_mm'])):
            lines.append(f"{label:27s} {getter(layout['baseline']):>12.7g} {getter(layout['candidate']):>17.7g}")
        lines.append(f"{'Historical/new right (mm)':27s} {layout['historical_geometry_margin']['width_mm']:>12.7g} {layout['candidate']['right_medium']['width_mm']:>17.7g}")
        lines += ['', 'x74 body/distance reselected on new92 grid only.',
                  'Old84 margin1mm is historical, not a new92 baseline.',
                  'No old84 FE model or old84 boundary DOFs rebuilt.',
                  'Actual x80 body right x89; outer right x92 mm.',
                  '6 continuous columns x 80 rows = 480 medium cells.',
                  'All right ux free; right uy free except original top uy.',
                  'Twelve-column body translation on the same new grid.',
                  'Candidate tip equals global min exactly: '+str(layout['candidate']['distance_relation']['tip_equals_global_minimum_exact']),
                  'Global firstpair only; tip exact edge ties retained.', '',
                  'Distances are geometry, not force/contact/pressure.',
                  'Containment and boundary-insensitivity are not qualified.',
                  'No displacement, equilibrium or loaded response evaluated.']
        ax.text(0., .98, '\n'.join(lines), transform=ax.transAxes, va='top',
                fontsize=8.5, family='monospace', linespacing=1.6)
        fig.suptitle('Circle r9 at y40: x74 to x80 | h=.5 retained, HF right explicitly extended84 to92\n'
            'True reference coordinates x1; only undeformed geometry and imposed-DOF observations', fontsize=13)
        checkpoint()
        fig.savefig(output, dpi=170)
        checkpoint()
    finally:
        plt.close(fig)
    return dict(file=output.name, panel_count=4, scale=1., mirror=False,
        modeled_extent='lower_half', coordinate_units='mm', image_dpi=170,
        baseline_center_mm=[74., 40.], candidate_center_mm=[80., 40.], radius_mm=9.,
        old_domain_right_reference_mm=84., current_domain_right_mm=92.,
        baseline_scope='Only x74 body/boundary/tip geometry reselected on the resident new92 grid; old84 margin is historical',
        equality_scope='Tip/global exact distance equality does not establish a unique nearest point or first contact',
        tip_reference_mm=list(TIP_REFERENCE_MM),
        right_zoom_scope='x85..93/y28..41 display; full-height strip checked in layout',
        source_data='Resident one-Project arrays and returned layout only; no file inputs',
        force_or_pressure_displayed=False, equilibrium_or_contact_qualified=False)
