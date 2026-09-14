"""Explicit CPU/float64 dependency probe, not a mechanics benchmark."""
from pathlib import Path
import importlib.metadata as metadata
import json
import platform
import time
import jax
import jax.numpy as jnp
import numpy as np

root = Path(__file__).resolve().parents[1]
assert jax.config.read('jax_enable_x64')
assert jax.default_backend() == 'cpu'
u = jnp.array([.1,.2], dtype=jnp.float64)
function = jax.jit(jax.jacfwd(lambda x: jnp.array([x[0]**2 + x[1], x[0]*x[1]])))
start = time.perf_counter()
value = np.asarray(function(u))
first = time.perf_counter() - start
start = time.perf_counter()
repeat = np.asarray(function(u))
second = time.perf_counter() - start
assert value.dtype == np.float64
np.testing.assert_allclose(value, [[.2,1],[.2,.1]], rtol=0,atol=1e-15)
record = {'scope':'HF-owned CPU float64 environment probe; not FE or speedup evidence',
          'python':platform.python_version(),'versions':{n:metadata.version(n) for n in ['numpy','scipy','matplotlib','jax','jaxlib','ml-dtypes','opt-einsum']},
          'devices':[str(d) for d in jax.devices()], 'backend':jax.default_backend(),
          'x64_enabled':bool(jax.config.read('jax_enable_x64')), 'jacobian_dtype':str(value.dtype),
          'jacobian':value.tolist(),'first_call_including_compile_seconds':first,'second_call_seconds':second,
          'bitwise_repeat':bool(np.array_equal(value,repeat))}
(root/'hf2_results/environment_probe.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
