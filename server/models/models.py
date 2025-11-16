from typing import Annotated, List, Optional, Literal, Union
from pydantic import BaseModel, StringConstraints


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
    default: Optional[float] = None


class BooleanState(BaseModel):
    type: Literal["boolean"] = "boolean"
    default: Optional[bool] = None


class EnumState(BaseModel):
    type: Literal["enum"] = "enum"
    options: List[str]
    default: Optional[str] = None


class CallbackState(BaseModel):
    type: Literal["callback"] = "callback"
    callback_id: str


StateDefinition = Union[NumberState, BooleanState, EnumState, CallbackState]


# -------------------------------------
# Internal states
# -------------------------------------


class InternalState(BaseModel):
    name: str
    definition: StateDefinition
    bind: Optional[Annotated[str, StringConstraints(pattern=r"^ha:.*")]] = None


class InternalStates(BaseModel):
    states: List[InternalState]


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
    types: Optional[List[StateDefinition]] = None


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
    right: Union[str, float, int, bool]


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

    state_based: List["StateBasedAction"]
    on_callback: List[OnCallback]


class StateBasedAction(BaseModel):
    on_state: str
    actions: List[str]


# -------------------------------------
# Timer module
# -------------------------------------


class TimerModule(BaseModel):
    callback: Optional[str]
    timeout_seconds: int
    time_state: str


class Module(BaseModel):
    id: str
    timer: TimerModule


# -------------------------------------
# Full configuration
# -------------------------------------


class FullConfig(BaseModel):
    screens: List[Screen]
    templates: List[Template]
    internal_states: InternalStates
    actions: Actions
    modules: List[Module]
