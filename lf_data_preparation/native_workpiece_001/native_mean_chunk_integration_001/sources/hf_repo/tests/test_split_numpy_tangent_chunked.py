"""Three focused cases for optional element-chunked DD tangents; no path solves."""
import numpy as np
import pytest

from hf_eval import split_kernel_invariants_hu as force
from hf_eval import split_numpy_tangent as tangent
from hf_eval.tmc import TMCModel, rectangular_model
from hf_eval.tmc_kernel import KernelError


@pytest.fixture(autouse=True)
def forbid_compilation(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Chunked NumPy tangent invoked compiled work")
    for name in ("_runtime", "_batch_with_tangent", "_batch_without_tangent"):
        monkeypatch.setattr(force, name, forbidden)


def example(kind):
    # 257 shared-node cells expose a one-cell tail after the default 256 block.
    base = rectangular_model(257, 1, 257., 1., alpha=0., fixed_dofs=(0, 1))
    model = TMCModel(base.coordinates, base.connectivity,
                     np.linspace(1., 2., 257), np.linspace(2., 3., 257),
                     kr=1./8, hx=1., hy=1., fixed_dofs=base.fixed_dofs)
    x, y = model.coordinates.T
    if kind == "mixed":
        profile = np.maximum(x-256., 0.)*y
        w = np.column_stack((profile/8., -profile/16.)).ravel()
    else:
        profile = (x.astype(int) % 2)*y
        w = np.column_stack((2.**-96*profile, -2.**-97*profile)).ravel()
    local = w[model.edofs]
    fields = force.batch_response_split_mechanical_numpy(
        np.zeros_like(local), local, model.ops, model.lam, model.mu, model.kr)
    return model, fields


@pytest.mark.parametrize("kind,selected", [("mixed", False), ("tiny", True)])
def test_chunks_keep_global_branch_all_tensor_words_layout_and_full_csc(kind, selected, monkeypatch):
    model, fields = example(kind)
    old = tangent._tangent(fields, model.ops, model.lam, model.mu, model.kr)
    selector, pairs = tangent._small_product_branch, tangent._tangent_pairs
    selections, blocks = [], []

    def observed_selector(G, near, operands):
        answer = selector(G, near, operands)
        selections.append((len(G[0]), bool(answer)))
        return answer

    def observed_pairs(local, *args):
        blocks.append(len(local["residual"]))
        return pairs(local, *args)

    monkeypatch.setattr(tangent, "_small_product_branch", observed_selector)
    monkeypatch.setattr(tangent, "_tangent_pairs", observed_pairs)
    actual = tangent._tangent_chunked(fields, model.ops, model.lam, model.mu, model.kr)
    assert selections == [(257, selected)] and blocks == [256, 1]
    assert set(actual) == set(old) == {"total_tangent", "material_tangent", "regularization_tangent"}
    for name, values in old.items():
        assert actual[name].shape == values.shape == (257, 8, 8)
        assert actual[name].dtype == values.dtype == np.float64
        assert actual[name].strides == values.strides
        assert actual[name].tobytes(order="C") == values.tobytes(order="C")
    if kind == "mixed":
        assert np.count_nonzero(fields["Hu"][:256]) == 0
        assert np.linalg.norm(old["regularization_tangent"][-1]-old["regularization_tangent"][-1].T) > 0.
    old_K = tangent._assemble_tangent(model, old["total_tangent"])
    actual_K = tangent._assemble_tangent(model, actual["total_tangent"])
    assert old_K.shape == actual_K.shape == (model.ndof, model.ndof)
    for name in ("data", "indices", "indptr"):
        left, right = getattr(old_K, name), getattr(actual_K, name)
        assert left.dtype == right.dtype and left.tobytes() == right.tobytes()
    assert actual_K[model.fixed_dofs, :].nnz > 0 and actual_K[:, model.fixed_dofs].nnz > 0


def test_unsupported_dd_components_keep_global_field_reporting_priority(monkeypatch):
    model, fields = example("mixed")
    fields["residual"] = fields["residual"].copy()
    fields["residual"][:, 0] = np.arange(257)

    def unsupported_pairs(local, *args):
        # Controlled support-gate fixture, not a constitutive reference: material
        # fails in the first block, while the higher-priority total fails last.
        ids = local["residual"][:, 0].astype(int)
        output = {name: (np.zeros((len(ids), 8, 8)), np.zeros((len(ids), 8, 8)))
                  for name in ("total_tangent", "material_tangent", "regularization_tangent")}
        output["material_tangent"][0][ids == 0, 0, 0] = np.inf
        output["total_tangent"][0][ids == 256, 0, 0] = np.inf
        return output

    monkeypatch.setattr(tangent, "_tangent_pairs", unsupported_pairs)
    for evaluate in (tangent._tangent, tangent._tangent_chunked):
        with pytest.raises(KernelError) as captured:
            evaluate(fields, model.ops, model.lam, model.mu, model.kr)
        assert captured.value.code == "unsupported_arithmetic_range"
        assert captured.value.details["field"] == "total_tangent"
