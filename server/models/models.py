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
    on_true: Optional[Action] = None
    on_false: Optional[Action] = None


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
        action_ids = {
            action["id"] for action in values.get("actions", {}).get("actions", [])
        }

        for screen in values.get("screens", []):
            for bound_state in screen.get("state_bindings", {}).values():
                if bound_state not in state_names:
                    raise ValueError(
                        f"Screen '{screen['id']}' binds to unknown internal state '{bound_state}'"
                    )

        for action in values.get("actions", {}).get("actions", []):
            if action.get("on_callback"):
                for act_id in action.get("on_callback", {}).get("actions", []):
                    if act_id not in action_ids:
                        raise ValueError(
                            f"OnCallback in action '{action['id']}' references unknown action id '{act_id}'"
                        )
        binds = set()
        for state in states:
            bind = state.get("bind")
            if bind:
                len_before = len(binds)
                binds.add(bind)
                if len(binds) == len_before:
                    raise ValueError(
                        f"Multiple internal states are bound to state {bind}"
                    )

        return values


# --------------------------------------
# Template configuration
# --------------------------------------


class TemplateConfig(BaseModel):
    templates: List[Template]
