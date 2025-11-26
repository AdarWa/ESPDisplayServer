from __future__ import annotations
from typing import Annotated, List, Optional, Literal, Union
from pydantic import BaseModel, Field, StringConstraints, model_validator


# -------------------------------------
# Core types
# -------------------------------------


class Callback(BaseModel):
    id: str
    description: Optional[str] = None


class StateType(str):
    pass


class NumberState(BaseModel):
    type: Literal["number"] = "number"
    min: Optional[float] = None
    max: Optional[float] = None
    default: float


class BooleanState(BaseModel):
    type: Literal["boolean"] = "boolean"
    default: bool


class EnumState(BaseModel):
    type: Literal["enum"] = "enum"
    options: List[str]
    default: str


class CallbackState(BaseModel):
    type: Literal["callback"] = "callback"
    callback_id: str


StateDefinition = Union[NumberState, BooleanState, EnumState, CallbackState]


# -------------------------------------
# Internal states
# -------------------------------------


class InternalState(BaseModel):
    name: str
    definition: StateDefinition = Field(discriminator="type")
    bind: Optional[Annotated[str, StringConstraints(pattern=r"^ha:.*")]] = None

    def to_stored_internal_state(
        self, value: Optional[Union[float, bool, str]] = None
    ) -> StoredInternalState:
        if self.definition.type == "callback":
            return StoredInternalState(
                name=self.name, definition=self.definition, value=""
            )
        return StoredInternalState(
            name=self.name,
            definition=self.definition,
            bind=self.bind,
            value=value or self.definition.default,
        )


class StoredInternalState(InternalState):
    value: Union[float, bool, str]


class InternalStates(BaseModel):
    states: List[InternalState]

    def find_state_by_name(self, name: str) -> Optional[InternalState]:
        for state in self.states:
            if state.name == name:
                return state
        return None


# -------------------------------------
# Template and fields
# -------------------------------------


class TemplateField(BaseModel):
    name: str
    bind_to_internal: Optional[str] = None
    callback: Optional[str] = None


class Template(BaseModel):
    name: str
    fields: List[TemplateField]


# -------------------------------------
# Screen configuration
# -------------------------------------


class Screen(BaseModel):
    id: str
    template: str
    state_bindings: dict  # mapping: screen_field -> internal_state


# -------------------------------------
# Callback triggered action
# -------------------------------------


class OnCallback(BaseModel):
    callback_id: str
    actions: List[str]  # list of Action ids to execute


# -------------------------------------
# Actions
# -------------------------------------


class CompareAction(BaseModel):
    left: str
    operator: Literal["eq", "ne", "lt", "gt", "le", "ge"]
    right: Union[str, float, int]
    on_true: Optional[str] = None
    on_false: Optional[str] = None


class ScriptCall(BaseModel):
    script_name: str
    args: Optional[dict] = None


class UpdateState(BaseModel):
    target: str
    value: Union[str, float, int, bool]


class Action(BaseModel):
    id: str

    compare: Optional[CompareAction] = None
    call_script: Optional[ScriptCall] = None
    update_state: Optional[UpdateState] = None
    on_callback: Optional[OnCallback] = None


class Actions(BaseModel):
    actions: List[Action]


class StateBasedAction(BaseModel):
    on_state: str
    actions: List[str]


# -------------------------------------
# Timer module
# -------------------------------------


class TimerModule(BaseModel):
    callback: Optional[str]
    time_state: str


class Module(BaseModel):
    id: str
    timer: TimerModule


# -------------------------------------
# Full configuration
# -------------------------------------


class FullConfig(BaseModel):
    screens: List[Screen]
    internal_states: InternalStates
    actions: Actions
    modules: List[Module]

    @model_validator(mode="before")
    def validate_references(cls, values):
        states = values.get("internal_states", {}).get("states", [])
        state_names = {state["name"] for state in states}

        actions = values.get("actions", {}).get("actions", [])
        action_ids = {action["id"] for action in actions if "id" in action}

        def check_state(state: str):
            return state in state_names or state.startswith("ha:")

        # helper to validate an action (handles nested compare.on_true/on_false)
        def check_action(action: dict):
            action_id = action.get("id", "<unknown>")
            sub_actions = [
                action.get("on_callback"),
                action.get("compare"),
                action.get("call_script"),
                action.get("update_state"),
            ]
            if sum(x is not None for x in sub_actions) != 1:
                raise ValueError(
                    f"Action '{action_id}' must define exactly one of on_callback, compare, call_script, update_state"
                )

            if action.get("update_state"):
                target = action["update_state"].get("target")
                if not check_state(target):
                    raise ValueError(
                        f"Action '{action_id}' update_state target '{target}' references unknown internal state '{target}'"
                    )

            if action.get("compare"):
                left = action["compare"].get("left")
                right = action["compare"].get("right")
                if left not in state_names:
                    raise ValueError(
                        f"Action '{action_id}' compare left '{left}' references unknown internal state '{left}'"
                    )
                if isinstance(right, str) and right not in state_names:
                    raise ValueError(
                        f"Action '{action_id}' compare right '{right}' references unknown internal state '{right}'"
                    )

            if action.get("on_callback"):
                for act_id in action["on_callback"].get("actions", []):
                    if act_id not in action_ids:
                        raise ValueError(
                            f"OnCallback in action '{action_id}' references unknown action id '{act_id}'"
                        )

        # validate screens reference existing states
        for screen in values.get("screens", []):
            for bound_state in screen.get("state_bindings", {}).values():
                if bound_state not in state_names:
                    raise ValueError(
                        f"Screen '{screen.get('id')}' binds to unknown internal state '{bound_state}'"
                    )

        # validate actions and their referenced states
        for action in actions:
            check_action(action)

        # validate modules reference existing states (e.g., timer.time_state)
        for module in values.get("modules", []):
            timer = (module or {}).get("timer") or {}
            time_state = timer.get("time_state")
            if time_state and time_state not in state_names:
                raise ValueError(
                    f"Module '{module.get('id')}' references unknown time_state '{time_state}'"
                )

        # ensure no duplicate external binds among internal states
        binds = set()
        for state in states:
            bind = state.get("bind")
            if bind:
                if bind in binds:
                    raise ValueError(
                        f"Multiple internal states are bound to state {bind}"
                    )
                binds.add(bind)

        return values


# --------------------------------------
# Template configuration
# --------------------------------------


class TemplateConfig(BaseModel):
    templates: List[Template]
