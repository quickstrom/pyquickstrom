from hypothesis.strategies._internal.misc import Nothing
import quickstrom.protocol as protocol
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar, Union

Selector = str


@dataclass(frozen=True)
class Screenshot():
    url: Path
    width: int
    height: int


JsonLike = Union[str, int, float, List['JsonLike'], Dict[str, 'JsonLike'],
                 Nothing]

T = TypeVar('T')


@dataclass
class Added(Generic[T]):
    value: T


@dataclass
class Removed(Generic[T]):
    value: object


@dataclass
class Modified(Generic[T]):
    old: object
    new: object


@dataclass
class Unmodified(Generic[T]):
    value: object


Diff = Union[Added[T], Removed[T], Modified[T], Unmodified[T]]

DiffedValue = Diff[Union[str, int, float, List['DiffedValue[T]'],
                         Dict[str, 'DiffedValue[T]'], Nothing]]


E = TypeVar('E')

@dataclass(frozen=True)
class Query(Generic[E]):
    selector: protocol.Selector
    elements: List[E]


@dataclass(frozen=True)
class State(Generic[E]):
    queries: List[Query[E]]
    screenshot: Optional[Screenshot]


@dataclass(frozen=True)
class Initial(Generic[E]):
    events: List[protocol.Action]
    state: State[E]


@dataclass(frozen=True)
class Transition(Generic[E]):
    toState: State[E]
    stutter: bool
    actions: List[protocol.Action]


@dataclass(frozen=True)
class Test(Generic[E]):
    validity: protocol.Validity
    initial: Initial[E]
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


Result = Union[Failed[JsonLike], Passed[JsonLike], Errored]

DiffedResult = Union[Failed[DiffedValue], Passed[DiffedValue], Errored]
