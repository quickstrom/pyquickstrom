from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shutil
from quickstrom.reporter import Reporter
import quickstrom.reporter.json as json_reporter
from quickstrom.result import Result, diff_result


@dataclass
class HtmlReporter(Reporter):
    path: Path

    def report(self, result: Result):
        report = json_reporter.Report(diff_result(result), datetime.utcnow())
        report_assets_dir = os.getenv('QUICKSTROM_HTML_REPORT_DIRECTORY')
        if report_assets_dir is None:
            raise RuntimeError(
                'HTML report assets directory is not configured')
        os.makedirs(self.path)
        for f in os.listdir(report_assets_dir):
            shutil.copy(Path(report_assets_dir) / f, Path(self.path) / f)
        jsonp_path = Path(self.path) / 'report.jsonp.js'
        with open(jsonp_path, 'w') as f:
            f.write('window.report = ')
            json_reporter.encode_to(report, f)
