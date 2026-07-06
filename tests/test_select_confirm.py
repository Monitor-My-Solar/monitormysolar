"""Select write-confirmation must never leave the entity at 'unknown'.

Repro of the GridBoss PortMode bug: user sends SmartLoad1_PortMode=2, the dongle
replies {"status":"success"}. HA must commit the SENT option ("Ac Coupled") and a
later coordinator refresh must re-derive the SAME option — not 'unknown'. The bug
was that the success path wrote the option LABEL (a string) into the coordinator
and cleared the optimistic guard, so a subsequent refresh decoded an out-of-range
value and HA rendered 'unknown'.

These mirror InverterSelect.confirm_option and _handle_coordinator_update's decode
without instantiating the HA SelectEntity base class.
"""

OPTIONS = ["Does Not Operate", "Smart Load", "Ac Coupled"]


def confirm_option(state, options, entities, entity_id):
    """Mirror of InverterSelect.confirm_option: commit sent option as its index."""
    if state not in options:
        return  # ignored; entity keeps prior value
    entities[entity_id] = options.index(state)


def decode(value, options, current):
    """Mirror of InverterSelect._handle_coordinator_update decode for non-SOC selects."""
    idx = int(value) if isinstance(value, (bool, int)) else None
    if idx is not None and 0 <= idx < len(options):
        return options[idx]
    if value in options:
        return value
    return current  # invalid/out-of-range: keep current (the `return` early-out in the real code)


def current_option_report(state, options):
    """HA renders 'unknown' when current_option is None or not in options."""
    return state if state in options else "unknown"


def test_success_commits_sent_option_as_index():
    entities = {}
    eid = "select.gb_smartload1_portmode"
    state = OPTIONS[2]  # user picked value 2 -> "Ac Coupled"
    confirm_option(state, OPTIONS, entities, eid)
    assert entities[eid] == 2  # stored as INT index, not the label string


def test_refresh_after_success_redecodes_same_option():
    entities = {}
    eid = "select.gb_smartload1_portmode"
    state = OPTIONS[2]
    confirm_option(state, OPTIONS, entities, eid)
    # A later coordinator refresh fires; decode the mirrored value.
    new_state = decode(entities[eid], OPTIONS, state)
    assert new_state == "Ac Coupled"
    assert current_option_report(new_state, OPTIONS) == "Ac Coupled"  # NOT unknown


def test_label_string_never_stored_so_never_unknown():
    # The old bug: label string stored, then decoded, then reported.
    # Even if a stray label lands in the coordinator, decode keeps a valid option.
    assert decode("Ac Coupled", OPTIONS, "Smart Load") == "Ac Coupled"
    assert current_option_report(decode("Ac Coupled", OPTIONS, "Smart Load"), OPTIONS) == "Ac Coupled"


def test_out_of_range_value_keeps_current_not_unknown():
    # An out-of-range int (e.g. dongle sent 7) must not blank the entity.
    assert decode(7, OPTIONS, "Ac Coupled") == "Ac Coupled"
    # None-producing decode is never written; report stays on a valid option.
    assert current_option_report(decode(7, OPTIONS, "Ac Coupled"), OPTIONS) == "Ac Coupled"


def test_index_zero_is_valid():
    # "Does Not Operate" is index 0 — must not be treated as falsey/absent.
    assert decode(0, OPTIONS, "Ac Coupled") == "Does Not Operate"
