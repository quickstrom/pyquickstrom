import json
import jsonlines
from typing import Any, Callable, IO, List, Dict, Optional, Literal, Union
from dataclasses import dataclass

Selector = str

Schema = Dict[str, 'Schema']

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

Certainty = Union[Literal['Definitely'], Literal['Probably']]


@dataclass
class Validity():
    certainty: Certainty
    value: bool


@dataclass
class RunResult():
    valid: Validity
    trace: Trace


@dataclass
class ErrorResult():
    error: str


Result = Union[RunResult, ErrorResult]


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
    version: int


@dataclass
class Performed():
    state: State


@dataclass
class Stale():
    pass


@dataclass
class Event():
    event: Action
    state: State


def message_writer(fp: IO[str]):
    dumps: Callable[[Any],
                    str] = lambda obj: json.dumps(obj, cls=_ProtocolEncoder)
    return jsonlines.Writer(fp, dumps=dumps, flush=True)


def message_reader(fp: IO[str]):
    def loads(s: str):
        return json.loads(s, object_hook=_decode_hook)

    return jsonlines.Reader(fp, loads=loads)


class _ProtocolEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, Performed):
            return {'tag': 'Performed', 'contents': o.state}
        elif isinstance(o, Stale):
            return {'tag': 'Stale'}
        elif isinstance(o, Event):
            event: Any = self.default(o.event)
            return {'tag': 'Event', 'contents': [event, o.state]}
        elif isinstance(o, Action):
            return {
                'id': o.id,
                'args': o.args,
                'isEvent': o.isEvent,
                'timeout': o.timeout
            }
        else:
            return json.JSONEncoder.default(self, o)


def _decode_hook(d: Any) -> Any:
    if 'tag' not in d:
        if 'valid' in d and 'trace' in d:
            return RunResult(d['valid'], d['trace'])
        if 'id' in d and 'args' in d and 'isEvent' in d and 'timeout' in d:
            return Action(d['id'], d['args'], d['isEvent'], d['timeout'])
        else:
            return d
    if d['tag'] == 'Start':
        return Start(dependencies=d['dependencies'])
    if d['tag'] == 'RequestAction':
        return RequestAction(action=d['action'], version=d['version'])
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
