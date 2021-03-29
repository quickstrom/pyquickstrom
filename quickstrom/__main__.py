from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import logging
import executor
import click

# driver = webdriver.Chrome()
# 
# driver.set_network_conditions(
#     offline=False,
#     latency=500,
#     throughput=500*1024,
# )
# 
# driver.get("http://wickstrom.tech")
# assert "Oskar" in driver.title
# driver.close()

@click.group()
@click.option('--log-level', default='WARN', help='log level (DEBUG|INFO|WARN|EROR)')
def cli(log_level):
    logging.basicConfig(level=getattr(logging, log_level.upper()))

@click.command()
@click.argument('module')
def check(module):
    """Checks the configured properties in the given module."""
    executor.Check(module).execute()

cli.add_command(check)

cli()