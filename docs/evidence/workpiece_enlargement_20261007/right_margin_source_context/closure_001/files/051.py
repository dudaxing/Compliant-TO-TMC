"""Install reviewed raw proposals using short archive names after a path-only failure."""
import argparse
import hashlib
import json
from pathlib import Path

CONTEXT = 'docs/evidence/workpiece_enlargement_20261007/right_margin_source_context'
NAMES = {'README.md', 'hf_repo/README.md', 'docs/CURRENT_STATUS.md',
         'docs/RESUME_DEVELOPMENT.md', 'docs/WORKPIECE_ENLARGEMENT_20261007.md',
         'docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--author', type=Path, required=True)
    args = parser.parse_args()
    repo, author = args.repo.resolve(), args.author.resolve()
    selection_path = author / 'installation_candidate/archive_selection.json'
    selection = read_json(selection_path)
    destination = repo / CONTEXT / 'closure_001'
    assert (repo / CONTEXT).is_dir()
    assert not (destination / 'documentation_install.json').exists(), 'already installed'
    assert not destination.exists() or destination.is_dir()
    blobs = {}
    for name, expected in selection['archive_files'].items():
        data = (author / name).read_bytes()
        assert sha(data) == expected['sha256'] and len(data) == expected['size_bytes'], name
        blobs[name] = data
    for name, expected in selection['existing_formal_files'].items():
        assert sha((repo / expected['repo_path']).read_bytes()) == expected['sha256'], name
    summary = read_json(author / 'final_doc_proposals_001/final_summary.json')
    review = read_json(author / 'final_documentation_review.json')
    assert summary['status'] == 'complete_mechanical_reference_views_project_incomplete'
    assert review['status'] == 'pass_saved_only' and not review['blocking_findings']
    assert summary['proposal_sha256'] == review['proposal_sha256']
    assert set(summary['proposal_sha256']) == NAMES
    summary_sha = sha(blobs['final_doc_proposals_001/final_summary.json'])
    assert summary_sha in review['readback_pins'].values()
    saved_review = read_json(author / 'final_saved_result_review.json')
    inspection = read_json(author / 'image_inspection_001/gif_inspection.json')
    assert saved_review['status'] == 'pass_saved_only'
    assert inspection['status'] == 'pass' and inspection['new_scientific_calls'] == 0
    before, proposals = {}, {}
    for name, expected_after in summary['proposal_sha256'].items():
        before[name] = (repo / name).read_bytes()
        assert sha(before[name]) == summary['input_json_and_figure_sha256'][name], name
        proposals[name] = blobs['final_doc_proposals_001/proposals/' + name]
        assert sha(proposals[name]) == expected_after, name
    # All raw identities are checked before the first repository write.
    partial = {}
    if destination.exists():
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                data = path.read_bytes()
                partial[path.relative_to(destination).as_posix()] = {'sha256': sha(data), 'size_bytes': len(data)}
    destination.mkdir(exist_ok=True)
    archived = {}
    def archive(relative, data):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            assert path.read_bytes() == data, relative
        else:
            path.write_bytes(data)
        assert path.read_bytes() == data, relative
        archived[relative] = {'sha256': sha(data), 'size_bytes': len(data)}
    short_map = {}
    for number, (name, data) in enumerate(blobs.items(), 1):
        short_map[name] = f'files/{number:03d}{Path(name).suffix}'
        archive(short_map[name], data)
    number = len(blobs)
    selection_short = f'files/{number + 1:03d}.json'
    helper_short = f'files/{number + 2:03d}.py'
    partial_short = f'files/{number + 3:03d}.json'
    archive(selection_short, selection_path.read_bytes())
    archive(helper_short, Path(__file__).read_bytes())
    partial_record = {'status': 'retained_partial_file_archive',
                      'failure': 'WinError206 path too long during original archive; before six formal writes',
                      'formal_preimages_still_match': True, 'new_scientific_calls': 0,
                      'files': partial, 'policy': 'retained in place; no delete, move or rewrite'}
    archive(partial_short, (json.dumps(partial_record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    before_map = {}
    for number, (name, data) in enumerate(before.items(), 1):
        before_map[name] = f'before/{number:03d}{Path(name).suffix}'
        archive(before_map[name], data)
    index = """# Right-medium margin closure archive\n\nThis is a selected ordinary source/review/documentation archive, not another scientific run.\nSix reviewed proposals were installed as raw bytes. Their recorded before/after identities\nand all archived file identities are in documentation_install.json. Author material that\nalready has the same raw SHA in a formal stage is referenced by archive_selection.json\nrather than copied again. No model/state/NPZ/PNG/GIF or large source capsule is duplicated.\n\nHistorical candidate README/notes, interim banners and source-phase snapshots describe\ntheir authoring time; pending wording there is not current scientific status. Absolute\nauthor paths are provenance only. Current results remain in the formal production,\nreference and functional_views stages and the current main report.\n\nThe fixed-body side18/right2col comparison has peak total Fy +0.1883%, regularization\nFy 4.267 times, while max |Hu| changes only +0.0576%; early loading total Fy changes\nabout +14 to +32%. This does not establish pressure, friction, free-body or domain/mesh\nconvergence. The next proposed comparison is 2 to 4 mm right margin at the same h=1 mm.\n\nroot_physical_interpretation.md is the root's planned subsequent report append. The\nreviewed six proposals are retained unchanged, including their historical reference\nstatus snapshot. Root will separately move that snapshot to prior_reference_snapshot\nand record the actual current reference PASS in a document-only revision. This archive\nreceipt covers the six-proposal installation before that separately recorded revision.\n\n## Selected files\n\n"""
    index += 'The original path-only archive failure retained the partial nested files. It changed no formal documents and called no science; this flat installation preserves those files.\n\n'
    for name in sorted(blobs):
        index += '- [' + name + '](' + short_map[name] + ')\n'
    index += '\n[Selection](' + selection_short + '), [flat helper](' + helper_short + '), [retained partial snapshot](' + partial_short + ').\n'
    archive('INDEX.md', index.encode('utf-8'))
    installed = {}
    for name, data in proposals.items():
        (repo / name).write_bytes(data)
        assert (repo / name).read_bytes() == data, name
        installed[name] = {'before_sha256': sha(before[name]), 'after_sha256': sha(data),
                           'proposal_path': short_map['final_doc_proposals_001/proposals/' + name],
                           'before_path': before_map[name]}
    receipt = {'schema_version': 'right-margin-documentation-install-1.0',
               'status': 'pass_raw_proposal_install', 'invocations': 1,
               'scope': 'six reviewed proposals plus selected ordinary archive; no science',
               'installed_files': installed, 'proposal_sha256': summary['proposal_sha256'],
               'final_summary_sha256': summary_sha,
               'final_documentation_review_sha256': sha(blobs['final_documentation_review.json']),
               'archive_selection_sha256': sha(selection_path.read_bytes()),
               'archive_files': archived, 'archive_source_map': short_map,
               'archive_selection_path': selection_short, 'flat_helper_path': helper_short,
               'flat_helper_sha256': sha(Path(__file__).read_bytes()),
               'retained_partial_snapshot_path': partial_short, 'retained_partial_files': partial,
               'ordinary_installation_failure': 'original WinError206; zero formal writes and zero science',
               'archive_file_count': len(archived),
               'archive_total_bytes': sum(v['size_bytes'] for v in archived.values()),
               'existing_formal_files': selection['existing_formal_files'],
               'all_copied_bytes_match': True, 'new_scientific_calls': 0,
               'subsequent_root_document_only_revision': 'not covered by this installation receipt'}
    dump(destination / 'documentation_install.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': str(destination / 'documentation_install.json'),
                      'installed_files': len(installed), 'archive_files': len(archived),
                      'archive_bytes': receipt['archive_total_bytes']}))


if __name__ == '__main__':
    main()
