"""Read-only canonical release metadata verification, without credential output."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[2]
ops = Path(__file__).resolve().parent
index = json.loads((root / '.github_handoff/c2_s0_workspace/handoff/evidence_assets.json').read_text(encoding='utf-8'))
result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
    capture_output=True, text=True, check=True, timeout=30,
    env={**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never'})
credential = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
request = urllib.request.Request('https://api.github.com/repos/dudaxing/Compliant-TO-TMC/releases/tags/hf4-c2-s0-evidence-v1',
    headers={'Authorization': 'Bearer ' + credential['password'], 'Accept': 'application/vnd.github+json',
             'User-Agent': 'S0-readonly-confirmation'})
with urllib.request.urlopen(request, timeout=60) as response:
    release = json.load(response)
assert not release['draft'] and release['tag_name'] == 'hf4-c2-s0-evidence-v1'
assert release['target_commitish'] == 'd70d5a63e3f52bda687cb73b0058a339bf16811f'
assets = [a for a in index['assets'] if a.get('release_tag') == release['tag_name']]
assert len(assets) == len(release['assets']) == 6
checked = []
for asset in assets:
    matches = [r for r in release['assets'] if r['name'] == asset['name']]
    assert len(matches) == 1
    remote = matches[0]
    assert remote['size'] == asset['bytes']
    assert remote['digest'] == 'sha256:' + asset['sha256']
    assert remote['browser_download_url'] == asset['url']
    checked.append(dict(name=asset['name'], bytes=asset['bytes'], sha256=asset['sha256'],
                        server_digest=remote['digest'], canonical_url=remote['browser_download_url'], status='pass'))
receipt = dict(schema='s0-publication-confirmation-v1', status='pass',
    observed_utc=datetime.now(timezone.utc).isoformat(), access='authenticated_read_only_api',
    unauthenticated_metadata_attempt='Shared-IP GitHub API rate limit; no metadata result was used.',
    release_url=release['html_url'], tag=release['tag_name'], target_commit=release['target_commitish'],
    draft=release['draft'], asset_count=6, assets=checked,
    note='Upload receipt retains temporary draft URLs; these canonical URLs were verified after publication. Public asset downloads are verified separately without authentication.')
path = ops / 'publication_confirmation.json'
assert not path.exists()
path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='pass', asset_count=6, release_url=release['html_url'])))
