"""One undeformed circle-preparation figure from an already built Project."""
from pathlib import Path


def plot_circle(project, output_png, diagnostics, checkpoint):
    """Plot memory-resident model data; no file, force or saved-state reads.

    diagnostics['boundary_edges'] contains physical workpiece edge node pairs;
    the y-symmetry cut is excluded by the preparation helper. 'old_square' is
    the unchanged parent workpiece definition, used only as a reference box.
    """
    checkpoint('plot_started')
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection, PolyCollection
    from matplotlib.patches import Arc, Patch, Rectangle
    from matplotlib.lines import Line2D

    output_png = Path(output_png)
    if output_png.exists():
        raise FileExistsError(output_png)
    model, regions = project.model, project.region_metadata
    body = project.task['workpiece']
    if body['shape'] != 'circle':
        raise ValueError('This preparation figure requires a circle workpiece')
    xy, conn = model.coordinates, model.connectivity
    polygons = xy[conn]
    cells = np.asarray(regions['workpiece']['cells'], dtype=np.int64)
    nodes = np.asarray(regions['workpiece']['nodes'], dtype=np.int64)
    edges = np.asarray(diagnostics['boundary_edges'], dtype=np.int64)
    center = np.asarray(body['center_mm'], dtype=float)
    radius = float(body['radius_mm'])
    grid = project.geometry.grid
    origin, extent = np.asarray(grid['origin_mm']), np.asarray(grid['extent_mm'])
    upper = origin + extent
    spacing = np.asarray(grid['cell_size_mm'])
    # The parent square is a reference envelope, never a second model.
    old_square = diagnostics['old_square']
    square_center = np.asarray(old_square['center_mm'], dtype=float)
    square_side = float(old_square['side_mm'])
    square_lower = square_center - square_side / 2.
    square_upper = np.array([square_center[0] + square_side / 2., square_center[1]])

    palette = np.array(['#edf1f3', '#263f51', '#efaf50'])
    category = np.zeros(model.ne, dtype=np.int64)
    category[model.solid] = 1
    category[cells] = 2
    physical_color, analytic_color, square_color = '#9a3f1e', '#207c83', '#6d697a'
    local_x = (center[0] - radius - 5., min(upper[0] + .5, center[0] + radius + 3.))
    local_y = (center[1] - radius - 4., center[1] + 1.2)

    def axes_style(ax, limits):
        ax.set(xlim=limits[0], ylim=limits[1], xlabel='x (mm)', ylabel='y (mm)', aspect='equal')
        ax.set_facecolor('white')
        ax.tick_params(labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#aab4bc')

    def phases(ax, *, mesh=False):
        ax.add_collection(PolyCollection(polygons, facecolors=palette[category],
            edgecolors='#b9c3ca' if mesh else 'none', linewidths=.20 if mesh else 0.,
            rasterized=True))
        ax.add_collection(LineCollection(xy[edges], colors=physical_color, linewidths=1.5))

    def references(ax):
        ax.add_patch(Arc(center, 2 * radius, 2 * radius, theta1=180., theta2=360.,
            color=analytic_color, linestyle='--', linewidth=1.4))
        ax.add_patch(Rectangle(square_lower, square_upper[0] - square_lower[0],
            square_upper[1] - square_lower[1], fill=False, color=square_color,
            linestyle=':', linewidth=1.3))
        ax.plot(*center, marker='+', color=analytic_color, markersize=7)

    def ports(ax, *, arrows):
        colors = dict(input='#11784b', output='#2860aa')
        for name, port in regions['ports'].items():
            port_nodes = np.asarray(port['nodes'], dtype=np.int64)
            ax.scatter(*xy[port_nodes].T, s=23, facecolors='white', edgecolors=colors[name],
                linewidths=1., zorder=6)
            if arrows:
                point = np.average(xy[port_nodes], axis=0, weights=port['weights'])
                direction = np.asarray(port['direction'])
                ax.quiver(*point, *(3. * direction), angles='xy', scale_units='xy', scale=1.,
                    color=colors[name], width=.004, zorder=7)
                ax.annotate(name + ' reference direction', point, xytext=(5, -15),
                    textcoords='offset points', color=colors[name], fontsize=9)

    fig = plt.figure(figsize=(15., 10.2), facecolor='white')
    grid_spec = fig.add_gridspec(2, 2, height_ratios=[1., 1.], hspace=.34, wspace=.19,
        left=.055, right=.98, bottom=.125, top=.90)
    full = fig.add_subplot(grid_spec[0, :])
    local = fig.add_subplot(grid_spec[1, 0])
    constraints = fig.add_subplot(grid_spec[1, 1])
    try:
        phases(full)
        support = np.asarray(regions['support']['attached_nodes'], dtype=np.int64)
        entity_symmetry = np.asarray(regions['entity_symmetry']['attached_nodes'], dtype=np.int64)
        background = np.asarray(regions['background_symmetry']['selected_nodes'], dtype=np.int64)
        full.scatter(*xy[support].T, marker='s', s=13, color='#7355a2', zorder=5)
        full.scatter(*xy[entity_symmetry].T, marker='v', s=12, color='#3b8492', zorder=5)
        full.scatter(*xy[background].T, marker='.', s=9, color='#a67199', zorder=4)
        ports(full, arrows=True)
        axes_style(full, ((origin[0] - 1., upper[0] + 1.), (origin[1] - 1., upper[1] + 2.)))
        full.set_title('A. Actual lower-half model: undeformed structure, workpiece and applied constraints',
            loc='left', fontsize=11)
        full.legend(handles=[Patch(color=palette[1], label='Original mechanism solid'),
            Patch(color=palette[0], label='Free third medium'),
            Patch(color=palette[2], label='Fixed circle cell overlay'),
            Line2D([], [], marker='s', linestyle='', color='#7355a2', label='Support: ux = uy = 0'),
            Line2D([], [], marker='v', linestyle='', color='#3b8492', label='Entity symmetry: uy = 0'),
            Line2D([], [], marker='.', linestyle='', color='#a67199', label='Background symmetry: uy = 0')],
            loc='upper left', bbox_to_anchor=(0., -.13), ncol=3, fontsize=8.5, framealpha=.94)
        checkpoint('resource_check')

        phases(local, mesh=True)
        references(local)
        ports(local, arrows=False)
        axes_style(local, (local_x, local_y))
        local.set_title('B. Actual Q1 cells and physical staircase boundary', loc='left', fontsize=11)
        local.legend(handles=[Line2D([], [], color=physical_color, linewidth=1.5,
                label='Modeled physical boundary; symmetry cut excluded'),
            Line2D([], [], color=analytic_color, linestyle='--', label='Analytic semicircle: reference only'),
            Line2D([], [], color=square_color, linestyle=':',
                label=f'Previous side-{square_side:g} square envelope: reference')],
            loc='lower left', fontsize=8., framealpha=.94)
        checkpoint('resource_check')

        phases(constraints)
        references(constraints)
        fixed = np.zeros((len(xy), 2), dtype=bool)
        fixed.reshape(-1)[model.fixed_dofs] = True
        for mask, marker, color, label in (
            (fixed.all(axis=1), '.', '#7355a2', 'Actual merged ux = uy = 0 nodes'),
            (fixed[:, 1] & ~fixed[:, 0], 'v', '#3b8492', 'Actual merged uy-only nodes'),
            (fixed[:, 0] & ~fixed[:, 1], '+', '#b67121', 'Actual merged ux-only nodes')):
            if np.any(mask):
                constraints.scatter(*xy[mask].T, marker=marker, s=14, color=color, label=label, zorder=5)
        ports(constraints, arrows=False)
        axes_style(constraints, (local_x, local_y))
        constraints.set_title('C. Fixed workpiece nodes and surrounding constraints', loc='left', fontsize=11)
        constraints.legend(loc='lower left', fontsize=8., framealpha=.94)
        constraints.text(.02, .97,
            f"Circle overlay: {len(cells)} cells; {len(nodes)} nodes; "
            f"{len(regions['workpiece']['dofs'])} fixed DOFs\n"
            f"Whole model: {model.ne} cells; {model.ndof} DOFs",
            transform=constraints.transAxes, va='top', fontsize=8.5,
            bbox=dict(facecolor='white', edgecolor='none', alpha=.92))
        fig.suptitle(f'L-CPREP1 | Wave gripper + fixed circle r = {radius:g} mm, '
            f'centre ({center[0]:g}, {center[1]:g}) mm\nUNDEFORMED / NOT SOLVED',
            fontsize=14, fontweight='bold', y=.975)
        fig.text(.055, .075,
            f"Native grid h = ({spacing[0]:g}, {spacing[1]:g}) mm; plane strain; "
            'lower half only; no mirrored geometry. All coordinates are scale x1; panels B/C only zoom.',
            fontsize=9)
        fig.text(.055, .047,
            'Port arrows are reference directions, not forces. Cell-centre selection gives a staircase, not a fitted circle. '
            'No displacement, reaction, contact or pressure has been computed.', fontsize=9)
        checkpoint('resource_check')
        fig.savefig(output_png, dpi=160, facecolor='white')
    finally:
        plt.close(fig)
    checkpoint('plot_completed')
    return dict(png_file=str(output_png), panels=3, coordinate_scale=1., mirrored=False,
        workpiece_boundary='Actual exposed Q1 edges, excluding the symmetry cut',
        analytic_circle='Reference only', previous_square=f'Side-{square_side:g} envelope reference only',
        mechanics_evaluated=False, additional_input_payload_reads=0)
