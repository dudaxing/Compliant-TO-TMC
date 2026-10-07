def numerical_rows(model, states):
    input_dofs = np.flatnonzero(model["b_in"])
    require(len(input_dofs) == 3 and np.all(input_dofs % 2 == 0), "Canonical input port differs")
    rows = []
    for index, accepted in enumerate(states):
        record, forces = accepted["row"], accepted["forces"]
        u = accepted["state"]["lift"]+accepted["state"]["fluctuation"]
        row = dict(index=index, target_mm=float(record["d"]), q_in_mm=float(record["q_in"]),
            R_input_N=float(record["R_input"]), q_out_mm=float(record["q_out"]),
            minimum_J=float(record["minimum_J"]), relative_residual=float(record["relative_residual"]),
            constraint_residual_mm=float(record["constraint_residual"]),
            relative_global_force_balance=float(record["relative_global_force_balance"]),
            balance_x_N=float(forces["global_force_balance"][0]),
            balance_y_N=float(forces["global_force_balance"][1]),
            solid_minimum_J=float(forces["J"][model["solid"]].min()),
            medium_minimum_J=float(forces["J"][~model["solid"]].min()),
            maximum_displacement_mm=float(np.linalg.norm(u.reshape(-1, 2), axis=1).max()))
        row.update({f"input_node_{j}_ux_mm": float(u[dof]) for j, dof in enumerate(input_dofs)})
        hp = accepted["audit"]["metrics"]
        row.update(hp_relative_residual=float(hp["independent_relative_residual"]),
                   hp_relative_constraint=float(hp["relative_constraint"]),
                   hp_relative_force_balance=float(hp["relative_force_balance"]))
        rows.append(row)
    return rows, input_dofs
