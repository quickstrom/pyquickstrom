import logging
import executor
import click

@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|EROR)')
def cli(log_level):
    logging.basicConfig(level=getattr(logging, log_level.upper()))

@click.command()
@click.argument('module')
@click.argument('origin')
def check(module, origin):
    """Checks the configured properties in the given module."""
    executor.Check(module, origin).execute()

cli.add_command(check)

cli()