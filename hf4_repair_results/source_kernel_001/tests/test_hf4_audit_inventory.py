"""Evidence inventory checks using hand-built records; no FE or HP evaluation."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def validate(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "hf4_inventory_under_test", scripts / "audit_hf4_normal.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_state_inventory


def inventory():
    targets = [0.0, 0.25, 0.5]
    states = [
        dict(index=0, d=0.0, is_original_target=True,
             original_target_displacement=0.0, bisection_depth=0),
        dict(index=1, d=0.125, is_original_target=False,
             original_target_displacement=0.25, bisection_depth=1),
        dict(index=2, d=0.25, is_original_target=True,
             original_target_displacement=0.25, bisection_depth=1),
        dict(index=3, d=0.5, is_original_target=True,
             original_target_displacement=0.5, bisection_depth=0),
    ]
    entries = [dict(index=s["index"], d=s["d"]) for s in states]
    result = dict(status="success", target_reached=True,
                  target_displacement=0.5, reached_displacement=0.5,
                  target_metrics=deepcopy(states[-1]),
                  last_accepted_state=deepcopy(states[-1]),
                  accepted_steps=deepcopy(states))
    return entries, result, targets, states


def reindex(entries, result, states):
    for i, (entry, state, reported) in enumerate(
            zip(entries, states, result["accepted_steps"])):
        entry["index"] = state["index"] = reported["index"] = i


def test_complete_targets_with_genuine_substep_are_accepted(validate):
    validate(*inventory())


@pytest.mark.parametrize("part", ["entries", "states", "reported"])
def test_differing_record_counts_are_rejected(validate, part):
    entries, result, targets, states = inventory()
    {"entries": entries, "states": states,
     "reported": result["accepted_steps"]}[part].pop()
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


def test_coherently_omitted_original_target_is_not_success(validate):
    entries, result, targets, states = inventory()
    for collection in (entries, states, result["accepted_steps"]):
        del collection[2]
    reindex(entries, result, states)
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


@pytest.mark.parametrize("part", ["entries", "states", "reported"])
def test_one_record_stream_reordered_is_rejected(validate, part):
    entries, result, targets, states = inventory()
    items = {"entries": entries, "states": states,
             "reported": result["accepted_steps"]}[part]
    items[1], items[2] = items[2], items[1]
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


def test_all_streams_reordered_and_reindexed_are_still_rejected(validate):
    entries, result, targets, states = inventory()
    for collection in (entries, states, result["accepted_steps"]):
        collection[1], collection[2] = collection[2], collection[1]
    reindex(entries, result, states)
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


@pytest.mark.parametrize("field,value", [
    ("is_original_target", True),
    ("original_target_displacement", 0.5),
    ("bisection_depth", 2),
])
def test_substep_identity_must_agree_with_production(validate, field, value):
    entries, result, targets, states = inventory()
    states[1][field] = value
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


def test_substep_cannot_be_relabelled_as_its_unreached_original(validate):
    entries, result, targets, states = inventory()
    for state in (states[1], result["accepted_steps"][1]):
        state["is_original_target"] = True
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


@pytest.mark.parametrize("field,value", [
    ("target_reached", False),
    ("reached_displacement", 0.25),
    ("target_metrics", None),
])
def test_success_label_cannot_override_missing_terminal_evidence(validate, field, value):
    entries, result, targets, states = inventory()
    result[field] = value
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


def test_failed_prefix_can_preserve_its_last_accepted_state(validate):
    entries, result, targets, states = inventory()
    for collection in (entries, states, result["accepted_steps"]):
        del collection[2:]
    result.update(status="failure", target_reached=False,
                  target_metrics=None, reached_displacement=0.125,
                  last_accepted_state=deepcopy(states[-1]))
    validate(entries, result, targets, states)


@pytest.mark.parametrize("parent_target", [0.0, 0.125, 0.375])
def test_coherent_substep_must_precede_a_declared_target(validate, parent_target):
    entries, result, targets, states = inventory()
    for state in (states[1], result["accepted_steps"][1]):
        state["original_target_displacement"] = parent_target
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


@pytest.mark.parametrize("terminal", [{}, {"d": 0.25}])
def test_success_needs_terminal_metrics_at_the_last_target(validate, terminal):
    entries, result, targets, states = inventory()
    result["target_metrics"] = terminal
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)


@pytest.mark.parametrize("reached,metrics", [
    (True, None), (False, {"d": 0.5}), (True, {"d": 0.5}),
])
def test_failure_cannot_publish_target_success(validate, reached, metrics):
    entries, result, targets, states = inventory()
    result.update(status="failure", target_reached=reached, target_metrics=metrics)
    with pytest.raises(ValueError):
        validate(entries, result, targets, states)
