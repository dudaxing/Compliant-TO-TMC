# Future softened x71 accepted-state reference (author v2)

This directory is a static author candidate. Nothing has been installed, constructed, evaluated or qualified by it.
The earlier soft author directory and both pose reference versions are preserved.

The new entry is `audit_shift_soft.py`. It imports the exact pose-v2 interface, exact B850 core and b028 pure metadata counter.
Its inherited `run_state`, workpiece checks and all mathematical gates are unchanged. The fresh reference loop is AST-identical.
Its loader accepts only the separate full softened case: E=0.5 MPa, gamma=alpha=2e-6, center(71,40), side16 mm, all eleven original targets.
Every actual accepted index, including bisections and repeated displacements, gets fresh HP80 and HP120. Failed inputs are not reevaluated or qualified.

Compared with a genuinely qualified pose002 model, exactly lam/mu/gamma/force_scale_per_length change; all other 23 arrays are identical.
Solid Lamé parameters halve. Medium Lamé parameters and global kr stay byte-identical; Et is10 N/mm and the original force-floor rule reads this stored value.
The actual `source_material_arrays_preserved=True` flag is retained. It refers to the soft task base material assignment being preserved by the body kinematic overlay, not equality to E1 materials.

`reference_contract_builder.py` only hashes/copies saved data and sources. It requires both actual complete pose002 qualification and complete soft production1800/1860.
The builder requires explicit `--reference-seconds` and `--budget-basis` once the complete soft accepted count is known; outer=helper+60 and RSS8GiB.
It writes a separate reference source closure and card. It never starts a reference or reuses a prior reference prefix.
The b028 eight-case metadata proof is bound separately and supplies no physical qualification.

Future invocation shape (not executed):
`reference_contract_builder.py --repo ROOT --input ROOT/lf_data_preparation/native_workpiece_001/shift_square_soft_001/run_001 --reference-seconds S --budget-basis ACTUAL_N_AND_COST`
Then the bound F3 launcher is called by the root only after reviewing that fresh card.

No auxiliary-energy, stress-HP, pressure/clamp/contact, all-column, H2/H3 or HF5 qualification is asserted.
