"""Preserve user-supplied review bytes and check quoted source lines, without execution.

No code from the attachments is imported or executed. This does not perform
the proposed scientific-data migration or run any mechanics/tests.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = [
    (Path("C:/Users/Lenovo/Downloads/N4_P4a_对_Astra_工作的启发与取舍.md"), "comparison_review.md"),
    (Path("C:/Users/Lenovo/Downloads/source_excerpts(1).md"), "source_excerpts.md"),
    (Path("C:/Users/Lenovo/Downloads/Astra_TMC_review_evidence.zip"), "Astra_TMC_review_evidence.zip"),
    (Path("C:/Users/Lenovo/Downloads/Astra_TMC_可恢复瘦身方案.md"), "storage_proposal.md"),
    (Path("C:/Users/Lenovo/Downloads/Astra_TMC_独立审查报告.md"), "independent_review.md"),
    (Path("C:/Users/Lenovo/.codex/attachments/3920c519-002b-4b82-ad99-2507f36eb827/已粘贴的文本.txt"), "comparison_pasted.txt"),
    (Path("C:/Users/Lenovo/.codex/attachments/e2b71bb3-ebef-4565-b6ce-c6dae1c993cc/已粘贴的文本.txt"), "review_pasted.txt"),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def write_json(path, data):
    write_new(path, (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))


def main():
    # Preflight all paths before writing so previous review captures are not overwritten.
    assert all(source.is_file() for source, _ in SOURCES)
    outputs = [HERE / "inputs" / name for _, name in SOURCES]
    outputs += [HERE / "input_manifest.json", HERE / "checks/source_excerpt_check.json"]
    assert not any(path.exists() for path in outputs), "Existing capture must be preserved"
    rows = []
    for source, name in SOURCES:
        raw = source.read_bytes()
        target = HERE / "inputs" / name
        write_new(target, raw)
        assert target.read_bytes() == raw
        rows.append({"original_path": str(source), "original_name": source.name,
                     "stored_path": target.relative_to(HERE).as_posix(),
                     "bytes": len(raw), "sha256": digest(raw), "copy_byte_identical": True})
    manifest = {"schema": "external-review-input-capture-v1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "purpose": "Review-source preservation, not execution of attached proposals",
                "sources": rows, "script_sha256": digest(Path(__file__).read_bytes()),
                "no_FE_or_HP": True, "no_scientific_archive_created": True}
    write_json(HERE / "input_manifest.json", manifest)

    excerpt_text = (HERE / "inputs/source_excerpts.md").read_text(encoding="utf-8-sig")
    pattern = re.compile(r"^## (Astra|N)/(.+?) · L(\d+)–L(\d+)\n\s*```text\n(.*?)\n```", re.M | re.S)
    sections = []
    for match in pattern.finditer(excerpt_text):
        origin, relative, first, last, body = match.groups()
        base = ROOT if origin == "Astra" else ROOT / "research_integration_20260920/sources/N19"
        original = (base / relative).resolve()
        assert original.is_relative_to(base.resolve())
        raw = original.read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        entries = [re.fullmatch(r"(\d+): ?(.*)", line) for line in body.splitlines()]
        assert all(entries), (origin, relative, "malformed numbered quote")
        quoted = [(int(entry[1]), entry[2]) for entry in entries]
        assert [n for n, _ in quoted] == list(range(int(first), int(last) + 1))
        discrepancies = [{"line": n, "quoted": text, "local": lines[n-1] if n <= len(lines) else None}
                         for n, text in quoted if n > len(lines) or lines[n-1] != text]
        sections.append({"source": origin + "/" + relative,
                         "local_file": original.relative_to(ROOT).as_posix(),
                         "source_sha256": digest(raw), "first_line": int(first), "last_line": int(last),
                         "quoted_lines": len(quoted), "mismatches": discrepancies})
    assert len(sections) == len(re.findall(r"^## (?:Astra|N)/", excerpt_text, re.M)), "All quoted sections must be handled"

    zpath = HERE / "inputs/Astra_TMC_review_evidence.zip"
    with zipfile.ZipFile(zpath) as archive:
        members = [{"path": member.filename, "bytes": member.file_size,
                    "sha256": digest(archive.read(member))}
                   for member in archive.infolist() if not member.is_dir()]
        standalone = {}
        for name in ("independent_review.md", "storage_proposal.md"):
            sha = digest((HERE / "inputs" / name).read_bytes())
            standalone[name] = [m["path"] for m in members if m["sha256"] == sha]
        # These are cited by the second comparison report, but are not supplied
        # merely by having the earlier Astra-only review ZIP.
        comparison_files = ("evidence/input_identity.json", "evidence/old_baseline_checked.json",
                            "check_old_scientific_baseline.py")
        absent = [name for name in comparison_files
                  if not any(m["path"] == name or m["path"].endswith("/" + name) for m in members)]
    result = {"schema": "review-source-excerpts-check-v1",
              "input_manifest_sha256": digest((HERE / "input_manifest.json").read_bytes()),
              "excerpt_sha256": digest((HERE / "inputs/source_excerpts.md").read_bytes()),
              "sections": sections, "section_count": len(sections),
              "quoted_line_count": sum(s["quoted_lines"] for s in sections),
              "all_quoted_lines_match_local_source": all(not s["mismatches"] for s in sections),
              "zip_members": members, "standalone_reports_matching_zip_members": standalone,
              "comparison_report_cited_material_not_in_this_zip": absent,
              "limits": ["Matching quoted lines does not validate the quoted scientific interpretations.",
                         "ZIP members were read as data only; no attached scripts were executed.",
                         "External tests, N4 port arithmetic and mechanics were not rerun.",
                         "No production source, protocol or archived scientific evidence was changed."]}
    write_json(HERE / "checks/source_excerpt_check.json", result)
    print(json.dumps({"copied_inputs": len(rows), "input_bytes": sum(x["bytes"] for x in rows),
                      "section_count": result["section_count"], "quoted_line_count": result["quoted_line_count"],
                      "all_quoted_lines_match": result["all_quoted_lines_match_local_source"],
                      "missing_comparison_evidence": absent}, ensure_ascii=True))


if __name__ == "__main__":
    main()
