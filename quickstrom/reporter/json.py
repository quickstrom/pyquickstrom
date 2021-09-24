from dataclasses import dataclass, is_dataclass
import dataclasses
import json
from typing import Any, Dict, List, Type, TypeVar, Union

import quickstrom.protocol as protocol
from quickstrom.reporter import Reporter
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class Initial():
    events: List[protocol.Action]
    state: protocol.State

@dataclass(frozen=True)
class Transition():
    fromState: protocol.State
    toState: protocol.State
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test():
    validity: protocol.Validity
    initial: Initial
    transitions: List[Transition]


def transitions_from_trace(full_trace: protocol.Trace) -> List[Transition]:
    A = TypeVar('A')
    # drop the initial events
    trace = list(full_trace.copy()[1:])

    def pop(cls: Type[A]) -> A:
        assert len(trace) > 0
        first = trace.pop(0)
        if isinstance(first, cls):
            return first
        else:
            raise TypeError(f"Expected a {cls} in trace but got {type(first)}")

    transitions = []
    last_state: protocol.TraceState = pop(protocol.TraceState)

    while len(trace) > 0:
        actions = pop(protocol.TraceActions)
        new_state = pop(protocol.TraceState)
        transitions.append(
            Transition(
                fromState=last_state.state,
                toState=new_state.state,
                actions=actions.actions,
                stutter=False,
            ))
        last_state = new_state

    return transitions


@dataclass(frozen=True)
class Errored():
    error: str
    tests: int


@dataclass(frozen=True)
class Failed():
    passedTests: List[Test]
    failedTest: Test


@dataclass(frozen=True)
class Passed():
    passedTests: List[Test]


Result = Union[Failed, Passed, Errored]


@dataclass(frozen=True)
class Report():
    result: Result
    generated_at: datetime


def report_from_result(result: protocol.Result) -> Report:
    def to_result() -> Result:
        if isinstance(result, protocol.RunResult):
            initial = Initial(result.trace[0].actions, result.trace[1].state)    # type: ignore
            if result.valid.value:
                return Passed([
                    Test(result.valid, initial,
                         transitions_from_trace(result.trace))
                ])
            else:
                return Failed([],
                              Test(result.valid, initial,
                                   transitions_from_trace(result.trace)))
        elif isinstance(result, protocol.ErrorResult):
            return Errored(result.error, 1)
        else:
            raise TypeError(
                f"cannot convert the given value to a JSON report: {result}")

    return Report(to_result(), datetime.utcnow())


@dataclass
class JsonReporter(Reporter):
    path: Path

    def report(self, result: protocol.Result):
        report = report_from_result(result)
        encode_file(report, self.path)


def encode_str(report: Report) -> str:
    return json.dumps(report, cls=_ReporterEncoder)


def encode_file(report: Report, output_path: Path):
    with open(output_path, 'w') as f:
        json.dump(report, f, cls=_ReporterEncoder)


class _ReporterEncoder(json.JSONEncoder):
    def default(self, obj):
        def tagged(o: Any, tag: str) -> Dict[str, Any]:
            d = dataclasses.asdict(o)
            d['tag'] = tag
            return d

        if isinstance(obj, Report):
            return {
                'result': self.default(obj.result),
                'generatedAt': str(obj.generated_at),
                'tag': 'Report'
            }
        elif isinstance(obj, Passed):
            return {
                'tag': 'Passed',
                'passedTests':
                [self.default(test) for test in obj.passedTests],
            }
        elif isinstance(obj, Errored):
            return tagged(obj, 'Errored')
        elif isinstance(obj, Failed):
            return {
                'tag': 'Failed',
                'passedTests':
                [self.default(test) for test in obj.passedTests],
                'failedTest': self.default(obj.failedTest)
            }
        elif isinstance(obj, Test):
            return {
                'validity': self.default(obj.validity),
                'initial': obj.initial,
                'transitions': [self.default(t) for t in obj.transitions],
            }
        elif isinstance(obj, Initial):
            return {
                'events': [self.default(t) for t in obj.events],
                'state': obj.state,
            }
        elif isinstance(obj, Transition):
            return {
                'fromState': obj.fromState,
                'toState': obj.toState,
                'stutter': obj.stutter,
                'actions': [self.default(t) for t in obj.actions],
            }
        elif isinstance(obj, protocol.Action):
            return {
                'id': obj.id,
                'args': obj.args,
                'isEvent': obj.isEvent,
                'timeout': obj.timeout
            }
        elif isinstance(obj, protocol.Validity):
            return dataclasses.asdict(obj)
        else:
            return json.JSONEncoder.default(self, obj)
