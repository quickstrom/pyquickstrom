from dataclasses import dataclass
from quickstrom.protocol import JsonLike
from quickstrom.reporter import Reporter
import sys
from typing import Any, Callable, IO, Text
from quickstrom.result import *
import quickstrom.printer as printer
from deepdiff import DeepDiff
import click


def element_heading(s: str):
    return click.style(s, bold=True, underline=True)


def selector(s: str):
    return click.style(s, bold=True)


def added(s: str):
    return click.style(s, fg='green')


def removed(s: str):
    return click.style(s, fg='red')


def modified(s: str):
    return click.style(s, fg='blue')


def unmodified(s: str):
    return click.style(s, dim=True)


def indent(s: str, level: int) -> str:
    return f"{' ' * level * 2}{s}"


def formatted(diff: Diff[Any]) -> str:
    if isinstance(diff, Added):
        return added(repr(diff.value))
    elif isinstance(diff, Removed):
        return removed(repr(diff.value))
    elif isinstance(diff, Modified):
        return modified(repr(diff.old) + " -> " + repr(diff.new))
    elif isinstance(diff, Unmodified):
        return unmodified(repr(diff.value))


def print_state_diff(state: State[DiffedValue], indent_level: int,
                     file: Optional[IO[Text]]):
    for sel, elements in state.queries.items():
        click.echo(indent(selector(f"`{sel}`"), indent_level), file=file)
        for element in elements:

            def element_prefix() -> str:
                if isinstance(element, Added):
                    return added("+ Element")
                elif isinstance(element, Removed):
                    return removed("- Element")
                elif isinstance(element, Modified):
                    return modified("~ Element")
                else:
                    return "* Element"

            click.echo(indent(f"{element_prefix()}", indent_level + 1),
                       file=file)

            def without_internal_props(d: dict) -> dict:
                return {
                    key: value
                    for key, value in d.items()
                    if key not in ['ref', 'position']
                }

            def print_value_diff(diff: DiffedValue, indent_level: int):
                if isinstance(diff, dict):
                    for key, value in without_internal_props(diff).items():
                        click.echo(indent(f"{key}:", indent_level), file=file)
                        print_value_diff(value, indent_level=indent_level + 1)
                elif isinstance(diff, list):
                    for value in diff:
                        click.echo(indent("*", indent_level), file=file)
                        print_value_diff(value, indent_level=indent_level + 1)
                else:
                    click.echo(indent(formatted(diff), indent_level),
                               file=file)

            print_value_diff(element, indent_level=indent_level + 2)


@dataclass
class ConsoleReporter(Reporter):
    report_on_success: bool
    file: Optional[IO[Text]] = sys.stdout

    def report(self, result: Result):
        if isinstance(result, Failed):
            diffed_test = diff_test(result.failed_test)

            click.echo("Trace:", file=self.file)
            i = 1
            for transition in diffed_test.transitions:
                for action in transition.actions:
                    label = "Event" if action.isEvent else "Action"
                    heading = f"{i}. {label}:"
                    click.echo(indent(
                        element_heading(
                            f"{heading} {printer.pretty_print_action(action)}"
                        ), 1),
                               file=self.file)
                    i += 1

                click.echo(indent(element_heading(f"{i}. State"), 1),
                           file=self.file)
                state: State = transition.to_state
                print_state_diff(state, indent_level=2, file=self.file)
