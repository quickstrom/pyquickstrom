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


@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|ERROR)')
def root(log_level):
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("selenium.webdriver.remote").setLevel(logging.INFO)


@click.command()
@click.argument('module')
@click.argument('origin')
@click.option('-B', '--browser', default='firefox')
@click.option('-I', '--include', multiple=True, help='include a path in the Specstrom module search paths')
@click.option('-S', '--capture-screenshots', help='capture a screenshot at each state and write to /tmp')
def check(module: str, origin: str, browser: executor.Browser, include: List[str], capture_screenshots):
    """Checks the configured properties in the given module."""
    origin_url = urlparse(urljoin("file://", origin))
    print(origin_url.geturl(), Path(origin_url.path).is_file())
    if origin_url.scheme == "file" and not Path(origin_url.path).is_file():
        print(f"File does not exist: {origin}")
        exit(1)
    try:
        results = executor.Check(
            module, origin_url.geturl(), browser, include, capture_screenshots).execute()
        printer.print_results(results)
        if any([not r.valid.value for r in results]):
            exit(3)
    except executor.SpecstromError as err:
        print(err)
        print(
            f"See interpreter log file for details: {err.log_file}")
        exit(1)


root.add_command(check)


def run(): root()
