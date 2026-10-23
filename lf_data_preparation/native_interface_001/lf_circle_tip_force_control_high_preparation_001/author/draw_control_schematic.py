"""High-input control schematic only; no FE shapes, caches or kernel imports."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE = Path(__file__).resolve().parent
assert not (HERE / 'control_schematic.png').exists()
blue, orange, green, ink = '#24678c', '#b65b28', '#386b50', '#243440'
fig = plt.figure(figsize=(16, 9.8), facecolor='white')
ax = fig.add_axes([.025, .04, .95, .88])
ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis('off')
fig.suptitle('High-input guided force cross-check | PREPARATION ONLY', fontsize=21, color=ink, y=.975)
ax.text(8, 8.8, 'Control diagram, not FE geometry or new deformation. High-input force solve has NOT run.',
        ha='center', fontsize=12, color='#576775')

def box(x, y, w, h, words, color=blue, size=12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08',
                 facecolor='#f4f7f9', edgecolor=color, linewidth=1.5))
    ax.text(x+w/2, y+h/2, words, ha='center', va='center', fontsize=size,
            color=ink, linespacing=1.6)

def arrow(x0, y0, x1, y1, color=blue):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>',
                 mutation_scale=15, color=color, linewidth=1.8))

box(.2, 6.45, 4.4, 1.9, 'Existing complete fixed parent\n13 loading targets: 0 -> 1.06 mm\nSelect accepted 012 / original 12\nOriginal split + signed R = 0.195223 N')
arrow(4.73, 7.4, 5.12, 7.4)
box(5.25, 6.45, 4.65, 1.9, 'Fresh nonzero preload anchor\nP0 = 2.39980095e-4 N\nNew F/T; first check must pass\nNo predictor, projection or repair', green)
arrow(10.03, 7.4, 10.42, 7.4, orange)
box(10.55, 6.45, 5.2, 1.9, 'Only prescribe absolute load P1\nP1 = 2.56157287e-4 N\nSolve unknown w, q and R\nInput mean HELD at 1.06 mm', orange)

box(.2, 4.15, 8.1, 1.65,
    'Keep r9 / center(80,40) / right92 / Lr80 / alpha2.5e-7\nHalf-model resultant N already includes thickness 20 mm\nP_full = 2 P_half; q unchanged; no moving remask\nTotal weak force retains material + Hu', blue, 11.6)
ax.add_patch(Circle((10.2, 5.05), .52, facecolor='#f4d4ae', edgecolor=orange, linewidth=2))
ax.text(10.2, 5.05, 'q = ?', ha='center', va='center', fontsize=17, color=orange)
arrow(10.85, 5.05, 13.5, 5.05, orange)
ax.text(12.2, 5.45, 'P along +x', ha='center', fontsize=13, color=orange)
ax.text(12.0, 4.12, 'Guided rigid body: uy = 0; rotation = 0', ha='center', fontsize=12, color=ink)

box(.2, 2.0, 7.5, 1.55,
    'Keep every original equilibrium gate + independent body-load gate\nFree / body relative residuals <= 1e-9; original mean gate\nJ > 0; global <= 1e-6; rigid / zero <= 8e-11 mm', green, 11.3)
box(8.05, 2.0, 7.7, 1.55,
    'Compare P1 solution to old given-q endpoint AFTER solving\nq_ref = 0.025 mm is NOT a target or initial guess\nq / all-DOF difference <= 1e-6 mm; separate R bound', orange, 11.4)
box(.2, .05, 15.55, 1.25,
    'PRESERVE OLD DIFFICULTY: direct q=0.025 -> invalid_J; internal bisection accepted 0.0125 then 0.025 mm\n'
    'Old endpoint min J = 4.1661e-4; Hu axial share about 72.58%. No contact / capacity / stability qualification.\n'
    'Candidate budget: controller3600 within science3900 + comparison60 + display/QA600 + other240 = helper4800; outer4860 s',
    '#9b7135', 11.1)
fig.savefig(HERE / 'control_schematic.png', dpi=150)
fig.savefig(HERE / 'control_schematic.svg')
plt.close(fig)
(HERE / 'SCHEMATIC_RENDER.json').write_bytes((json.dumps(dict(
    stage='L-CTIPFHIGHPREP1', status='schematic_rendered_pending_QA',
    PNG=1, SVG=1, not_FE_geometry=True, scientific_payload_reads=0,
    HF_mechanical_imports=0, force_calls=0, tangent_calls=0, solve_calls=0, HP_calls=0,
    plotted_source='Already recorded ordinary PROBE1 scalar metadata; no old media or fields',
    library_scope='Matplotlib diagram rendering only, not a mechanics computation'), indent=2)+'\n').encode())
