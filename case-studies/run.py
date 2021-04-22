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
    browsers: List[executor.Browser] = [
        "chrome",
        # , "firefox"
    ]
    include_paths = list(map(lambda p: str(p.absolute()),
                         [case_studies_dir, ulib_dir]))
    for app in apps:
        checks = [executor.Check(app.module, origin=urljoin("file://", app.origin), browser=browser,
                                 include_paths=include_paths, capture_screenshots=False) for browser in browsers]
        for check in checks:
            with open(f"results/{app.name}.{app.module}.{check.browser}.log", "w") as results_file:
                click.echo(heading1(f"{app.name}"))
                for key, value in asdict(check).items():
                    if key != 'log':
                        click.echo(f"{key}: {value}")
                click.echo("details: " + results_file.name)

                try:
                    results = check.execute()
                    printer.print_results(results, file=results_file)

                    for result in results:
                        color = success if result.valid.value else failure
                        click.echo(
                            "result: " + color(f"{result.valid.certainty} {result.valid.value}"))
                except Exception as e:
                    click.echo(
                        f"Test failed with exception:\n{e}", file=results_file)
                    click.echo(failure("result: failed with exception"))

                click.echo("")


def todomvc_app(name: str) -> TestApp:
    base = os.getenv("TODOMVC_DIR") or "https://todomvc.com"
    url = f"{base}/examples/{name}/index.html"
    return TestApp(name, "todomvc", url)


all_apps = [
    todomvc_app("angular2"),
    todomvc_app("angularjs_require"),
    todomvc_app("backbone_require"),
    todomvc_app("closure"),
    todomvc_app("duel"),
    todomvc_app("enyo_backbone"),
    todomvc_app("jquery"),
    todomvc_app("knockoutjs"),
    todomvc_app("mithril"),
    todomvc_app("react-alt"),
    todomvc_app("riotjs"),
    todomvc_app("typescript-react"),
    todomvc_app("angular2_es2015"),
    todomvc_app("aurelia"),
    todomvc_app("binding-scala"),
    todomvc_app("cujo"),
    todomvc_app("elm"),
    todomvc_app("exoskeleton"),
    todomvc_app("jsblocks"),
    todomvc_app("knockoutjs_require"),
    todomvc_app("polymer"),
    todomvc_app("react-backbone"),
    todomvc_app("scalajs-react"),
    todomvc_app("vanilla-es6"),
    todomvc_app("angular-dart"),
    todomvc_app("backbone"),
    todomvc_app("canjs"),
    todomvc_app("dijon"),
    todomvc_app("emberjs"),
    todomvc_app("firebase-angular"),
    todomvc_app("js_of_ocaml"),
    todomvc_app("kotlin-react"),
    todomvc_app("ractive"),
    todomvc_app("react-hooks"),
    todomvc_app("typescript-angular"),
    todomvc_app("vanillajs"),
    todomvc_app("angularjs"),
    todomvc_app("backbone_marionette"),
    todomvc_app("canjs_require"),
    todomvc_app("dojo"),
    todomvc_app("emberjs_require"),
    todomvc_app("gwt"),
    todomvc_app("knockback"),
    todomvc_app("lavaca_require"),
    todomvc_app("react"),
    todomvc_app("reagent"),
    todomvc_app("typescript-backbone"),
    todomvc_app("vue"),
]

if __name__ == "__main__":
    run(all_apps)
