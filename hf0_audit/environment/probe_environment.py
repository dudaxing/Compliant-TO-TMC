"""HF-0 environment smoke only; this is neither an HF solver nor a benchmark."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import sys
import time

import numpy as np
import scipy
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import spsolve
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

out = Path(__file__).resolve().parent
files = [
    Path("C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (6).zip"),
    Path("C:/Users/Lenovo/Zotero/storage/AAXN3GZJ/TMC_code.zip"),
    Path("C:/Users/Lenovo/Zotero/storage/RQ982KG5/Frederiksen et al. - 2026 - A Matlab code for analysis and topology optimization with Third Medium Contact.pdf"),
    Path("C:/Users/Lenovo/Zotero/storage/PMK9MVG8/Frederiksen et al. - 2025 - Improved third medium formulation for 3D topology optimization with contact.pdf"),
    Path("C:/Users/Lenovo/.codex/attachments/bfcef907-4575-4bc0-8f52-528e4ab637fa/pasted-text.txt"),
]
inventory = []
for file in files:
    digest = hashlib.file_digest(file.open("rb"), "sha256").hexdigest()
    inventory.append({"source_path_record_only": str(file), "bytes": file.stat().st_size, "sha256": digest})
(out / "source_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

# Deliberately nonsymmetric synthetic residual tests AD and general sparse LU.
# It is not a mechanics model and makes no scientific validation claim.
def residual(u):
    return jnp.array([u[0] ** 2 + 3 * u[1], jnp.sin(u[0]) + 2 * u[1]])

u = jnp.array([0.2, -0.1], dtype=jnp.float64)
kernel = jax.jit(jax.jacfwd(residual))
t0 = time.perf_counter()
k = np.asarray(kernel(u).block_until_ready())
cold = time.perf_counter() - t0
t0 = time.perf_counter()
kernel(u).block_until_ready()
warm = time.perf_counter() - t0
expected = np.array([[0.4, 3.0], [np.cos(0.2), 2.0]])
rhs = np.array([1.0, 2.0])
solution = spsolve(csc_matrix(k), rhs)
result = {
    "scope": "HF-0 synthetic environment smoke; not FE, MATLAB parity, or speedup evidence",
    "python_executable": sys.executable,
    "python": sys.version,
    "platform": platform.platform(),
    "logical_cpu_count": os.cpu_count(),
    "versions": {n: metadata.version(n) for n in ["numpy", "scipy", "jax", "jaxlib", "pytest", "matplotlib"]},
    "jax_devices": [str(d) for d in jax.devices()],
    "jax_backend": jax.default_backend(),
    "jax_x64": jax.config.jax_enable_x64,
    "jacobian_dtype": str(k.dtype),
    "jacobian_max_abs_error": float(np.max(np.abs(k - expected))),
    "sparse_solve_residual_l2": float(np.linalg.norm(k @ solution - rhs)),
    "synthetic_first_call_seconds_including_compile": cold,
    "synthetic_second_call_seconds": warm,
}
(out / "environment_probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
