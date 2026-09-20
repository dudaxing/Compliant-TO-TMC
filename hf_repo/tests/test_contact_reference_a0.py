import numpy as np
import pytest

from hf_eval.contact_reference_a0 import closed_plane_problem


@pytest.mark.parametrize("h", [.25, .125])
@pytest.mark.parametrize("amplitude", [0., .125, .25])
def test_closed_plane_contract(h, amplitude):
    p = closed_plane_problem(h, amplitude)
    m = p.model
    assert m.kr == 0 and m.solid.all()
    assert m.ne == int(2 / h) * int(1 / h)
    assert len(m.fixed_dofs[m.fixed_dofs % 2 == 0]) == 1
    assert m.coordinates[m.fixed_dofs[m.fixed_dofs % 2 == 0][0] // 2].tolist() == [1., 0.]
    assert np.array_equal(p.lift_shape[m.fixed_dofs], p.direction[m.fixed_dofs])
    assert not np.any(p.direction[m.free])
    assert not np.any(p.direction[2 * p.top_nodes + 1])
    assert np.min(p.direction[2 * p.bottom_nodes + 1]) == 1 - 2 * amplitude
    assert np.max(p.direction[2 * p.bottom_nodes + 1]) == 1 + amplitude
    for nodes, name in ((p.top_nodes, "top"), (p.bottom_nodes, "bottom")):
        assert np.array_equal(np.flatnonzero(p.reaction_groups[name]), 2 * nodes + 1)
        assert not np.any(p.reaction_groups[name][m.free])


@pytest.mark.parametrize("h,a", [(True, 0.), (.25, True), (.5, 0.), (.25, .5), (float('nan'), 0.)])
def test_undeclared_tasks_rejected(h, a):
    with pytest.raises(ValueError):
        closed_plane_problem(h, a)
