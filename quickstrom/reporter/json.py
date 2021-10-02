from dataclasses import dataclass
import dataclasses
import json
from typing import IO, Any, Dict, List, Type, TypeVar, Union

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

    transitions: List[Transition] = []
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
        else:
            return Errored(result.error, 1)

    return Report(to_result(), datetime.utcnow())


@dataclass
class JsonReporter(Reporter):
    path: Path

    def report(self, result: protocol.Result):
        report = report_from_result(result)
        encode_file(report, self.path)


def encode_str(report: Report) -> str:
    return json.dumps(report, cls=_ReporterEncoder)

def encode_to(report: Report, fp: IO[str]):
    json.dump(report, fp, cls=_ReporterEncoder)

def encode_file(report: Report, output_path: Path):
    with open(output_path, 'w') as f:
        encode_to(report, f)


class _ReporterEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Dict[str, Any]:
        if isinstance(o, Report):
            return {
                'result': self.default(o.result),
                'generatedAt': str(o.generated_at),
                'tag': 'Report'
            }
        elif isinstance(o, Passed):
            return {
                'tag': 'Passed',
                'passedTests':
                [self.default(test) for test in o.passedTests],
            }
        elif isinstance(o, Errored):
            return {
                'tag': 'Errored',
                'error': o.error,
                'tests': o.tests,
            }
        elif isinstance(o, Failed):
            return {
                'tag': 'Failed',
                'passedTests':
                [self.default(test) for test in o.passedTests],
                'failedTest': self.default(o.failedTest)
            }
        elif isinstance(o, Test):
            return {
                'validity': self.default(o.validity),
                'initial': o.initial,
                'transitions': [self.default(t) for t in o.transitions],
            }
        elif isinstance(o, Initial):
            return {
                'events': [self.default(t) for t in o.events],
                'state': o.state,
            }
        elif isinstance(o, Transition):
            return {
                'fromState': o.fromState,
                'toState': o.toState,
                'stutter': o.stutter,
                'actions': [self.default(t) for t in o.actions],
            }
        elif isinstance(o, protocol.Action):
            return {
                'id': o.id,
                'args': o.args,
                'isEvent': o.isEvent,
                'timeout': o.timeout
            }
        elif isinstance(o, protocol.Validity):
            return dataclasses.asdict(o)
        else:
            return json.JSONEncoder.default(self, o)
