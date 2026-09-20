"""Freeze and prepare the C2 publication whitelist; never commit or push.

Run only after the final report and all source evidence have been frozen.
Draft until final report/evidence are explicitly frozen. No mode commits or pushes.
Every output receipt is exclusive-create, and a dirty publication clone stops
the preparation. This tool does not interpret mechanical admission status.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".github_handoff/Compliant-TO-TMC"
SOURCE = ROOT / "hf_repo"
BASE = "04e57aa82bf173780c1db92d143588000791b87e"
TAG = "hf-history-0.5.0"
TAG_OBJECT = "bde0d945255ce48bd0369ae6cec73005373daaa5"
TAG_COMMIT = "14e107d147c8813579db8bf740a79774942b30b2"
MANIFEST = "handoff/repository_manifest.json"
ENTRIES = {"README.md", "docs/RESUME_DEVELOPMENT.md"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".venv", "tmp", "temp"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".tmp", ".partial", ".bak"}
SECRET_PATTERNS = [r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{40,}",
                   r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}",
                   r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True, encoding="utf-8").strip()


def safe(root, name):
    rel = PurePosixPath(name)
    require(bool(rel.parts) and not rel.is_absolute() and ".." not in rel.parts
            and "\\" not in name and ":" not in name, "Unsafe relative path: " + name)
    path = root.joinpath(*rel.parts)
    require(path.resolve().is_relative_to(root.resolve()), "Escaping path: " + name)
    return path


def record(path, name):
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def baseline():
    require(git(DEST, "rev-parse", "HEAD") == BASE, "Publication HEAD changed")
    require(not git(DEST, "status", "--porcelain"), "Publication clone must be clean")
    refs = dict(line.split()[::-1] for line in git(DEST, "ls-remote", "origin",
                "refs/heads/main", "refs/tags/" + TAG, "refs/tags/" + TAG + "^{}").splitlines())
    require(refs.get("refs/heads/main") == BASE, "Remote main changed; stop without overwriting")
    require(refs.get("refs/tags/" + TAG) == TAG_OBJECT
            and refs.get("refs/tags/" + TAG + "^{}") == TAG_COMMIT, "Stable remote tag changed")
    require(git(DEST, "rev-parse", TAG) == TAG_OBJECT, "Stable local tag changed")
    manifest = json.loads(git(DEST, "show", BASE + ":" + MANIFEST))
    require(len(manifest["files"]) == 3021, "Unexpected baseline payload count")
    for item in manifest["files"]:
        path = safe(DEST, item["path"])
        require(record(path, item["path"]) == item, "Baseline payload differs: " + item["path"])
    return manifest


def selection(manifest):
    published = {item["path"]: item for item in manifest["files"]}
    selected, excluded = {}, []
    names = git(SOURCE, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in filter(None, names):
        path = PurePosixPath(name)
        if path.parts[0] not in ("configs", "scripts", "src", "tests") or path.suffix not in (".py", ".json"):
            continue
        destination = "hf_repo/" + name
        source = safe(SOURCE, name)
        if destination in published:
            require(record(source, destination) == published[destination],
                    "Already published research file changed: " + destination)
        elif "contact_c2" in path.stem:
            selected[destination] = source
    for source in sorted((ROOT / "docs").glob("HF4_C2*.md")):
        selected[source.relative_to(ROOT).as_posix()] = source
    evidence = ROOT / "hf4_c2_diagnostics"
    require(evidence.is_dir(), "C2 evidence directory is missing")
    for source in sorted(evidence.rglob("*")):
        if not source.is_file():
            continue
        name = source.relative_to(ROOT).as_posix()
        relative = source.relative_to(evidence)
        if any(part in SKIP_DIRS or part.startswith(".venv") for part in relative.parts) or source.suffix in SKIP_SUFFIXES:
            excluded.append(name)
            continue
        require(not source.is_symlink(), "Evidence symlink requires explicit review: " + name)
        require(source.suffix.lower() not in (".zip", ".7z", ".m", ".mat"),
                "Source archive/MATLAB material is outside this whitelist: " + name)
        selected[name] = source
    require("hf4_c2_diagnostics/README.md" in selected, "Missing C2 continuation README")
    require(not (set(selected) & set(published)), "C2 whitelist would replace historical evidence")
    return selected, excluded


def scan(selected):
    imports, absolute_literals = {}, []
    for name, source in selected.items():
        require(source.stat().st_size < 100 * 1024**2, "GitHub single-file limit: " + name)
        if source.suffix in (".py", ".json", ".md", ".log", ".txt", ".csv", ".svg"):
            text = source.read_text(encoding="utf-8-sig")
            require(not any(re.search(pattern, text) for pattern in SECRET_PATTERNS),
                    "Secret-pattern match requires review; filename only: " + name)
            if source.suffix == ".py":
                tree = ast.parse(text, filename=name)
                imports[name] = sorted({node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
                    | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
                absolute_literals.extend(dict(path=name, line=node.lineno)
                    for node in ast.walk(tree) if isinstance(node, ast.Constant)
                    and isinstance(node.value, str) and re.search(r"[A-Za-z]:[\\/]", node.value))
    return imports, absolute_literals


def links(selected, manifest):
    allowed = {item["path"] for item in manifest["files"]} | set(selected) | {MANIFEST}
    checked = []
    for name, source in selected.items():
        if source.suffix != ".md":
            continue
        text = re.sub(r"```.*?```", "", source.read_text(encoding="utf-8-sig"), flags=re.S)
        for match in re.finditer(r'!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+)(?:\s+"[^"]*")?)\)', text):
            link = match.group(1) or match.group(2)
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = ((DEST / name).parent / unquote(parts.path)).resolve()
            require(target.is_relative_to(DEST.resolve()), "Link escapes publication tree: " + name)
            relative = target.relative_to(DEST).as_posix()
            require(relative in allowed or any(p.startswith(relative.rstrip("/") + "/") for p in allowed),
                    "Link missing from publication whitelist: " + name + " -> " + link)
            checked.append(dict(document=name, link=link, target=relative))
    return checked


def freeze(args):
    manifest = baseline()
    selected, excluded = selection(manifest)
    require(args.final_report in selected and args.final_report.startswith("docs/HF4_C2"),
            "Final report must be a selected new docs/HF4_C2*.md file")
    replacements = {"README.md": args.entry_readme.resolve(),
                    "docs/RESUME_DEVELOPMENT.md": args.entry_resume.resolve()}
    require(all(path.is_file() for path in replacements.values()), "Final entry drafts must already exist")
    selected.update(replacements)
    imports, warnings = scan(selected)
    checked_links = links(selected, manifest)
    plan = dict(schema="c2-publication-freeze-1.0", created_utc=datetime.now(timezone.utc).isoformat(),
                baseline_commit=BASE, baseline_payload_count=3021, final_report=args.final_report,
                stable_tag=TAG, stable_tag_object=TAG_OBJECT, stable_tag_commit=TAG_COMMIT,
                files=[dict(record(source, name), source=str(source.resolve())) for name, source in sorted(selected.items())],
                excluded_temporary_files=excluded, import_inventory=imports,
                absolute_code_literals_for_review=warnings, relative_links=checked_links,
                admission_status="not inferred by publication tooling", git_index_changed=False,
                committed=False, pushed=False)
    write_new(args.output, plan)
    print(json.dumps(dict(status="frozen_plan_only", files=len(plan["files"]),
                         bytes=sum(item["bytes"] for item in plan["files"]),
                         code_literal_review_locations=warnings, output=str(args.output)), indent=2))


def prepare(args):
    require(not args.output.exists(), "Receipt already exists")
    plan = read(args.plan)
    require(plan["schema"] == "c2-publication-freeze-1.0" and plan["baseline_commit"] == BASE,
            "Plan schema or baseline differs")
    manifest = baseline()
    selected, excluded = selection(manifest)
    planned = {item["path"]: item for item in plan["files"]}
    require(len(planned) == len(plan["files"]), "Duplicate planned destination")
    require(set(planned) == set(selected) | ENTRIES, "Whitelist changed since final freeze")
    for name in ENTRIES:
        selected[name] = Path(planned[name]["source"])
    for name, source in selected.items():
        expected = {key: planned[name][key] for key in ("path", "bytes", "sha256")}
        require(record(source, name) == expected, "Source changed since freeze: " + name)
        require(source.resolve() == Path(planned[name]["source"]), "Source identity changed: " + name)
        destination = safe(DEST, name)
        require(name in ENTRIES or not destination.exists(), "New destination unexpectedly exists: " + name)
    require(excluded == plan["excluded_temporary_files"], "Temporary inventory changed since freeze")
    scan(selected)
    checked_links = links(selected, manifest)
    for name, source in selected.items():
        destination = safe(DEST, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        require(sha(destination) == planned[name]["sha256"], "Copy identity mismatch: " + name)
    immutable = [item for item in manifest["files"] if item["path"] not in ENTRIES]
    for item in immutable:
        require(record(DEST / item["path"], item["path"]) == item, "Historical payload changed: " + item["path"])
    names = {item["path"] for item in manifest["files"]} | set(planned)
    manifest["created_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["contact_c2_extension"] = dict(report=plan["final_report"],
        report_sha256=planned[plan["final_report"]]["sha256"], stable_release=TAG,
        general_HF4_C_status="open", scope="bounded C2 diagnostics; no HF5 or contact-law admission inferred",
        admission_status="see frozen report; failures and unused protocol versions retained")
    manifest["files"] = [record(DEST / name, name) for name in sorted(names)]
    (DEST / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    verification = subprocess.run([sys.executable, str(DEST / "tools/handoff.py"), "verify"],
                                  cwd=ROOT / ".github_handoff", check=True, text=True,
                                  encoding="utf-8", capture_output=True)
    require(not git(DEST, "diff", "--cached", "--name-only"), "Git index unexpectedly changed")
    receipt = dict(schema="c2-publication-prepared-1.0", status="prepared_uncommitted_requires_final_checks",
                   created_utc=datetime.now(timezone.utc).isoformat(), baseline_commit=BASE,
                   frozen_plan=str(args.plan.resolve()), frozen_plan_sha256=sha(args.plan),
                   files=[record(DEST / name, name) for name in sorted(planned)],
                   old_payload_unchanged=len(immutable), entry_documents_changed=sorted(ENTRIES),
                   manifest_payload_count=len(names), repository_verify=json.loads(verification.stdout),
                   relative_links=checked_links, release_assets_modified=False, git_index_changed=False,
                   committed=False, pushed=False, pending=["foreign-cwd saved-state HP audit in a separate temporary copy; never create details in frozen evidence",
                   "scoped staged diff check", "ordinary commit/push when authorized", "remote fresh-clone verification"])
    write_new(args.output, receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key not in ("files", "relative_links")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    frozen = commands.add_parser("freeze", help="Read-only final whitelist/hash snapshot")
    frozen.add_argument("--final-report", required=True)
    frozen.add_argument("--entry-readme", type=Path, required=True)
    frozen.add_argument("--entry-resume", type=Path, required=True)
    frozen.add_argument("--output", type=Path, required=True)
    prepared = commands.add_parser("prepare", help="Copy frozen inputs/update manifest, without git writes")
    prepared.add_argument("--plan", type=Path, required=True)
    prepared.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    (freeze if args.command == "freeze" else prepare)(args)


if __name__ == "__main__":
    main()
