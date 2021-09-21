from itertools import chain
from typing import List
import quickstrom.reporter.json as json_reporter
from hypothesis.strategies._internal.misc import just
import quickstrom.protocol as protocol
from hypothesis import given
from hypothesis.strategies import integers
from hypothesis.strategies._internal.core import booleans, composite, dictionaries, lists, text
from hypothesis.strategies._internal.strategies import SearchStrategy, one_of


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


def element_states() -> SearchStrategy[protocol.ElementState]:
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

    first = draw(trace_states())
    rest = list(chain(*draw(lists(pairs(), max_size=10))))

    return [first] + rest


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


def result_from_report(report: json_reporter.Report):
    def to_trace(test: json_reporter.Test) -> protocol.Trace:
        def to_trace_elements(
            transition: json_reporter.Transition
        ) -> List[protocol.TraceElement]:
            return [
                protocol.TraceActions(transition.actions),
                protocol.TraceState(transition.toState),
            ]

        initial: List[protocol.TraceElement] = [
            protocol.TraceState(test.initial_state)
        ]
        return initial + [
            e for t in test.transitions for e in to_trace_elements(t)
        ]

    if isinstance(report.result, json_reporter.Passed):
        # TODO: we need to support multiple tests later on
        test = report.result.passedTests[0]
        return protocol.RunResult(test.validity, to_trace(test))
    elif isinstance(report.result, json_reporter.Failed):
        # TODO: we need to support multiple tests later on
        test = report.result.failedTest
        return protocol.RunResult(test.validity, to_trace(test))
    elif isinstance(report.result, json_reporter.Errored):
        return protocol.ErrorResult(report.result.error)
    else:
        raise TypeError(f"Invalid report: {report}")


@given(results())
def test_json_reporter_roundtrip(result):
    report = json_reporter.report_from_result(result)
    new_result = result_from_report(report)
    assert new_result == result
