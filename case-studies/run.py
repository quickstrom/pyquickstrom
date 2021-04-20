import quickstrom.executor as executor
import quickstrom.printer as printer
import click
import os
from typing import List
from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import pathlib


@dataclass
class TestApp():
    name: str
    module: str
    origin: str


def heading1(s): return click.style(s, bold=True, underline=True)


def heading2(s): return click.style(s, bold=True)


def success(s): return click.style(s, fg='green')


def failure(s): return click.style(s, fg='red')

case_studies_dir = pathlib.Path(__file__).parent
  
ulib_dir = case_studies_dir.parent.joinpath("ulib")

def run(apps: List[TestApp]):
    os.makedirs("results", exist_ok=True)
    browsers: List[executor.Browser] = ["chrome", "firefox"]
    include_paths = list(map(lambda p: str(p.absolute()), [case_studies_dir, ulib_dir]))
    for app in apps:
        checks = [executor.Check(app.module, origin=urljoin("file://", app.origin), browser=browser,
                                 include_paths=include_paths, capture_screenshots=False) for browser in browsers]
        for check in checks:
            with open(f"results/{app.name}.{app.module}.{check.browser}.log", "w") as results_file:
                click.echo(heading1(f"{app.name}"))
                for key, value in asdict(check).items():
                    if key != 'log':
                        click.echo(f"{key}: {value}")
                try:
                    results = check.execute()
                    printer.print_results(results, file=results_file)
                except e:
                    pass
                click.echo("")

                for result in results:
                    color = success if result.valid.value else failure
                    click.echo("details: " + results_file.name)
                    click.echo(
                        "result: " + color(f"{result.valid.certainty} {result.valid.value}"))
                    click.echo("")


def todomvc_url(name: str) -> str:
    base = os.getenv("TODOMVC_DIR") or "https://todomvc.com"
    return f"{base}/examples/{name}/index.html"


all_apps = [
    TestApp("backbone", "todomvc", todomvc_url("backbone")),
    TestApp("react", "todomvc", todomvc_url("react")),
    TestApp("angularjs", "todomvc", todomvc_url("angularjs")),
    TestApp("mithril", "todomvc", todomvc_url("mithril")),
]

if __name__ == "__main__":
    run(all_apps)
