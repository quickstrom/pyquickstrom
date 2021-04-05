import logging
import click
from typing import List

import quickstrom.executor as executor

@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|EROR)')
def cli(log_level):
    logging.basicConfig(level=getattr(logging, log_level.upper()))

@click.command()
@click.argument('module')
@click.argument('origin')
@click.option('-I', '--include', multiple=True, help='include a path in the Specstrom module search paths')
def check(module: str, origin: str, include: List[str]):
    """Checks the configured properties in the given module."""
    executor.Check(module, origin, include).execute()

cli.add_command(check)

cli()