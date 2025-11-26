from models.models import BooleanState, InternalState, NumberState
from state_scheduler.state_scheduler import (
    bulk_add_trigger,
    get_ha_bind_dict,
    states_to_stored_states,
)


def test_states_to_stored_states_uses_defaults():
    states = [
        InternalState(name="temp", definition=NumberState(default=21.5)),
        InternalState(name="enabled", definition=BooleanState(default=True)),
    ]

    stored = states_to_stored_states(states)

    assert stored[0].value == 21.5
    assert stored[1].value is True


def test_get_ha_bind_dict_filters_and_strips_prefix():
    states = [
        InternalState(
            name="switch",
            definition=BooleanState(default=False),
            bind="ha:light.kitchen",
        ),
        InternalState(name="other", definition=BooleanState(default=True)),
    ]

    result = get_ha_bind_dict(states)

    assert result == {"switch": "light.kitchen"}


def test_bulk_add_trigger_registers_all_entities():
    recorded = []

    class FakeListener:
        def add_trigger(self, trigger_type, callback, **kwargs):
            recorded.append((trigger_type, kwargs, callback))

    entities = ["light.kitchen", "sensor.outdoor"]
    callback = lambda *args, **kwargs: None  # noqa: E731
    listener = FakeListener()

    bulk_add_trigger(entities, listener, callback, type="state")

    assert len(recorded) == 2
    for entity_id, (_, kwargs, _) in zip(entities, recorded):
        assert kwargs["entity_id"] == entity_id
