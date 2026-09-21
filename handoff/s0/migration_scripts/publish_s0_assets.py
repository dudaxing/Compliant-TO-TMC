"""Publish the six verified S0 assets at a new tag; never alter historical releases.

Git credential values remain in memory and are never printed or recorded.
The commit must already be available on the repository before this command.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

TAG='hf4-c2-s0-evidence-v1'
API='https://api.github.com/repos/dudaxing/Compliant-TO-TMC'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--index',type=Path,required=True)
    p.add_argument('--archives',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();assert len(a.commit)==40 and all(c in '0123456789abcdef' for c in a.commit)
    assert not a.receipt.exists(),'Choose a fresh receipt; prior attempts are never overwritten'
    index=json.loads(a.index.read_text(encoding='utf-8'))
    assets=[x for x in index['assets'] if x.get('release_tag')==TAG]
    assert len(assets)==6 and len({x['name'] for x in assets})==6
    for asset in assets:
        path=a.archives/asset['name']
        assert path.stat().st_size==asset['bytes'] and sha(path)==asset['sha256']
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,
                              capture_output=True,check=True,timeout=30,
                              env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    headers={'Authorization':'Bearer '+fields['password'],'Accept':'application/vnd.github+json',
             'User-Agent':'Compliant-TO-TMC-S0-handoff','X-GitHub-Api-Version':'2022-11-28'}
    def api(path,method='GET',body=None):
        raw=None if body is None else json.dumps(body).encode()
        request=urllib.request.Request(API+path,data=raw,method=method,
                     headers={**headers,**({'Content-Type':'application/json'} if raw is not None else {})})
        with urllib.request.urlopen(request,timeout=60) as response:return json.load(response)
    receipt={'schema':'s0-release-publication-v1','status':'running','started_utc':datetime.now(timezone.utc).isoformat(),
             'tag':TAG,'target_commit':a.commit,'source_index_sha256':sha(a.index),'assets':[]}
    def save():
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        assert api('/commits/'+a.commit)['sha']==a.commit
        matches=[r for r in api('/releases?per_page=100') if r['tag_name']==TAG]
        assert len(matches)<=1
        if matches:
            release=matches[0]
            assert release['target_commitish']==a.commit,'Existing release target differs; preserve it'
        else:
            release=api('/releases','POST',{'tag_name':TAG,'target_commitish':a.commit,
                'name':'HF4-C2-S0: recoverable scientific evidence', 'draft':True,'prerelease':False,
                'body':'Six lossless evidence assets from delivery baseline 552350cd3202432d483b4a5aa7697afbe08db12a. '
                       'This is a storage/handoff release, not a new mechanics version.\n\n'
                       'All 1099 original files, split displacement arrays, HP strings, failures and control records are preserved. '
                       'C2 remains partial: 58/59 states pass, with the fine-mesh terminal force-evaluation gate unchanged. '
                       'No new FE path or stable-F repair was performed.\n\n'
                       'See docs/HF4_C2_S0_STORAGE_REPORT.md and tools/handoff.py prepare-replay. '
                       'Per-asset and per-member SHA256 and dependency closures are in handoff/evidence_assets.json. '
                       'Historical hf-history-0.5.0 remains unchanged. No original paper PDFs or private MATLAB sources are added.'})
        receipt.update(release_id=release['id'],release_url=release['html_url']);save()
        for asset in assets:
            remote=api(f"/releases/{release['id']}/assets?per_page=100")
            assert not ({x['name'] for x in remote}-{x['name'] for x in assets}),'Unrecognized assets in this release'
            found=[x for x in remote if x['name']==asset['name']];assert len(found)<=1
            if found:
                result=found[0]
            else:
                print(json.dumps({'uploading':asset['name'],'bytes':asset['bytes']}),flush=True)
                url=urllib.parse.urlsplit(release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(asset['name']))
                conn=http.client.HTTPSConnection(url.hostname,timeout=60)
                conn.putrequest('POST',url.path+'?'+url.query)
                for key,value in {**headers,'Content-Type':'application/zip','Content-Length':str(asset['bytes'])}.items():conn.putheader(key,value)
                conn.endheaders()
                with (a.archives/asset['name']).open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):conn.send(block)
                response=conn.getresponse();raw=response.read();status=response.status;conn.close()
                if status!=201:raise RuntimeError('Upload HTTP '+str(status))
                result=json.loads(raw)
            assert result['state']=='uploaded' and result['size']==asset['bytes']
            assert result.get('digest')=='sha256:'+asset['sha256'],'Server digest differs'
            receipt['assets'].append({'name':asset['name'],'id':result['id'],'bytes':result['size'],
                'sha256':asset['sha256'],'server_digest':result['digest'],'url':result['browser_download_url']})
            save();print(json.dumps({'verified':asset['name']}),flush=True)
        published=api(f"/releases/{release['id']}",'PATCH',{'draft':False,'make_latest':'false'})
        assert not published['draft']
        receipt.update(status='published_server_hashes_match',published_at=published['published_at']);save()
        print(json.dumps({'status':receipt['status'],'url':published['html_url']}),flush=True)
    except Exception as error:
        # Do not include HTTP headers, credentials, server bodies or raw requests.
        receipt.update(status='failed_preserved',error_type=type(error).__name__)
        if isinstance(error,urllib.error.HTTPError):receipt['http_status']=error.code
        save();print(json.dumps({'status':receipt['status'],'error_type':type(error).__name__}),flush=True)
        raise SystemExit(1)

if __name__=='__main__':main()
