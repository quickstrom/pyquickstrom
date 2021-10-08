from deepdiff import DeepDiff
import quickstrom.protocol as protocol
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

Selector = str


@dataclass(frozen=True, eq=True)
class Screenshot():
    url: Path
    width: int
    height: int


T = TypeVar('T', contravariant=True)


@dataclass(frozen=True, eq=True)
class Added(Generic[T]):
    value: T


@dataclass(frozen=True, eq=True)
class Removed(Generic[T]):
    value: T


@dataclass(frozen=True, eq=True)
class Modified(Generic[T]):
    old: T
    new: T


@dataclass(frozen=True, eq=True)
class Unmodified(Generic[T]):
    value: T


Diff = Union[Added[T], Removed[T], Modified[T], Unmodified[T]]

DiffedValue = Union[Diff[Union[str, int, float, None]], List['DiffedValue'],
                    Dict[Diff[str], 'DiffedValue']]

T2 = TypeVar('T2')
def map_diff(
        f: Callable[[T], T2],
        diff: Diff[T]
) -> Diff[T2]:
    if isinstance(diff, Added):
        return Added(f(diff.value))
    elif isinstance(diff, Removed):
        return Removed(f(diff.value))
    elif isinstance(diff, Modified):
        return Modified(f(diff.old), f(diff.new))
    elif isinstance(diff, Unmodified):
        return Unmodified(f(diff.value))

def new_value(
    diff: Diff[T]
) -> Union[T]:
    if isinstance(diff, Added):
        return diff.value
    elif isinstance(diff, Removed):
        return diff.value
    elif isinstance(diff, Modified):
        return diff.new
    elif isinstance(diff, Unmodified):
        return diff.value


S = TypeVar('S')
E = TypeVar('E')


@dataclass(frozen=True)
class State(Generic[S, E]):
    queries: Dict[S, List[E]]
    screenshot: Optional[Screenshot]


@dataclass(frozen=True)
class Initial(Generic[S, E]):
    events: List[protocol.Action]
    state: State[S, E]


@dataclass(frozen=True)
class Transition(Generic[S, E]):
    to_state: State[S, E]
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test(Generic[S, E]):
    validity: protocol.Validity
    transitions: List[Transition[S, E]]


@dataclass(frozen=True)
class Errored():
    error: str
    tests: int


@dataclass(frozen=True)
class Failed(Generic[S, E]):
    passed_tests: List[Test[S, E]]
    failed_test: Test[S, E]


@dataclass(frozen=True)
class Passed(Generic[S, E]):
    passed_tests: List[Test[S, E]]


Result = Union[Failed[protocol.Selector, protocol.JsonLike],
               Passed[protocol.Selector, protocol.JsonLike], Errored]


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


DiffedResult = Union[Failed[Diff[Selector], DiffedValue],
                     Passed[Diff[Selector], DiffedValue], Errored]


def diff_state(
        state_diff: DeepDiff,
        state: State[str, protocol.JsonLike]) -> State[Diff[str], DiffedValue]:

    diffs_by_path: Dict[str, Diff[protocol.JsonLike]] = {}
    key_diffs_by_path: Dict[str, Callable[[str], Diff[str]]] = {}

    if 'values_changed' in state_diff:
        for path, diff in state_diff['values_changed'].items():
            diffs_by_path[path] = Modified(diff['old_value'],
                                           diff['new_value'])    # type: ignore
    if 'type_changes' in state_diff:
        for path, diff in state_diff['type_changes'].items():
            diffs_by_path[path] = Modified(diff['old_value'],
                                           diff['new_value'])    # type: ignore

    if 'iterable_item_added' in state_diff:
        for path, diff in state_diff['iterable_item_added'].items():
            diffs_by_path[path] = Added(diff)    # type: ignore

    if 'iterable_item_removed' in state_diff:
        for path, diff in state_diff['iterable_item_removed'].items():
            diffs_by_path[path] = Removed(diff)    # type: ignore

    if 'dictionary_item_added' in state_diff:
        for path in state_diff['dictionary_item_added']:
            key_diffs_by_path[path] = lambda x: Added(x)

    if 'dictionary_item_removed' in state_diff:
        for path in state_diff['dictionary_item_removed']:
            key_diffs_by_path[path] = lambda x: Removed(x)

    def key_diff(nested_path: str) -> Callable[[str], Diff[str]]:
        return key_diffs_by_path.get(nested_path, lambda x: Unmodified(x))

    def value_diff(diff_path: str, value: protocol.JsonLike) -> DiffedValue:
        if isinstance(value, dict):

            return {
                key_diff(nested_path)(key): value_diff(nested_path, nested)
                for key, nested in value.items()
                for nested_path in [f"{diff_path}['{key}']"]
            }
        elif isinstance(value, list):
            return [
                value_diff(f"{diff_path}['{i}']", nested)
                for i, nested in enumerate(value)
            ]
        else:
            return diffs_by_path[
                diff_path] if diff_path in diffs_by_path else Unmodified(value)

    diffed_state: Dict[Diff[Selector], List[DiffedValue]] = {
        key_diff(f"root['{sel}']")(sel):
        [value_diff(f"root['{sel}'][{i}]", e) for i, e in enumerate(elements)]
        for sel, elements in state.queries.items()
    }

    return State(diffed_state, state.screenshot)


def diff_transitions(
    ts: List[Transition[Selector, protocol.JsonLike]]
) -> List[Transition[Diff[Selector], DiffedValue]]:
    results: List[Transition[Diff[Selector], DiffedValue]] = []
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


def diff_test(
    test: Test[Selector,
               protocol.JsonLike]) -> Test[Diff[Selector], DiffedValue]:
    return Test(test.validity, diff_transitions(test.transitions))


def diff_result(result: Result) -> DiffedResult:
    if isinstance(result, Errored):
        return result
    elif isinstance(result, Failed):
        return Failed([diff_test(test) for test in result.passed_tests],
                      diff_test(result.failed_test))
    elif isinstance(result, Passed):
        return Passed([diff_test(test) for test in result.passed_tests])
