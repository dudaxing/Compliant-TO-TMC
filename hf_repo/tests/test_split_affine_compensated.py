"""The v4 path solver is the frozen split_affine controller with exactly one different line (the kernel import).

The complete frozen controller test module (tests/test_split_affine.py, unchanged) is re-run against the copy:
its own analytic spring stub replaces the module's assemble_split, so no FE kernel is ever evaluated here.
"""
import importlib.util
from pathlib import Path

from hf_eval import split_affine, split_affine_compensated, split_kernel, split_kernel_compensated

ROOT = Path(__file__).resolve().parents[1]
KERNEL_IMPORT = (b"from .split_kernel import assemble_split\n", b"from .split_kernel_compensated import assemble_split\n")


def test_only_the_kernel_import_line_differs():
    frozen = (ROOT / "src/hf_eval/split_affine.py").read_bytes().splitlines(keepends=True)
    copy = (ROOT / "src/hf_eval/split_affine_compensated.py").read_bytes().splitlines(keepends=True)
    assert len(frozen) == len(copy)
    assert [(index, a, b) for index, (a, b) in enumerate(zip(frozen, copy)) if a != b] == [(18, *KERNEL_IMPORT)]


def test_each_module_evaluates_through_its_own_kernel():
    assert split_affine_compensated.assemble_split is split_kernel_compensated.assemble_split
    assert split_affine.assemble_split is split_kernel.assemble_split
    assert split_affine_compensated.solve_split_affine_path is not split_affine.solve_split_affine_path


_spec = importlib.util.spec_from_file_location("frozen_split_affine_tests_on_v4_copy", ROOT / "tests/test_split_affine.py")
_frozen_tests = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frozen_tests)
# The frozen helper installs its spring stub on `control`; pointing it at the copy re-runs every test on the copy.
_frozen_tests.control = split_affine_compensated
for _name in dir(_frozen_tests):
    if _name.startswith("test_"):
        globals()["test_v4_copy__" + _name[5:]] = getattr(_frozen_tests, _name)
