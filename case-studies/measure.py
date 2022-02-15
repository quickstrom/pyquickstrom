#!/usr/bin/env python3

from dataclasses import dataclass
import sys
from typing import List, TextIO
import click
import time

import shared


@dataclass
class Result():
    name: str
    duration: float
    result: shared.ResultName
    browser: str

    def to_csv_row(self) -> str:
        return f"{self.name},{self.duration},{self.result},{self.browser}\n"


def measure(apps: List[shared.TestApp], file: TextIO):
    with shared.todomvc_server() as server:
        try:
            browsers: List[shared.Browser] = [
            # "chrome",
                "firefox",
            ]
            for app in apps:

                for browser in browsers:
                    max_tries = 3
                    for _ in range(1, max_tries + 1):
                        start_time = time.time()
                        click.echo(shared.heading1(f"{app.name}"))
                        click.echo(f"Browser: {browser}")

                        try:
                            r = shared.check(
                                app=app,
                                stderr=sys.stdout,
                                headful=True,
                                browser=browser,
                            )
                            end_time = time.time()
                            result = Result(app.name,
                                            duration=(end_time - start_time),
                                            result=r,
                                            browser=browser)
                            file.write(result.to_csv_row())
                            file.flush()
                            click.echo(result)
                        except KeyboardInterrupt:
                            exit(1)
                        except Exception as e:
                            click.echo(f"Test failed with exception:\n{e}")
        finally:
            server.kill()


def todomvc_app(name: str,
                path: str = "index.html",
                expected: shared.ResultName = 'passed') -> shared.TestApp:
    base = "http://localhost:12345"
    url = f"{base}/examples/{name}/{path}"
    return shared.TestApp(name, "todomvc", url, expected)


all_apps = [
    todomvc_app("angular-dart", path="web/", expected='error'),
    todomvc_app("angular2_es2015", expected='failed'),
    todomvc_app("angular2", expected='failed'),
    todomvc_app("angularjs_require"),
    todomvc_app("angularjs", expected='failed'),
    todomvc_app("aurelia"),
    todomvc_app("backbone_marionette", expected='failed'),
    todomvc_app("backbone_require"),
    todomvc_app("backbone"),
    todomvc_app("binding-scala"),
    todomvc_app("canjs_require"),
    todomvc_app("canjs"),
    todomvc_app("closure"),
    todomvc_app("cujo", expected='error'),
    todomvc_app("dijon", expected='failed'),
    todomvc_app("dojo", expected='failed'),
    todomvc_app("duel", path="www/index.html", expected='failed'),
    todomvc_app("elm"),
    # todomvc_app("emberjs_require", expected='error'), # this should be excluded
    todomvc_app("emberjs"),
    todomvc_app("enyo_backbone"),
    todomvc_app("exoskeleton"),
    # todomvc_app("firebase-angular", expected='failed'), # excluded due to its async state updates
    todomvc_app("gwt", expected='error'),
    todomvc_app("jquery", expected='failed'),
    todomvc_app("js_of_ocaml"),
    todomvc_app("jsblocks"),
    todomvc_app("knockback"),
    todomvc_app("knockoutjs_require", expected='failed'),
    todomvc_app("knockoutjs"),
    todomvc_app("kotlin-react"),
    todomvc_app("lavaca_require", expected='failed'),
    todomvc_app("mithril", expected='failed'),
    todomvc_app("polymer", expected='failed'),
    todomvc_app("ractive"),
    todomvc_app("react-alt"),
    todomvc_app("react-backbone"),
    # todomvc_app("react-hooks", expected='error'), # this should be excluded
    todomvc_app("react"),
    todomvc_app("reagent", expected='failed'),
    todomvc_app("riotjs"),
    todomvc_app("scalajs-react"),
    todomvc_app("typescript-angular"),
    todomvc_app("typescript-backbone"),
    todomvc_app("typescript-react"),
    todomvc_app("vanilla-es6", expected='failed'),
    todomvc_app("vanillajs", expected='failed'),
    todomvc_app("vue"),
]

if __name__ == "__main__":
    output_file = sys.argv[1]
    apps_to_run = sys.argv[2:]
    selected_apps: List[shared.TestApp] = all_apps
    if len(apps_to_run) > 0:
        selected_apps = list(filter(lambda a: a.name in apps_to_run, all_apps))
        click.echo("Running selected apps only:")
        for a in selected_apps:
            click.echo(f" - {a.name}")
    else:
        click.echo("Running all apps")
    click.echo("")

    with open(output_file, "w+") as f:
        f.write(f"name,duration,result,browser\n")
        measure(selected_apps, file=f)
