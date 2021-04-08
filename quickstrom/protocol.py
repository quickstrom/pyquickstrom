import json
from typing import List, Dict, Optional, Literal, Union
from dataclasses import dataclass

Selector = str

# mypy doesn't support recursive types :(
Schema = Dict[str, object]

ElementState = Dict[str, object]

State = Dict[Selector, ElementState]


@dataclass
class Start():
    dependencies: Dict[Selector, State]


@dataclass
class End():
    pass


@dataclass
class Done():
    results: List[Result]


@dataclass
class TraceActions():
    actions: List[Action]


@dataclass
class TraceState():
    state: State


TraceElement = Union[TraceActions, TraceState]

Trace = List[TraceElement]


@dataclass
class Result():
    valid: Validity
    trace: Trace


@dataclass
class Validity():
    certainty: Literal['Definitely'] | Literal['Probably']
    value: bool


@dataclass
class Action():
    id: str
    args: List[object]
    isEvent: bool
    timeout: Optional[int]


@dataclass
class RequestAction():
    action: Action


def encode_protocol_message(obj):
    return json.dumps(obj, cls=_ProtocolEncoder)


def decode_protocol_message(s):
    return json.loads(s, object_hook=_decode_hook)


class _ProtocolEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Start):
            deps = json.JSONEncoder.default(self, obj.dependencies)
            return {'tag': 'Start', 'dependencies': deps}
        elif isinstance(obj, End):
            return {'tag': 'End'}
        else:
            return json.JSONEncoder.default(self, obj)


def _decode_hook(d):
    if 'tag' not in d:
        if 'valid' in d and 'trace' in d:
            return Result(d['valid'], d['trace'])
        if 'id' in d and 'args' in d and 'isEvent' in d and 'timeout' in d:
            return Action(d['id'], d['args'], d['isEvent'], d['timeout'])
        else:
            return d
    if d['tag'] == 'Start':
        return Start(dependencies=d['dependencies'])
    if d['tag'] == 'RequestAction':
        return RequestAction(action=d['action'])
    elif d['tag'] == 'End':
        return End()
    elif d['tag'] == 'Done':
        return Done(results=d['results'])
    elif d['tag'] == 'Definitely':
        return Validity('Definitely', d['contents'])
    elif d['tag'] == 'Probably':
        return Validity('Probably', d['contents'])
    elif d['tag'] == 'TraceAction':
        return TraceActions(actions=d['contents'])
    elif d['tag'] == 'TraceState':
        return TraceState(state=d['contents'])
    else:
        raise(Exception(f"Unsupported tagged JSON type: {d['tag']}"))
