#!/usr/bin/env python3

import sys
import click
import os
from typing import List, Literal, Optional, Union
from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import shutil
import pathlib
import subprocess
import time

case_studies_dir = pathlib.Path(__file__).parent.resolve()

ResultName = Union[
    Literal['passed'],
    Literal['failed'],
    Literal['error'],
    Literal['specstrom-error'],
    Literal['unknown'],
    ]

@dataclass
class TestApp():
    name: str
    module: str
    origin: str
    expected: ResultName


def heading1(s): return click.style(s, bold=True, underline=True)


def heading2(s): return click.style(s, bold=True)


def success(s): return click.style(s, fg='green')


def failure(s): return click.style(s, fg='red')


def warning(s): return click.style(s, fg='yellow')


case_studies_dir = pathlib.Path(__file__).parent.resolve()


def result_from_exit_code(n: int) -> ResultName:
    if n == 0:
        return 'passed'
    elif n == 1:
        return 'error'
    elif n == 2:
        return 'specstrom-error'
    elif n == 3:
        return 'failed'
    else:
        return 'unknown'

def todomvc_server():
    todomvc_dir = os.getenv("TODOMVC_DIR")
    if todomvc_dir is None:
        raise Exception("Missing TODOMVC_DIR environment variable")
    return subprocess.Popen(["python3", "-m", "http.server", "--directory", todomvc_dir, "12345"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(apps: List[TestApp]):
    with todomvc_server() as server:
        unexpected_result_tests = []
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
                    max_tries = 5
                    for try_n in range(1, max_tries + 1):
                        result_dir = str(pathlib.Path(f"results/{app.name}.{browser}.{try_n}").absolute())
                        os.makedirs(result_dir)
                        html_report_dir = f"{result_dir}/html-report"
                        interpreter_log_file = f"{result_dir}/interpreter.log"
                        duration_file = f"{result_dir}/duration"
                        start_time = time.time()
                        shutil.rmtree(html_report_dir, ignore_errors=True)

                        with open(f"{result_dir}/stdout.log", "w") as stdout_file:
                            with open(f"{result_dir}/stderr.log", "w") as stderr_file:
                                click.echo(heading1(f"{app.name}"))
                                click.echo(f"Browser: {browser}")
                                click.echo("Stdout: " + stdout_file.name)
                                click.echo("Stderr: " + stderr_file.name)
                                click.echo(f"Interpreter log: {interpreter_log_file}")
                                click.echo(f"HTML report: {html_report_dir}/index.html")

                                include_flags = [arg for path in include_paths for arg in ["-I", path] ]
                                args = ["quickstrom"] + include_flags + ["--log-level", "debug",
                                                                        "check",
                                                                        app.module,
                                                                        origin,
                                                                        "--reporter=console",
                                                                        "--capture-screenshots",
                                                                        "--reporter=html",
                                                                        "--html-report-directory", html_report_dir,
                                                                        "--interpreter-log-file", interpreter_log_file,
                                                                        ]
                                click.echo(f"Command: {' '.join(args)}")
                                click.echo("")

                                click.echo(f"Try {try_n}...")
                                try:
                                    check = subprocess.Popen(args, stdout=stdout_file, stderr=stderr_file)
                                    r = result_from_exit_code(check.wait())

                                    if r != app.expected:
                                        if try_n == max_tries or app.expected == 'passed':
                                            unexpected_result_tests.append(app.name)
                                        click.echo(failure(f"Expected '{app.expected}' but result was '{r}'!"))
                                        if app.expected == 'passed':
                                            break
                                    else:
                                        if r == 'passed':
                                            click.echo(success("Passed!"))
                                        else:
                                            click.echo(warning(f"Got expected '{r}'!"))
                                        break
                                except KeyboardInterrupt:
                                    exit(1)
                                except Exception as e:
                                    click.echo(
                                        f"Test failed with exception:\n{e}", file=stdout_file)
                                    click.echo(
                                        failure("result: failed with exception"))
                                finally:
                                    end_time = time.time()
                                    with open(duration_file, 'w+') as f:
                                        f.write(str(end_time - start_time))

                                click.echo("")
        finally:
            server.kill()
            if len(unexpected_result_tests) > 0:
                click.echo(f"There were unexpected results. Rerun only those apps with:\n\n{sys.argv[0]} {' '.join(unexpected_result_tests)}")
                exit(1)


def todomvc_app(name: str, path: str = "index.html", expected: ResultName = 'passed') -> TestApp:
    base = "http://localhost:12345"
    url = f"{base}/examples/{name}/{path}"
    return TestApp(name, "todomvc", url, expected)


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

    # Non-todomvc
    TestApp("timer", "timer", str(case_studies_dir / "timer.html"), expected='passed')
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
