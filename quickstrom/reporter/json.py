from dataclasses import dataclass
import dataclasses
import json
from typing import IO, Any, Dict
import quickstrom.protocol as protocol
from quickstrom.result import *
from quickstrom.reporter import Reporter
from pathlib import Path
from datetime import datetime


@dataclass(frozen=True)
class Report():
    result: DiffedResult
    generated_at: datetime


@dataclass
class JsonReporter(Reporter):
    path: Path

    def report(self, result: Result):
        report = Report(diff_result(result), datetime.utcnow())
        
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
                'passedTests': [self.default(test) for test in o.passed_tests],
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
                'passedTests': [self.default(test) for test in o.passed_tests],
                'failedTest': self.default(o.failed_test)
            }
        elif isinstance(o, Test):
            return {
                'validity': self.default(o.validity),
                'transitions': [self.default(t) for t in o.transitions],
            }
        elif isinstance(o, Initial):
            return {
                'events': [self.default(t) for t in o.events],
                'state': o.state,
            }
        elif isinstance(o, Transition):
            return {
                'toState': o.to_state,
                'stutter': o.stutter,
                'actions': [self.default(t) for t in o.actions],
            }
        elif isinstance(o, State):
            return {
                'queries': o.queries,
                'screenshot': self.default(o.screenshot) if o.screenshot is not None else None
            }
        elif isinstance(o, Screenshot):
            return {
                'url': o.url,
                'width': o.width,
                'height': o.height,
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
        elif isinstance(o, Added):
            assert(isinstance(o.value, dict))
            o.value['diff'] = 'Added'
            return o.value
        elif isinstance(o, Removed):
            assert(isinstance(o.value, dict))
            o.value['diff'] = 'Removed'
            return o.value
        elif isinstance(o, Modified):
            assert(isinstance(o.new, dict))
            o.new['diff'] = 'Modified'
            return o.new
        elif isinstance(o, Unmodified):
            assert(isinstance(o.value, dict))
            o.value['diff'] = 'Unmodified'
            return o.value
        else:
            return json.JSONEncoder.default(self, o)
