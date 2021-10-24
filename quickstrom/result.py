import quickstrom.protocol as protocol
from quickstrom.hash import dict_hash
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

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
    value: T


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
        return Modified(f(diff.value))
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
        return diff.value
    elif isinstance(diff, Unmodified):
        return diff.value


E = TypeVar('E')
E2 = TypeVar('E2')


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
    from_state: Optional[State[E, I]]
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

Result = Union[Failed[E, I], Passed[E, I], Errored]

ResultWithScreenshots = Result[protocol.JsonLike, I]

PlainResult = ResultWithScreenshots[bytes]


def map_states( r: Result[E, I], f: Callable[[State[E, I]], State[E2, O]]
) -> Result[E2, O]:
    def on_test(test: Test):
        return Test(test.validity, [
            Transition(
                f(t.from_state) if t.from_state else None, f(t.to_state),
                t.stutter, t.actions) for t in test.transitions
        ])

    if isinstance(r, Passed):
        return Passed([on_test(test) for test in r.passed_tests])
    elif isinstance(r, Failed):
        return Failed([on_test(test) for test in r.passed_tests],
                      on_test(r.failed_test))
    elif isinstance(r, Errored):
        return Errored(r.error, r.tests)


def from_state(state: protocol.State) -> State[protocol.JsonLike, bytes]:
    return State(dict_hash(state), state, None)


def transitions_from_trace(
        full_trace: protocol.Trace
) -> List[Transition[protocol.JsonLike, bytes]]:
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
    last_state: Optional[State] = None
    while len(trace) > 0:
        actions = pop(protocol.TraceActions)
        new_state = pop(protocol.TraceState)
        to_state = from_state(new_state.state)
        transitions.append(
            Transition(
                from_state=last_state,
                to_state=to_state,
                actions=actions.actions,
                stutter=False,
            ))
        last_state = to_state

    return transitions


def from_protocol_result(result: protocol.Result) -> PlainResult:
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


DiffedResult = Union[Failed[Diff[protocol.JsonLike], I],
                     Passed[Diff[protocol.JsonLike], I], Errored]


def diff_states(
    old: State[protocol.JsonLike, I], new: State[protocol.JsonLike, I]
) -> Tuple[State[Diff[protocol.JsonLike], I], State[Diff[protocol.JsonLike],
                                                    I]]:
    old_result_queries = {}
    new_result_queries = {}

    for sel in new.queries.keys():
        old_elements: List[Dict[str, protocol.JsonLike]] = old.queries.get(
            sel, [])    # type: ignore
        new_elements: List[Dict[str, protocol.JsonLike]] = new.queries.get(
            sel, [])    # type: ignore

        old_by_ref = {el['ref']: el for el in old_elements}
        new_by_ref = {el['ref']: el for el in new_elements}

        def diff_old(
                el: Dict[str, protocol.JsonLike]) -> Diff[protocol.JsonLike]:
            ref = el['ref']
            if ref in new_by_ref:
                new_el = new_by_ref[ref]
                if new_el == el:
                    return Unmodified(el)
                else:
                    return Modified(el)
            else:
                return Removed(el)

        def diff_new(
                el: Dict[str, protocol.JsonLike]) -> Diff[protocol.JsonLike]:
            ref = el['ref']
            if ref in old_by_ref:
                old_el = old_by_ref[ref]
                if old_el == el:
                    return Unmodified(el)
                else:
                    return Modified(el)
            else:
                return Added(el)

        old_result_queries[sel] = [diff_old(el) for el in old_elements]
        new_result_queries[sel] = [diff_new(el) for el in new_elements]

    return (State(old.hash, old_result_queries, old.screenshot),
            State(new.hash, new_result_queries, new.screenshot))


def diff_transitions(
    ts: List[Transition[protocol.JsonLike, I]]
) -> List[Transition[Diff[protocol.JsonLike], I]]:
    results: List[Transition[Diff[protocol.JsonLike], I]] = []
    last_state = None
    for t in ts:
        stutter = last_state is not None and last_state.hash == t.to_state.hash

        def _diff_states():
            if last_state is None:
                return (None, mark_unmodified(t.to_state))
            elif stutter:
                return (mark_unmodified(last_state), mark_unmodified(t.to_state))
            else:
                return diff_states(last_state, t.to_state)

        (diff_old, diff_new) = _diff_states()
        results.append(
            Transition(from_state=diff_old,
                       to_state=diff_new,
                       stutter=stutter,
                       actions=t.actions))
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

def mark_unmodified(s: State[E, I]) -> State[Diff[E], I]:
    return State(s.hash, { sel: [Unmodified(e) for e in es] for sel, es in s.queries.items() }, s.screenshot)

def mark_all_unmodified(r: Result[E, I]) -> Result[Diff[E], I]:
    return map_states(r, mark_unmodified)