from pathlib import Path
from pypdf import PdfReader
import json
sources = {
  'frederiksen_2026': Path(r'C:/Users/Lenovo/Zotero/storage/RQ982KG5/Frederiksen et al. - 2026 - A Matlab code for analysis and topology optimization with Third Medium Contact.pdf'),
  'frederiksen_2025': Path(r'C:/Users/Lenovo/Zotero/storage/PMK9MVG8/Frederiksen et al. - 2025 - Improved third medium formulation for 3D topology optimization with contact.pdf')
}
for stem, path in sources.items():
    reader=PdfReader(path)
    out=Path('hf0_audit/papers')/stem
    out.mkdir(exist_ok=True)
    lines=[]
    for i,p in enumerate(reader.pages):
        t=p.extract_text(extraction_mode='layout')
        (out/f'page_{i+1:02d}.txt').write_text(t,encoding='utf-8')
        lines.append(f'\n\n======== PDF PAGE {i+1} ========\n'+t)
    (out/'full_text.txt').write_text(''.join(lines),encoding='utf-8')
    print(stem,len(reader.pages),json.dumps(dict(reader.metadata or {}),ensure_ascii=True))

