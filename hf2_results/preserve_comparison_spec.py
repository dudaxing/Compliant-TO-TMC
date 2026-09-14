"""Restore the exact explanatory-only spec revision used by comparison_001."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
original=(root/'hf_repo/validation/hf2/validation_spec.json').read_bytes()
text=original.decode('utf-8').replace('\r\n','\n')
text=text.replace('    "global_force_balance_tolerance":1e-6\n',
    '    "global_force_balance_tolerance":1e-6,\n'
    '    "global_force_balance_formula":"norm(reaction_sum+lambda*F0_sum) <= 1e-6*max(norm(lambda*F0),3*lambda)"\n')
expected='5dfac16148a729fde2a54d65d6c7d201489d316cd4b57b2f8923c27335579433'
for content in [text.encode('utf-8'),text.replace('\n','\r\n').encode('utf-8')]:
    if hashlib.sha256(content).hexdigest()==expected:
        target=root/'hf2_results/cshape_comparison_001/validation_spec_used.json'
        target.write_bytes(content)
        print('Exact original comparison spec bytes recovered and archived:',expected)
        break
else:
    raise RuntimeError('Could not reconstruct the recorded spec bytes exactly')
