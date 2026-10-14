"""Sixteen metadata-only unit tests; imported and run only by the approved helper."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

RESPONSE = None
FIXTURE_ROOT = None
CHECKPOINT = None
REFERENCE_CALLS = 0


class SelectedReferenceTests(unittest.TestCase):
    def setUp(self):
        CHECKPOINT()
        self.repo = (Path(FIXTURE_ROOT)/self._testMethodName).resolve()
        self.repo.mkdir(parents=True, exist_ok=False)
        self.result, self.model = self.repo/'result.json', self.repo/'model.json'
        self.source, self.reference = self.repo/'source.py', self.repo/'reference.json'
        self.result.write_bytes(b'{"fixture":"result"}\n')
        self.model.write_bytes(b'{"fixture":"model"}\n')
        self.source.write_bytes(b'"""ordinary source fixture; never imported"""\n')
        self.rpin = hashlib.sha256(self.result.read_bytes()).hexdigest()
        self.mpin = hashlib.sha256(self.model.read_bytes()).hexdigest()
        self.states = [dict(state_sha256=f'fixture-state-{i:02}', d=i/20) for i in range(25)]
        self.states[13]['d'], self.states[16]['d'] = 1.20, 1.05

    def record(self, indices=(13, 16)):
        return dict(status='pass', result_sha256=self.rpin, accepted_states=len(indices),
            HP_calls_started=2*len(indices), HP_calls_completed=2*len(indices),
            states=[dict(index=i, status='pass', HP_calls=2,
                state_sha256=self.states[i]['state_sha256'], target_mm=self.states[i]['d']) for i in indices],
            input_bindings={'result.json':self.rpin, 'model.json':self.mpin},
            source_bindings={'source.py':hashlib.sha256(self.source.read_bytes()).hexdigest()},
            full_element_and_DOF_coverage=True)

    def evaluate(self, value, complete=True):
        global REFERENCE_CALLS
        CHECKPOINT()
        self.reference.write_text(json.dumps(value)+'\n', encoding='utf-8')
        REFERENCE_CALLS += 1
        answer = RESPONSE._reference(self.reference, self.result, self.rpin, self.model,
            self.mpin, self.states, complete, self.repo)
        self.assertEqual(answer['production_accepted_state_count'], 25)
        for name in ('HP_all_columns_qualified', 'contact_qualified', 'clamp_qualified',
                     'pressure_qualified', 'HF5_qualified'):
            self.assertIs(answer[name], False)
        CHECKPOINT()
        return answer

    def mismatch(self, value):
        answer = self.evaluate(value)
        self.assertEqual(answer['status'], 'mismatch')
        self.assertIs(answer['selected_reference_pass'], False)
        self.assertIs(answer['accepted_reference_pass'], False)
        self.assertIs(answer['full_path_reference_pass'], False)
        self.assertEqual(answer['matched_state_indices'], [])
        self.assertEqual(answer['matched_state_count'], 0)
        self.assertTrue(answer['reasons'])

    def test_01_no_reference(self):
        global REFERENCE_CALLS
        REFERENCE_CALLS += 1
        answer = RESPONSE._reference(None, self.result, self.rpin, self.model, self.mpin,
            self.states, True, self.repo)
        self.assertEqual(answer['status'], 'not_provided')
        self.assertIs(answer['accepted_reference_pass'], False)
        self.assertIs(answer['selected_reference_pass'], False)
        self.assertEqual(answer['production_accepted_state_count'], 25)

    def test_02_full_reference_compatibility(self):
        answer = self.evaluate(self.record(range(25)))
        self.assertEqual(answer['status'], 'matched')
        self.assertIs(answer['selected_reference_pass'], True)
        self.assertIs(answer['accepted_reference_pass'], True)
        self.assertIs(answer['full_path_reference_pass'], True)
        self.assertEqual(answer['matched_state_indices'], list(range(25)))

    def test_03_full_reference_incomplete_production(self):
        answer = self.evaluate(self.record(range(25)), complete=False)
        self.assertIs(answer['accepted_reference_pass'], True)
        self.assertIs(answer['full_path_reference_pass'], False)

    def test_04_selected_actual_indices(self):
        value = self.record()
        value.update(selected_accepted_indices=[13,16], production_accepted_states=25)
        answer = self.evaluate(value)
        self.assertEqual(answer['status'], 'matched_partial')
        self.assertEqual(answer['matched_state_indices'], [13,16])
        self.assertEqual(answer['matched_state_count'], 2)
        self.assertIs(answer['source_bindings_verified'], True)
        self.assertIs(answer['selected_reference_pass'], True)
        self.assertIs(answer['accepted_reference_pass'], False)
        self.assertIs(answer['full_path_reference_pass'], False)
        self.assertIs(answer['covers_all_accepted_states'], False)

    def test_05_empty_reference(self):
        self.mismatch(self.record(()))

    def test_06_missing_or_misreported_count(self):
        value = self.record(); del value['accepted_states']; self.mismatch(value)
        value = self.record(); value['states'].pop(); self.mismatch(value)

    def test_07_global_HP_count(self):
        value = self.record(); value['HP_calls_completed'] = 2; self.mismatch(value)

    def test_08_row_HP_and_status(self):
        value = self.record(); value['states'][0]['HP_calls'] = 1; self.mismatch(value)
        value = self.record(); value['states'][0]['status'] = 'not_pass'; self.mismatch(value)
        value = self.record(); value['status'] = 'not_pass'; self.mismatch(value)

    def test_09_duplicate_index(self):
        value = self.record(); value['states'][1] = copy.deepcopy(value['states'][0]); self.mismatch(value)

    def test_10_bool_index(self):
        value = self.record(); value['states'][0]['index'] = True; self.mismatch(value)

    def test_11_out_of_range_index(self):
        value = self.record(); value['states'][1]['index'] = 25; self.mismatch(value)

    def test_12_wrong_state_SHA(self):
        value = self.record(); value['states'][0]['state_sha256'] = self.states[0]['state_sha256']; self.mismatch(value)

    def test_13_wrong_target(self):
        value = self.record(); value['states'][1]['target_mm'] = 1.20; self.mismatch(value)

    def test_14_result_and_input_identity(self):
        value = self.record(); value['result_sha256'] = 'wrong'; self.mismatch(value)
        for name in ('result.json', 'model.json'):
            value = self.record(); value['input_bindings'][name] = 'wrong'; self.mismatch(value)

    def test_15_source_and_full_coverage(self):
        value = self.record(); value['source_bindings']['source.py'] = 'wrong'; self.mismatch(value)
        value = self.record(); value['full_element_and_DOF_coverage'] = False; self.mismatch(value)

    def test_16_explicit_selection_and_population(self):
        value = self.record(); value['selected_accepted_indices'] = [0,1]; self.mismatch(value)
        value = self.record(); value['production_accepted_states'] = 2; self.mismatch(value)
