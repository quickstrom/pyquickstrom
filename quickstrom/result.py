import quickstrom.protocol as protocol
from quickstrom.hash import dict_hash
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

Selector = str

I = TypeVar('I')
O = TypeVar('O')


@dataclass(frozen=True, eq=True)
class Screenshot(Generic[I]):
    image: I
    width: int
    height: int
    scale: int


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


def new_value(diff: Diff[T2]) -> T2:
    if isinstance(diff, Added):
        return diff.value
    elif isinstance(diff, Removed):
        return diff.value
    elif isinstance(diff, Modified):
        return diff.new
    elif isinstance(diff, Unmodified):
        return diff.value


E = TypeVar('E')


@dataclass(frozen=False)
class State(Generic[E, I]):
    hash: str
    queries: Dict[Selector, List[E]]
    screenshot: Optional[Screenshot[I]]


@dataclass(frozen=True)
class Initial(Generic[E, I]):
    events: List[protocol.Action]
    state: State[E, I]


@dataclass(frozen=True)
class Transition(Generic[E, I]):
    to_state: State[E, I]
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test(Generic[E, I]):
    validity: protocol.Validity
    transitions: List[Transition[E, I]]


@dataclass(frozen=True)
class Errored():
    error: str
    tests: int


@dataclass(frozen=True)
class Failed(Generic[E, I]):
    passed_tests: List[Test[E, I]]
    failed_test: Test[E, I]


@dataclass(frozen=True)
class Passed(Generic[E, I]):
    passed_tests: List[Test[E, I]]


ResultWithScreenshots = Union[Failed[protocol.JsonLike, I],
                              Passed[protocol.JsonLike, I], Errored]

Result = ResultWithScreenshots[bytes]


def map_states(
    r: ResultWithScreenshots[I], f: Callable[[State[protocol.JsonLike, I]],
                                             State[protocol.JsonLike, O]]
) -> ResultWithScreenshots[O]:
    def on_test(test: Test):
        return Test(test.validity, [
            Transition(f(t.to_state), t.stutter, t.actions)
            for t in test.transitions
        ])

    if isinstance(r, Passed):
        return Passed([on_test(test) for test in r.passed_tests])
    elif isinstance(r, Failed):
        return Failed([on_test(test) for test in r.passed_tests],
                      on_test(r.failed_test))
    elif isinstance(r, Errored):
        return Errored(r.error, r.tests)


def from_state(state: protocol.State) -> State:
    return State(dict_hash(state), state, None)


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


DiffedResult = Union[Failed[Diff[protocol.JsonLike], I],
                     Passed[Diff[protocol.JsonLike], I], Errored]


def diff_states(
        old: State[protocol.JsonLike, I],
        new: State[protocol.JsonLike, I]) -> State[Diff[protocol.JsonLike], I]:
    result_queries = {}

    for sel in new.queries.keys():
        old_elements: List[Dict[str, protocol.JsonLike]] = old.queries.get(
            sel, [])    # type: ignore
        new_elements: List[Dict[str, protocol.JsonLike]] = new.queries.get(
            sel, [])    # type: ignore

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

    return State(new.hash, result_queries, new.screenshot)


def diff_transitions(
    ts: List[Transition[protocol.JsonLike, I]]
) -> List[Transition[Diff[protocol.JsonLike], I]]:
    results: List[Transition[Diff[protocol.JsonLike], I]] = []
    last_state = State("", {}, None)
    for t in ts:
        stutter = last_state.hash == t.to_state.hash
        # TODO: no diff if stutter, just mark everything unmodified
        diffed = diff_states(last_state, t.to_state)
        results.append(
            Transition(to_state=diffed, stutter=stutter, actions=t.actions))
        last_state = t.to_state
    return results


def diff_test(
        test: Test[protocol.JsonLike, I]) -> Test[Diff[protocol.JsonLike], I]:
    return Test(test.validity, diff_transitions(test.transitions))


def diff_result(result: ResultWithScreenshots[I]) -> DiffedResult[I]:
    if isinstance(result, Errored):
        return result
    elif isinstance(result, Failed):
        return Failed([diff_test(test) for test in result.passed_tests],
                      diff_test(result.failed_test))
    elif isinstance(result, Passed):
        return Passed([diff_test(test) for test in result.passed_tests])
