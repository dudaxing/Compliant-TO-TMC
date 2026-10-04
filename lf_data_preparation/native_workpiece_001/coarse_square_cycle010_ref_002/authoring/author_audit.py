"""Author an independent reference wrapper; preserve all accepted-state math."""
from pathlib import Path
from hashlib import sha256
import ast
import difflib
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
original = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/audit_cycle010.py'
raw = original.read_bytes(); candidate = raw
changes = []


def replace(old, new):
    global candidate
    a,b = old.encode(),new.encode()
    assert candidate.count(a) == 1, old[:80]
    candidate = candidate.replace(a,b); changes.append((a,b))


replace('from core_audit_mechanical import Audit as ActionCoreAudit, MECHANICAL_AVAILABILITY',
        'from core_audit_mechanical import Audit as ActionCoreAudit, MECHANICAL_AVAILABILITY\nfrom counter_contract import reconstruct')
replace('        self.first_range_observation = None',
        '        self.first_range_observation = None\n        self.tangent_range_observation = None')
replace('        self.check(Path(__file__).relative_to(self.repo).as_posix() in self.sources, "New checker is not source-bound")',
'''        reference_protocol = Path(__file__).with_name("protocol.json")
        self.bind(reference_protocol)
        self.reference_protocol_sha256 = sha(reference_protocol)
        self.reference_bindings = read(reference_protocol)["bindings"]
        for name, expected in self.reference_bindings.items():
            self.bind(self.repo/name, expected)
        self.check(self.reference_bindings.get(Path(__file__).relative_to(self.repo).as_posix()) == sha(Path(__file__))
            and self.reference_bindings.get(Path(__file__).with_name("counter_contract.py").relative_to(self.repo).as_posix())
                == sha(Path(__file__).with_name("counter_contract.py")), "Independent reference/counter source binding differs")''')
replace('        extra_paths = [PRIVATE_CORE, Path(__file__), *(self.stage/name for name in',
        '        extra_paths = [self.stage/"core_audit_mechanical.py", self.stage/"audit_cycle010.py", *(self.stage/name for name in')
replace('            and self.sources[PRIVATE_CORE.relative_to(self.repo).as_posix()] == sha(PRIVATE_CORE),',
        '            and self.sources[(self.stage/"core_audit_mechanical.py").relative_to(self.repo).as_posix()] == sha(PRIVATE_CORE),')
replace('''            and receipt["observed_tangent_calls"] == receipt["observed_tangent_calls_completed"]
                == counts["tangent_calls"] == counts["tangent_calls_completed"]
            and receipt["first_tangent_range_input"] is None
            and not (self.stage/"first_tangent_range_input").exists()''',
'''            and receipt["observed_tangent_calls"] == counts["tangent_calls"]
            and receipt["observed_tangent_calls_completed"] == counts["tangent_calls_completed"]
            and receipt["first_tangent_range_input"] is not None
            and (self.stage/"first_tangent_range_input").is_dir()''')
replace('        self.first_range_observation = self.verify_first_range_observation(result, receipt, model)',
        '        self.first_range_observation = self.verify_first_range_observation(result, receipt, model)\n        self.tangent_range_observation = self.verify_tangent_range_observation(receipt, model)')
start = candidate.index(b'    def reconstruct_counts(')
end = candidate.index(b'    def verify_first_range_observation(',start)
replace(candidate[start:end].decode(),'''    def reconstruct_counts(self, result, receipt):
        """Strict captured-failure trace; all accepted caches must be complete."""
        return reconstruct(result, receipt, SETTINGS, self.check)

''')
replace('    def run(self):', '''    def verify_tangent_range_observation(self, receipt, model):
        """Read/copy failed input and its same-object force fields; no reevaluation."""
        directory = self.stage/"first_tangent_range_input"
        descriptor = directory/"observation.json"
        self.bind(descriptor)
        observation = read(descriptor)
        self.check(observation == receipt["first_tangent_range_input"]
            and observation["tangent_call_ordinal"] == self.accounting["failed_tangent_base"]["tangent_call"]
            and observation["bound_force_call_ordinal"] == self.accounting["failed_tangent_base"]["force_call"]
            and observation["state_sha256"] == self.accounting["failed_tangent_base"]["state_sha256"]
            and observation["source_freeze_sha256"] == receipt["source_freeze_sha256"]
            and observation["input_inventory_sha256"] == receipt["input_inventory_sha256"]
            and observation["exception_type"] == "KernelError"
            and np.isfinite(observation["elapsed_seconds"])
            and 0 <= observation["elapsed_seconds"] <= receipt["elapsed_seconds"],
            "Failed tangent observation/provenance differs")
        archive, force_archive = directory/"input.npz", directory/"force_fields.npz"
        self.bind(archive, observation["input_npz_sha256"])
        self.bind(force_archive, observation["force_fields_npz_sha256"])
        arrays, fields = npz(archive), npz(force_archive)
        verify_fields(arrays, observation["fields"])
        verify_fields(fields, observation["force_fields"])
        intrinsic = ("edofs", "coordinates", "connectivity", "lam", "mu", "kr", "hx", "hy",
                     "thickness", "solid", "fixed_dofs", "grad", "hessian", "weights", "points")
        self.check(set(arrays) == set(intrinsic)|{"lift", "fluctuation"}, "Failed tangent input field contract")
        same_arrays({k:arrays[k] for k in intrinsic},{k:model[k] for k in intrinsic}, "Failed tangent model/operator fields")
        self.check(all(arrays[k].dtype == np.dtype("float64") and arrays[k].shape == (6642,)
                and np.isfinite(arrays[k]).all() for k in ("lift","fluctuation"))
            and np.count_nonzero(arrays["lift"]) == 0
            and np.count_nonzero(arrays["fluctuation"][model["fixed_dofs"]]) == 0
            and state_hash(arrays) == observation["state_sha256"]
            and all(np.isfinite(v).all() for v in fields.values())
            and fields["J"].shape == (3200,9) and np.all(fields["J"] > 0)
            and not any(row["state_sha256"] == observation["state_sha256"] for row in self.result["states"]),
            "Failed tangent raw fields/state/caches differ")
        copied = self.output/"first_tangent_range_input"; copied.mkdir()
        for path in (descriptor,archive,force_archive):
            shutil.copyfile(path,copied/path.name); self.bind(copied/path.name,sha(path))
        return dict(observation=self.record(copied/descriptor.name),input=self.record(copied/archive.name),
            force_fields=self.record(copied/force_archive.name),tangent_call_ordinal=observation["tangent_call_ordinal"],
            bound_force_call_ordinal=observation["bound_force_call_ordinal"],state_sha256=observation["state_sha256"],
            independently_qualified=False,reevaluated=False,arithmetic_issue_resolved=False,
            scope="Only bound failed local tangent input and returned force fields; no force/tangent/HP evaluation")

    def run(self):''')
replace('''            tangent_observation=dict(observed_tangent_calls=self.receipt["observed_tangent_calls"],
                all_tangent_calls_completed=True, first_tangent_range_input=None),''',
'''            tangent_observation=dict(observed_tangent_calls=self.receipt["observed_tangent_calls"],
                observed_tangent_calls_completed=self.receipt["observed_tangent_calls_completed"],
                all_tangent_calls_completed=False,all_accepted_caches_completed=True,
                first_tangent_range_input=self.tangent_range_observation),
            independent_reference_card_protocol_sha256=self.reference_protocol_sha256,
            independent_reference_source_bindings=self.reference_bindings,''')
restored = candidate
for old,new in reversed(changes):
    assert restored.count(new) == 1
    restored = restored.replace(new,old)
assert restored == raw
target = AUTHOR/'audit_cycle010_ref002.py'
compile(candidate,str(target),'exec'); target.open('xb').write(candidate)
(AUTHOR/'audit_cycle010_ref002.diff').open('xb').write(''.join(difflib.unified_diff(raw.decode().splitlines(True),candidate.decode().splitlines(True),fromfile=original.name,tofile=target.name)).encode())
with (AUTHOR/'audit_migration.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(status='authored_not_executed',original_sha256=sha256(raw).hexdigest(),
        candidate_sha256=sha256(candidate).hexdigest(),inverse_bytes_exact=True,
        changes=len(changes),accepted_state_core_sha256='b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5',
        scope='New independent reference identity and strict captured-failure accounting only; no accepted-state mathematical equation/gate change; original failed reference kept'),stream,indent=2)
print('Authored independent reference source only; no module import or evaluation')
