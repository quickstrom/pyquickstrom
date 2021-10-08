from deepdiff import DeepDiff
import quickstrom.protocol as protocol
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generic, List, Optional, Type, TypeVar, Union

Selector = str


@dataclass(frozen=True)
class Screenshot():
    url: Path
    width: int
    height: int


T = TypeVar('T', contravariant=True)


@dataclass
class Added(Generic[T]):
    value: T


@dataclass
class Removed(Generic[T]):
    value: T


@dataclass
class Modified(Generic[T]):
    old: T
    new: T


@dataclass
class Unmodified(Generic[T]):
    value: T


Diff = Union[Added[T], Removed[T], Modified[T], Unmodified[T]]

DiffedValue = Union[Diff[Union[str, int, float, None]], List['DiffedValue'],
                    Dict[str, 'DiffedValue']]


def new_value(
    diff: DiffedValue
) -> Union[str, int, float, List['DiffedValue'], Dict[str, 'DiffedValue'],
           None]:
    if isinstance(diff, Added):
        return diff.value
    elif isinstance(diff, Removed):
        return diff.value
    elif isinstance(diff, Modified):
        return diff.new
    elif isinstance(diff, Unmodified):
        return diff.value


E = TypeVar('E')


@dataclass(frozen=True)
class State(Generic[E]):
    queries: Dict[protocol.Selector, List[E]]
    screenshot: Optional[Screenshot]


@dataclass(frozen=True)
class Initial(Generic[E]):
    events: List[protocol.Action]
    state: State[E]


@dataclass(frozen=True)
class Transition(Generic[E]):
    to_state: State[E]
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test(Generic[E]):
    validity: protocol.Validity
    transitions: List[Transition[E]]


@dataclass(frozen=True)
class Errored():
    error: str
    tests: int


@dataclass(frozen=True)
class Failed(Generic[E]):
    passed_tests: List[Test[E]]
    failed_test: Test[E]


@dataclass(frozen=True)
class Passed(Generic[E]):
    passed_tests: List[Test[E]]


Result = Union[Failed[protocol.JsonLike], Passed[protocol.JsonLike], Errored]


def from_state(state: protocol.State) -> State:
    return State(state, None)


def transitions_from_trace(full_trace: protocol.Trace) -> List[Transition]:
    A = TypeVar('A')
    trace = list(full_trace.copy())

    def pop(cls: Type[A]) -> A:
        assert len(trace) > 0
        first = trace.pop(0)
        if isinstance(first, cls):
            return first
        else:
            raise TypeError(f"Expected a {cls} in trace but got {type(first)}")

    transitions: List[Transition] = []
    while len(trace) > 0:
        actions = pop(protocol.TraceActions)
        new_state = pop(protocol.TraceState)
        transitions.append(
            Transition(
                to_state=from_state(new_state.state),
                actions=actions.actions,
                stutter=False,
            ))

    return transitions


def from_protocol_result(result: protocol.Result) -> Result:
    def to_result() -> Result:
        if isinstance(result, protocol.RunResult):
            if result.valid.value:
                return Passed(
                    [Test(result.valid, transitions_from_trace(result.trace))])
            else:
                return Failed([],
                              Test(result.valid,
                                   transitions_from_trace(result.trace)))
        else:
            return Errored(result.error, 1)

    return to_result()


DiffedResult = Union[Failed[DiffedValue], Passed[DiffedValue], Errored]


def diff_state(state_diff: DeepDiff,
               state: State[protocol.JsonLike]) -> State[DiffedValue]:

    diffs_by_path: Dict[str, Diff[protocol.JsonLike]] = {}

    if 'values_changed' in state_diff:
        for path, diff in state_diff['values_changed'].items():
            diffs_by_path[path] = Modified(diff['old_value'],
                                           diff['new_value'])    # type: ignore

    if 'iterable_item_added' in state_diff:
        for path, diff in state_diff['iterable_item_added'].items():
            diffs_by_path[path] = Added(diff)    # type: ignore

    if 'iterable_item_removed' in state_diff:
        for path, diff in state_diff['iterable_item_removed'].items():
            diffs_by_path[path] = Removed(diff)    # type: ignore

    def value_diff(diff_path: str, value: protocol.JsonLike) -> DiffedValue:
        if isinstance(value, dict):
            return {
                key: value_diff(f"{diff_path}['{key}']", nested)
                for key, nested in value.items()
            }
        elif isinstance(value, list):
            return [
                value_diff(f"{diff_path}['{i}']", nested)
                for i, nested in enumerate(value)
            ]
        else:
            return diffs_by_path[
                diff_path] if diff_path in diffs_by_path else Unmodified(value)

    diffed_state: Dict[Selector, List[DiffedValue]] = {
        sel: [value_diff(f"root['{sel}'][{i}]", e) for i, e in enumerate(elements)]   
        for sel, elements in state.queries.items()
    }

    return State(diffed_state, state.screenshot)


def diff_transitions(
        ts: List[Transition[protocol.JsonLike]]
) -> List[Transition[DiffedValue]]:
    results: List[Transition[DiffedValue]] = []
    last_state = State({}, None)
    for t in ts:
        # DeepDiff is both a dict and a class we can init in a special
        # way, so pyright must be silenced.
        diff = DeepDiff(last_state.queries, t.to_state.queries)    # type: ignore
        results.append(
            Transition(to_state=diff_state(diff, t.to_state),
                       stutter=bool(diff),
                       actions=t.actions))
        last_state = t.to_state
    return results


def diff_test(test: Test[protocol.JsonLike]) -> Test[DiffedValue]:
    return Test(test.validity, diff_transitions(test.transitions))


def diff_result(result: Result) -> DiffedResult:
    if isinstance(result, Errored):
        return result
    elif isinstance(result, Failed):
        return Failed([diff_test(test) for test in result.passed_tests],
                      diff_test(result.failed_test))
    elif isinstance(result, Passed):
        return Passed([diff_test(test) for test in result.passed_tests])
