from dataclasses import dataclass, is_dataclass
import dataclasses
import json
from typing import List, Type, TypeVar, Union, no_type_check

import quickstrom.protocol as protocol
from quickstrom.reporter import Reporter
from pathlib import Path
from datetime import datetime


@dataclass(frozen=True)
class Transition():
    fromState: protocol.State
    toState: protocol.State
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test():
    validity: protocol.Validity
    initial_state: protocol.State
    transitions: List[Transition]


def transitions_from_trace(full_trace: protocol.Trace) -> List[Transition]:
    A = TypeVar('A')
    trace = full_trace.copy()

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
    tag = "Errored"


@dataclass(frozen=True)
class Failed():
    passedTests: List[Test]
    failedTest: Test
    tag = "Passed"


@dataclass(frozen=True)
class Passed():
    passedTests: List[Test]
    tag = "Passed"


Result = Union[Failed, Passed, Errored]


@dataclass(frozen=True)
class Report():
    result: Result
    generated_at: datetime


@no_type_check
def report_from_result(result: Result) -> Report:
    def to_result() -> Result:
        if isinstance(result, protocol.RunResult):
            if result.valid.value:
                return Passed([
                    Test(result.valid, result.trace[0].state,
                         transitions_from_trace(result.trace))
                ])
            else:
                return Failed([],
                              Test(result.valid, result.trace[0].state,
                                   transitions_from_trace(result.trace)))
        elif isinstance(result, protocol.ErrorResult):
            return Errored(result.error, 1)
        else:
            raise TypeError(
                f"cannot convert the given value to a JSON report: {result}")

    return Report(to_result(), datetime.utcnow())


@dataclass
class Reporter(Reporter):
    path: Path

    def report(self, result: Result):
        print(json.dumps(result, cls=_ReporterEncoder))


class _ReporterEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return json.JSONEncoder.default(self, dataclasses.asdict(obj))
        else:
            return json.JSONEncoder.default(self, obj)
