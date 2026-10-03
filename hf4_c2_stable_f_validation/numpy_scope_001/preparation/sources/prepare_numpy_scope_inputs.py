"""Extract exact old inputs and HP strings for the NumPy scope comparison.

No candidate mechanics, HP evaluation, JAX runtime, or equilibrium solve runs.
The extracted references are a recovery product of the existing frozen corpus.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time

import numpy as np

ORIGINAL = "hf4_c2_independent_recheck_20260927/manufactured_001/results"
SAVED = "hf4_c2_stable_f_validation/saved_all_c2_001/driver_output"
HP_KEYS = ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal",
           "tangent_action_decimal", "material_tangent_action_decimal",
           "regularization_tangent_action_decimal")


def native(path):
    if str(path).startswith("\\\\?\\"):
        return Path(path)
    path = Path(path).resolve()
    return Path("\\\\?\\" + str(path)) if os.name == "nt" else path


def sha(path):
    with native(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path):
    with native(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def write(path, value):
    with native(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def require(ok, message):
    if not ok:
        raise ValueError(message)


class Corpus:
    def __init__(self, source):
        self.source = Path(source).resolve()
        self.manifest = self.source.parent / "input_manifest.json"
        self.records = {r["path"]: r for r in read(self.manifest)["files"]}
        self.bound = {}

    def path(self, name):
        require(name in self.records or "data/" + name in self.records, "unbound source: " + name)
        key = name if name in self.records else "data/" + name
        path = self.source.parent / key
        require(path.resolve().is_relative_to(self.source.parent), "source path escape")
        row = self.records[key]
        require(native(path).stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "frozen source changed: " + key)
        self.bound[key] = row["sha256"]
        return native(path)

    def json(self, name):
        return read(self.path(name))

    def npz(self, name):
        with np.load(self.path(name), allow_pickle=False) as archive:
            return {key: archive[key] for key in archive.files}


def helper(corpus):
    path = corpus.path("source/hf_repo/scripts/validate_contact_c2_stable_f.py")
    spec = importlib.util.spec_from_file_location("scope_input_binding_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference(pair, ndof):
    out = {}
    for precision in (80, 120):
        fields = pair[str(precision)]
        out["hp" + str(precision)] = {}
        for key in HP_KEYS:
            values = fields[key]
            require(len(values) == ndof and all(isinstance(v, str) and Decimal(v).is_finite() for v in values),
                    "HP vector shape, type or finiteness changed: " + key)
            out["hp" + str(precision)][key] = values
    return out


def validate_arrays(model, state, direction_keys):
    ndof = 2 * len(model["coordinates"])
    for key in ("u_lift", "u_fluctuation", *direction_keys):
        value = state[key]
        require(value.shape == (ndof,) and value.dtype == np.float64 and np.isfinite(value).all(),
                "state shape/type/finiteness changed: " + key)
    return ndof


def prepare(source, output):
    started = time.perf_counter()
    corpus = Corpus(source)
    old = helper(corpus)
    expected = dict(total_force="1e-11", total_tangent="1e-10", material_force="1e-9",
                    regularization_force="1e-9", material_tangent="1e-9", regularization_tangent="1e-9",
                    precision_agreement="1e-40")
    require(old.THRESHOLDS == expected, "original gates changed")
    freeze = corpus.json(SAVED + "/saved_input_freeze.json")
    historical = {name: digest for name, digest in freeze["files"].items()
                  if name.startswith(("hf4_c1_results/", "hf4_c2_diagnostics/"))}
    require(len(historical) == 209, "saved historical binding inventory changed")
    for name, digest in historical.items():
        require(sha(corpus.path(name)) == digest, "saved historical SHA mismatch: " + name)
    descriptors = old.saved_descriptors(corpus, True)
    actual = [dict(run=name, stage=stage, index=entry["index"], d=entry["d"], original_status=row["status"])
              for name, stage, entry, row in descriptors]
    require(len(descriptors) == 63 and actual == freeze["selected"], "saved 63-state selection changed")
    manufacture_index = corpus.json(ORIGINAL + "/output_sha256.json")
    cases, bindings = [], {SAVED + "/saved_input_freeze.json", ORIGINAL + "/output_sha256.json"}
    plans = []
    for mesh, *_ in old.SIZES:
        for case in old.CASES:
            identifier = mesh + "__" + case
            base = ORIGINAL + "/" + identifier
            originals = {}
            for tail in ("inputs.npz", "hp_0.json", "hp_1.json", "result.json"):
                name = base + "/" + tail
                digest = sha(corpus.path(name))
                require(digest == manufacture_index[identifier + "/" + tail], "manufactured SHA mismatch: " + name)
                originals[name] = digest
            fixture = corpus.npz(base + "/inputs.npz")
            ndof = validate_arrays(fixture, fixture, ("direction_0", "direction_1"))
            result = corpus.json(base + "/result.json")
            refs = []
            for direction in (0, 1):
                pair = corpus.json(base + f"/hp_{direction}.json")
                ref = reference(pair, ndof)
                sf = result["directions"][direction]["force_scale"]
                with localcontext() as ctx:
                    ctx.prec = 120
                    hp = {key: [Decimal(a) for a in pair["80"][key]] for key in HP_KEYS}
                    require(Decimal(sf) == old.force_scale(hp, fixture, .125), "manufactured SF changed: " + identifier)
                ref["force_scale"] = sf
                refs.append(ref)
            row = dict(case=identifier, kind="manufactured", metadata={}, ndof=ndof,
                       source_files=originals, original_status=result["status"], direction_keys=["direction_0", "direction_1"])
            plans.append((row, base + "/inputs.npz", base + "/inputs.npz", refs))
    metadata_by_stage = {}
    for name, stage, entry, audit in descriptors:
        identifier = name + f"__{entry['index']:03d}"
        if stage not in metadata_by_stage:
            metadata_by_stage[stage] = corpus.json(stage + "/metadata.json")
        metadata = metadata_by_stage[stage]
        model_name, state_name = stage + "/model.npz", stage + "/steps/" + entry["file"]
        require(sha(corpus.path(model_name)) == metadata["model_sha256"], "saved model SHA mismatch")
        require(sha(corpus.path(state_name)) == entry["sha256"], "saved state SHA mismatch")
        binding_names = [stage + "/metadata.json", stage + "/steps/index.json"]
        if metadata["schema"] == "contact_c2_stage_v1":
            record_name = stage + "/steps/" + entry["record_file"]
            old.validate_saved_record_binding(metadata, entry, record_sha256=sha(corpus.path(record_name)))
            binding_names.append(record_name)
        else:
            require(metadata["schema"] == "contact_c1_stage_v1", "unknown saved record schema")
            binding_names += [stage + "/completion.json", stage + "/result.json"]
            old.validate_saved_record_binding(metadata, entry, completion=corpus.json(stage + "/completion.json"),
                file_sha256={f: sha(corpus.path(stage + "/" + f)) for f in ("result.json", "steps/index.json", "metadata.json")},
                controller=corpus.json(stage + "/result.json"), entries=corpus.json(stage + "/steps/index.json")["steps"])
        bindings.update(binding_names)
        run = stage.split("/stages/")[0]
        binding_names.append(run + "/audit.json")
        if metadata["schema"] == "contact_c2_stage_v1":
            bindings.add(run + "/audit.json")
            compact = next(r for r in corpus.json(run + "/audit.json")["states"] if r["index"] == entry["index"])
            binding_names.append(run + "/" + compact["detail_file"])
        require(audit["verification_precision_pair"] == [80, 120], "saved precision pair changed")
        fixture, arrays = corpus.npz(model_name), corpus.npz(state_name)
        ndof = validate_arrays(fixture, arrays, ("tangent_direction",))
        pair = audit["precision_evidence_decimal"]
        ref = reference(pair, ndof)
        sf = audit["measurements"]["force_scale"]
        prior = corpus.json(SAVED + "/" + identifier + "/result.json")
        require(Decimal(sf) == Decimal(prior["force_scale"]) == Decimal(pair["80"]["force_scale_decimal"]), "saved SF binding changed")
        with localcontext() as ctx:
            ctx.prec = 80
            hp = {key: [Decimal(a) for a in pair["80"][key]] for key in HP_KEYS}
            require(Decimal(sf) == old.force_scale(hp, fixture, entry["d"], metadata["force_scale_per_length"]), "saved SF definition changed")
        ref["force_scale"] = sf
        originals = {n: sha(corpus.path(n)) for n in (model_name, state_name, *binding_names)}
        row = dict(case=identifier, kind="saved", run=name, stage=stage, metadata=metadata, ndof=ndof,
                   entry=entry, source_files=originals, original_status=prior["status"],
                   original_audit_status=audit["status"], parameter_s=entry["d"],
                   physical_mean_drive=audit.get("physical_mean_drive"), direction_keys=["tangent_direction"])
        plans.append((row, model_name, state_name, [ref]))
    require(len(plans) == 96, "scope inventory changed")
    output = Path(output).resolve()
    require(not output.exists(), "output must be new")
    output.mkdir(parents=True)
    copies = {}
    def copy(original, relative):
        if original in copies:
            return copies[original]
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(corpus.path(original), native(target))
        require(sha(target) == sha(corpus.path(original)), "copy mismatch")
        copies[original] = relative
        return relative
    for row, model_name, state_name, refs in plans:
        identifier = row["case"]
        if row["kind"] == "manufactured":
            model_file = copy(model_name, "manufactured/" + identifier + ".npz")
        else:
            model_file = copy(model_name, "models/" + row["run"] + ".npz")
        state_file = copy(state_name, "states/" + identifier + ".npz")
        ref_file = "references/" + identifier + ".json.gz"
        target = output / ref_file
        target.parent.mkdir(exist_ok=True)
        value = dict(force_scale=refs[0]["force_scale"], directions=refs, reference_origin="existing_exact_HP_strings_no_recomputation",
                     source_files=row["source_files"])
        payload = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
        with native(target).open("xb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as handle:
                handle.write(payload)
        row.update(model_file=model_file, state_file=state_file, reference_file=ref_file,
                   model_sha256=sha(output / model_file), state_sha256=sha(output / state_file), reference_sha256=sha(target))
        cases.append(row)
    for i, original in enumerate(sorted(bindings)):
        copy(original, f"bindings/{i:03d}_" + Path(original).name)
    shutil.copyfile(native(corpus.manifest), native(output / "bindings/invariants_input_manifest.json"))
    files = {p.relative_to(output).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in output.rglob("*") if p.is_file()}
    index = dict(schema="numpy_scope_inputs_v1", manufactured=33, saved=63, directions=129, cases=cases,
                 thresholds=expected, force_scale_definition="unchanged old helper; manufacturing Decimal120, saved Decimal80; saved local parameter entry.d",
                 reference_policy="reuse exact existing HP80/120 strings; no new HP, JIT, candidate mechanics, or solve",
                 source_manifest_sha256=sha(corpus.manifest), preparer_sha256=sha(__file__),
                 source_bound_sha256=corpus.bound, original_copies=copies, files=files,
                 compressed_reference_bytes=sum(v["bytes"] for k, v in files.items() if k.startswith("references/")),
                 output_bytes_excluding_index=sum(v["bytes"] for v in files.values()), seconds=time.perf_counter() - started)
    write(output / "index.json", index)
    print(json.dumps({k: index[k] for k in ("manufactured", "saved", "directions", "compressed_reference_bytes", "output_bytes_excluding_index", "seconds")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="version_002/data of the restored frozen corpus")
    parser.add_argument("--output", type=Path, required=True, help="new independent inputs directory")
    args = parser.parse_args()
    prepare(args.source, args.output)
