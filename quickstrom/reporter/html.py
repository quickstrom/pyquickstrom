from dataclasses import dataclass
import os
from pathlib import Path
import shutil
from quickstrom.reporter import Reporter
import quickstrom.reporter.json as json_reporter
import quickstrom.protocol as protocol


@dataclass
class HtmlReporter(Reporter):
    path: Path

    def report(self, result: protocol.Result):
        report = json_reporter.report_from_result(result)
        report_assets_dir = os.getenv('QUICKSTROM_HTML_REPORT_DIRECTORY')
        if report_assets_dir is None:
            raise RuntimeError('HTML report assets directory is not configured')
        os.makedirs(self.path)
        for f in os.listdir(report_assets_dir):
            shutil.copy(Path(report_assets_dir) / f, Path(self.path) / f)
        jsonp_path = Path(self.path) / 'report.jsonp.js'
        with open(jsonp_path, 'w') as f:
            f.write('window.report = ')
            json_reporter.encode_to(report, f)
