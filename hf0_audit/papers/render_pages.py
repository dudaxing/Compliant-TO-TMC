from pathlib import Path
import subprocess,json
render=Path(r'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
sources=[('frederiksen_2026',r'C:/Users/Lenovo/Zotero/storage/RQ982KG5/Frederiksen et al. - 2026 - A Matlab code for analysis and topology optimization with Third Medium Contact.pdf',[2,3,4,5,11,14,15,18,19]),('frederiksen_2025',r'C:/Users/Lenovo/Zotero/storage/PMK9MVG8/Frederiksen et al. - 2025 - Improved third medium formulation for 3D topology optimization with contact.pdf',[3,4,5,6,8,11,14,16])]
manifest=[]
for stem,path,pages in sources:
    for page in pages:
        prefix=Path('hf0_audit/papers')/stem/f'page_{page:02d}'
        subprocess.run([str(render),'-f',str(page),'-l',str(page),'-r','110','-singlefile','-png',path,str(prefix)],check=True,capture_output=True)
        manifest.append({'source':path,'pdf_page':page,'render':str(prefix.with_suffix('.png').resolve())})
Path('hf0_audit/papers/render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Rendered {len(manifest)} pages')
