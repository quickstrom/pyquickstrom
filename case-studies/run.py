#!/usr/bin/env python3

import sys
import click
import os
from typing import List
from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import shutil
import pathlib
import subprocess


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


def todomvc_server():
    todomvc_dir = os.getenv("TODOMVC_DIR")
    if todomvc_dir is None:
        raise Exception("Missing TODOMVC_DIR environment variable")
    return subprocess.Popen(["python3", "-m", "http.server", "--directory", todomvc_dir, "12345"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(apps: List[TestApp]):
    with todomvc_server() as server:
        non_passed = []
        try:
            shutil.rmtree("results", ignore_errors=True)
            os.makedirs("results")
            browsers: List[str] = [
                "chrome",
                # , "firefox"
            ]
            include_paths = [str(p.absolute()) for p in [case_studies_dir]]
            for app in apps:
                origin=urljoin("file://", app.origin)

                for browser in browsers:
                    result_dir = str(pathlib.Path(f"results/{app.name}.{app.module}.{browser}").absolute())
                    os.makedirs(result_dir)
                    html_report_dir = f"{result_dir}/html-report"
                    interpreter_log_file = f"{result_dir}/interpreter.log"
                    shutil.rmtree(html_report_dir, ignore_errors=True)

                    with open(f"{result_dir}/result.log", "w") as results_file:
                        click.echo(heading1(f"{app.name}"))
                        click.echo(f"Browser: {browser}")
                        click.echo("Text report: " + results_file.name)
                        click.echo(f"Interpreter log: {interpreter_log_file}")
                        click.echo(f"HTML report: {html_report_dir}/index.html")

                        try:
                            include_flags = [arg for path in include_paths for arg in ["-I", path] ]
                            args = ["quickstrom"] + include_flags + ["check",
                                                                     app.module,
                                                                     origin,
                                                                     "--reporter=console",
                                                                     "--capture-screenshots",
                                                                     "--reporter=html",
                                                                     "--html-report-directory", html_report_dir,
                                                                     "--interpreter-log-file", interpreter_log_file,
                                                                     ]
                            click.echo(f"Command: {' '.join(args)}")
                            check = subprocess.Popen(args, stdout=results_file, stderr=subprocess.PIPE)
                            r = check.wait()

                            if r == 0:
                                click.echo(success("Passed!"))
                            elif r == 1:
                                click.echo(failure("Error!"))
                                non_passed.append(app.name)
                            elif r == 2:
                                click.echo(failure("Specstrom error!"))
                                non_passed.append(app.name)
                            elif r == 3:
                                click.echo(failure("Failed!"))
                                non_passed.append(app.name)
                            else:
                                click.echo(failure(f"Unknown exit code: {r}"))
                                non_passed.append(app.name)
                        except KeyboardInterrupt:
                            exit(1)
                        except Exception as e:
                            click.echo(
                                f"Test failed with exception:\n{e}", file=results_file)
                            click.echo(
                                failure("result: failed with exception"))

                        click.echo("")
        finally:
            if non_passed is not []:
                click.echo(f"Rerun non-passed apps with: {sys.argv[0]} {' '.join(non_passed)}")
            server.kill()


def todomvc_app(name: str) -> TestApp:
    base = "http://localhost:12345"
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
    apps_to_run = sys.argv[1:]
    selected_apps: List[TestApp] = all_apps
    if len(apps_to_run) > 0:
        click.echo("Running selected apps only")
        selected_apps = list(filter(lambda a: a.name in apps_to_run, all_apps))
    else:
        click.echo("Running all apps")

    run(selected_apps)
