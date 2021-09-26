import logging
from quickstrom.protocol import ErrorResult, RunResult
from quickstrom.reporter import Reporter
import click
from typing import cast, Dict, List
from urllib.parse import urljoin, urlparse
from pathlib import Path

import quickstrom.executor as executor
import quickstrom.reporter.json as json_reporter
import quickstrom.reporter.html as html_reporter
import quickstrom.reporter.console as console_reporter


class NoWebdriverFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith('selenium.webdriver.remote')


global_options: Dict[str, object] = {'includes': []}


@click.group()
@click.option('--log-level',
              default='WARN',
              help='log level (DEBUG|INFO|WARN|ERROR)')
@click.option('-I',
              '--include',
              multiple=True,
              help='include a path in the Specstrom module search paths')
def root(log_level, include):
    global_options['includes'] = include
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("selenium.webdriver.remote").setLevel(logging.INFO)


@click.command()
@click.argument('module')
@click.argument('origin')
@click.option('-B', '--browser', default='firefox')
@click.option('-S',
              '--capture-screenshots/--no-capture-screenshots',
              default=False,
              help='capture a screenshot at each state and write to /tmp')
@click.option('--console-report-on-success/--no-console-report-on-success',
              default=False,
              help='capture a screenshot at each state and write to /tmp')
@click.option('--reporter',
              multiple=True,
              default=['console'],
              help='enable a reporter by name')
@click.option('--json-report-file', default='report.json')
@click.option('--html-report-directory', default='html-report')
def check(module: str, origin: str, browser: executor.Browser,
          capture_screenshots: bool, console_report_on_success: bool,
          reporter: List[str], json_report_file: Path,
          html_report_directory: Path):
    """Checks the configured properties in the given module."""
    def reporters_by_names(names: List[str]) -> List[Reporter]:
        all_reporters = {
            'json': json_reporter.JsonReporter(json_report_file),
            'html': html_reporter.HtmlReporter(html_report_directory),
            'console':
            console_reporter.ConsoleReporter(console_report_on_success)
        }
        chosen_reporters = []
        for name in names:
            if name in all_reporters:
                chosen_reporters.append(all_reporters[name])
            else:
                raise click.UsageError(f"There is no reporter called `{name}`")
        return chosen_reporters

    origin_url = urlparse(urljoin("file://", origin))
    if origin_url.scheme == "file" and not Path(origin_url.path).is_file():
        print(f"File does not exist: {origin}")
        exit(1)
    try:
        results = executor.Check(module, origin_url.geturl(), browser,
                                 cast(List[str], global_options['includes']),
                                 capture_screenshots).execute()
        chosen_reporters = reporters_by_names(reporter)
        for result in results:
            for r in chosen_reporters:
                r.report(result)

            if isinstance(result, RunResult):
                click.echo(
                    f"Result: {result.valid.certainty} {result.valid.value}")
            elif isinstance(result, ErrorResult):
                click.echo(f"Error: {result.error}")

        if any([(isinstance(r, ErrorResult) or not r.valid.value)
                for r in results]):
            exit(3)
    except executor.SpecstromError as err:
        print(err)
        print(f"See interpreter log file for details: {err.log_file}")
        exit(1)


root.add_command(check)


def run():
    root()
