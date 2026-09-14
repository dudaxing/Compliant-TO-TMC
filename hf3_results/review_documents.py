"""Check current review links and record visual/document inspection without solving."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

root=Path(__file__).resolve().parents[1]
documents=[root/p for p in ('README.md','HF3_EVIDENCE_README.md','docs/PROJECT_STATUS.md',
    'docs/REQUIREMENTS_TRACEABILITY.md','docs/HF3_EXECUTION_PLAN.md','docs/HF3_NEAR_ZERO_DECISION.md',
    'docs/HF3_REPORT.md','hf_repo/README.md','hf_repo/docs/HF3_IMPLEMENTATION.md','hf_repo/docs/HF3_VALIDATION.md')]
publication={root/'deliverables/HF3_evaluator_and_evidence.zip',root/'deliverables/HF3_release_manifest.json',root/'HF3_CONTENT_MANIFEST.json'}
missing, checked, deferred=[],[],[]
for path in documents:
    for first,second in re.findall(r'\]\((?:<([^>]+)>|([^\s)]+))\)',path.read_text(encoding='utf-8')):
        target=first or second
        if re.match(r'^[a-z]+://',target) or target.startswith('#'):continue
        target=re.sub(r':\d+$','',unquote(target.split('#')[0]))
        resolved=(path.parent/target).resolve()
        row=dict(document=path.relative_to(root).as_posix(),target=target)
        if resolved.exists():checked.append(row)
        elif resolved in publication:deferred.append(row)
        else:missing.append(row)
assert not missing, missing
visuals=['plots_002/regions_and_background_constraints.png','plots_002/initial_model_components_and_bias.png',
    'plots_002/path_01/last_accepted_deformation_and_J.png','plots_002/path_02/last_accepted_deformation_and_J.png',
    'plots_002/path_02/accepted_path_diagnostics.png']
review=dict(status='pass',checked_links=len(checked),publication_artifacts_created_after_commit=deferred,
    document_sha256={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in documents},
    visual_inspection=dict(method='Rendered PNG images inspected through view_image; physical mm axes, port weights/directions, separate J scales, actual deformation scale and curve labels checked',
        images=visuals,conclusion='No clipped labels or contradictory physical signs observed in the inspected views; small model-component percentages are quantified in companion JSON and report tables.'),
    scientific_review=dict(conclusion='Free-output lower-half numerical pilots; no workpiece, contact accuracy, material validity or performance certification. Initial bias is not a finite-path physical error bound.',
        unresolved_HF3_numerical_gate=False,HF4_executed=False))
(root/'hf3_results/document_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='pass',links_checked=len(checked),deferred_publication_links=len(deferred))))
