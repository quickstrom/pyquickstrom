import json
import jsonlines
from typing import List, Dict, Optional, Literal, Union
from dataclasses import dataclass

Selector = str

# mypy doesn't support recursive types :(
Schema = Dict[str, object]

ElementState = Dict[str, object]

State = Dict[Selector, List[ElementState]]


@dataclass
class Action():
    id: str
    args: List[object]
    isEvent: bool
    timeout: Optional[int]


@dataclass
class TraceActions():
    actions: List[Action]


@dataclass
class TraceState():
    state: State


TraceElement = Union[TraceActions, TraceState]

Trace = List[TraceElement]


@dataclass
class Validity():
    certainty: Union[Literal['Definitely'], Literal['Probably']]
    value: bool


@dataclass
class Result():
    valid: Validity
    trace: Trace


@dataclass
class Start():
    dependencies: Dict[Selector, Schema]


@dataclass
class End():
    pass


@dataclass
class Done():
    results: List[Result]


@dataclass
class RequestAction():
    action: Action


@dataclass
class Performed():
    state: State


@dataclass
class Event():
    event: Action
    state: State


def message_writer(fp):
    return jsonlines.Writer(
        fp,
        dumps=lambda obj: json.dumps(obj, cls=_ProtocolEncoder),
        flush=True)


def message_reader(fp):
    def loads(s):
        return json.loads(s, object_hook=_decode_hook)

    return jsonlines.Reader(fp, loads=loads)


class _ProtocolEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Performed):
            return {'tag': 'Performed', 'contents': obj.state}
        elif isinstance(obj, Event):
            event = self.default(obj.event)
            return {'tag': 'Event', 'contents': [event, obj.state]}
        elif isinstance(obj, Action):
            return {
                'id': obj.id,
                'args': obj.args,
                'isEvent': obj.isEvent,
                'timeout': obj.timeout
            }
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
        raise (Exception(f"Unsupported tagged JSON type: {d['tag']}"))
