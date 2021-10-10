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

T2 = TypeVar('T2')


def map_diff(f: Callable[[T], T2], diff: Diff[T]) -> Diff[T2]:
    if isinstance(diff, Added):
        return Added(f(diff.value))
    elif isinstance(diff, Removed):
        return Removed(f(diff.value))
    elif isinstance(diff, Modified):
        return Modified(f(diff.old), f(diff.new))
    elif isinstance(diff, Unmodified):
        return Unmodified(f(diff.value))
    else:
        raise TypeError(f"{diff} is not a Diff")


def new_value(diff: Diff[T]) -> Union[T]:
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
    queries: Dict[Selector, List[E]]
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


DiffedResult = Union[Failed[Diff[protocol.JsonLike]],
                     Passed[Diff[protocol.JsonLike]], Errored]


def diff_states(
        old: State[protocol.JsonLike],
        new: State[protocol.JsonLike]) -> State[Diff[protocol.JsonLike]]:
    result_queries = {}

    for sel in new.queries.keys():
        old_elements: List[Dict[str, protocol.JsonLike]] = old.queries.get(sel, [])    # type: ignore
        new_elements: List[Dict[str, protocol.JsonLike]] = new.queries.get(sel, [])    # type: ignore
                
        old_by_ref = {el['ref']: el for el in old_elements}
        new_by_ref = {el['ref']: el for el in new_elements}
        removed_refs = old_by_ref.keys() - new_by_ref.keys()

        query_elements: List[Diff[protocol.JsonLike]] = []
        for ref in removed_refs:
            query_elements.append(Removed(old_by_ref[ref]))
        for el in new_elements:
            if el['ref'] in old_by_ref:
                old_el = old_by_ref[el['ref']]
                if old_el == el:
                    query_elements.append(Unmodified(el))
                else:
                    query_elements.append(Modified(old_el, el))
            else:
                query_elements.append(Added(el))

        result_queries[sel] = query_elements

    return State(result_queries, new.screenshot)


def diff_transitions(
    ts: List[Transition[protocol.JsonLike]]
) -> List[Transition[Diff[protocol.JsonLike]]]:
    results: List[Transition[Diff[protocol.JsonLike]]] = []
    last_state = State({}, None)
    for t in ts:
        stutter = last_state == t.to_state
        # TODO: no diff if stutter, just mark everything unmodified
        diffed = diff_states(last_state, t.to_state)
        results.append(
            Transition(to_state=diffed, stutter=stutter, actions=t.actions))
        last_state = t.to_state
    return results


def diff_test(test: Test[protocol.JsonLike]) -> Test[Diff[protocol.JsonLike]]:
    return Test(test.validity, diff_transitions(test.transitions))


def diff_result(result: Result) -> DiffedResult:
    if isinstance(result, Errored):
        return result
    elif isinstance(result, Failed):
        return Failed([diff_test(test) for test in result.passed_tests],
                      diff_test(result.failed_test))
    elif isinstance(result, Passed):
        return Passed([diff_test(test) for test in result.passed_tests])
