import logging
import click
from typing import List
from urllib.parse import urljoin

import quickstrom.executor as executor

class NoWebdriverFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith('selenium.webdriver.remote')

@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|EROR)')
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
    origin_url = urljoin("file://", origin)
    executor.Check(module, origin_url, browser, include, capture_screenshots).execute()

root.add_command(check)

def run(): root()