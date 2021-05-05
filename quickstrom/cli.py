import logging
import click
from typing import List
from urllib.parse import urljoin, urlparse
from pathlib import Path

import quickstrom.executor as executor
import quickstrom.printer as printer


class NoWebdriverFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith('selenium.webdriver.remote')

global_options = { 'includes': [] }

@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|ERROR)')
@click.option('-I', '--include', multiple=True, help='include a path in the Specstrom module search paths')
def root(log_level, include):
    global_options['includes'] = include
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("selenium.webdriver.remote").setLevel(logging.INFO)


@click.command()
@click.argument('module')
@click.argument('origin')
@click.option('-B', '--browser', default='firefox')
@click.option('-S', '--capture-screenshots/--no-capture-screenshots', default=False, help='capture a screenshot at each state and write to /tmp')
@click.option('--show-trace-on-success/--no-show-trace-on-success', default=False, help='capture a screenshot at each state and write to /tmp')
def check(module: str, origin: str, browser: executor.Browser, capture_screenshots: bool, show_trace_on_success: bool):
    """Checks the configured properties in the given module."""
    origin_url = urlparse(urljoin("file://", origin))
    if origin_url.scheme == "file" and not Path(origin_url.path).is_file():
        print(f"File does not exist: {origin}")
        exit(1)
    try:
        results = executor.Check(
            module, origin_url.geturl(), browser, global_options['includes'], capture_screenshots).execute()
        printer.print_results(results, show_trace_on_success=show_trace_on_success)
        if any([not r.valid.value for r in results]):
            exit(3)
    except executor.SpecstromError as err:
        print(err)
        print(
            f"See interpreter log file for details: {err.log_file}")
        exit(1)


root.add_command(check)


def run(): root()
