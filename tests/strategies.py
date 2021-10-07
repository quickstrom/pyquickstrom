from itertools import chain
from hypothesis.strategies import integers, just
from hypothesis.strategies._internal.core import booleans, composite, dictionaries, lists, text
from hypothesis.strategies._internal.strategies import SearchStrategy, one_of
import quickstrom.protocol as protocol



def actions():
    return one_of(
        just(
            protocol.Action(id="click",
                            args=["foo"],
                            isEvent=False,
                            timeout=None)))


def trace_actions():
    return lists(actions(), min_size=1,
                 max_size=2).map(lambda a: protocol.TraceActions(a))


def selectors():
    return one_of(
        just(".foo"),
        just("#bar"),
        just("[baz]"),
    )


def element_states() -> SearchStrategy[protocol.JsonLike]:
    return dictionaries(keys=text(alphabet=['a', 'b', 'c'], max_size=3),
                        values=integers(min_value=0, max_value=5),
                        max_size=5)


def states() -> SearchStrategy[protocol.State]:
    return dictionaries(keys=selectors(),
                        values=lists(element_states(), max_size=5),
                        max_size=5)


def trace_states():
    return states().map(lambda s: protocol.TraceState(s))


@composite
def traces(draw):
    @composite
    def pairs(draw):
        return [draw(trace_actions()), draw(trace_states())]

    return list(chain(*draw(lists(pairs(), min_size=1, max_size=10))))


@composite
def validities(draw):
    return protocol.Validity(
        draw(one_of(just('Definitely'), just('Probably'))), draw(booleans()))


@composite
def run_results(draw):
    validity = draw(validities())
    trace = draw(traces())
    return protocol.RunResult(validity, trace)


@composite
def error_results(draw):
    return protocol.ErrorResult(draw(one_of(just("error1"), just("error2"))))


def results():
    return one_of(run_results(), error_results())
