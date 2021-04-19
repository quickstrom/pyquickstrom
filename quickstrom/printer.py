import sys
from typing import List, cast, IO, Text
from quickstrom.protocol import *
from deepdiff import DeepDiff, extract
import click

def print_results(results: List[Result], file: Optional[IO[Text]] = sys.stdout, print_all_traces: bool = False):
    for result in results:
        click.echo("Trace:", file=file)
        last_state = None
        if not result.valid.value or print_all_traces:
            for i, element in zip(range(1, len(result.trace) + 1), result.trace):
                if isinstance(element, TraceActions):
                    for action in element.actions:
                        label = "Event" if action.isEvent else "Action"
                        heading = f"{i}. {label}:"
                        click.echo(indent(element_heading(f"{heading} {action.id}({', '.join([repr(arg) for arg in action.args])})"), 1), file=file)
                elif isinstance(element, TraceState):
                    click.echo(indent(element_heading(f"{i}. State"), 1), file=file)
                    state: State = element.state
                    diff = DeepDiff(last_state, state)
                    print_state_diff(diff, state, indent_level=2, file=file)
                    last_state = state
        click.echo(f"Result: {result.valid.certainty} {result.valid.value}", file=file)

@dataclass
class Diff():
    def formatted(self): str

@dataclass
class Added(Diff):
    value: object

    def formatted(self):
        return added(repr(self.value))

@dataclass
class Removed(Diff):
    value: object

    def formatted(self):
        return removed(repr(self.value))

@dataclass
class Modified(Diff):
    old: object
    new: object

    def formatted(self):
        return modified(repr(self.old) + " -> " + repr(self.new))

@dataclass
class Unmodified(Diff):
    value: object

    def formatted(self):
        return unmodified(repr(self.value))

def print_state_diff(state_diff: DeepDiff, state: State, indent_level: int, file: Optional[IO[Text]]): 
    diffs_by_path: 'Dict[str, Diff]' = {}
    for key, diffs in state_diff.items():
        for path, diff in diffs.items():
            if key == 'values_changed':
                diffs_by_path[path] = Modified(diff['old_value'], diff['new_value'])
            if key == 'iterable_item_added':
                diffs_by_path[path] = Added(diff)
            if key == 'iterable_item_removed':
                diffs_by_path[path] = Removed(diff)

    def value_diff(diff_path: str, value: object) -> Diff:
        return diffs_by_path[diff_path] if diff_path in diffs_by_path else Unmodified(value)

    for sel, elements in state.items():
        click.echo(indent(selector(f"`{sel}`"), indent_level), file=file)
        for i, state_element in enumerate(elements):
            element_diff_key = f"root['{sel}'][{i}]"

            def element_prefix() -> str:
                element_diff = value_diff(element_diff_key, state_element)
                if isinstance(element_diff, Added):
                    return added("+ Element")
                elif isinstance(element_diff, Removed):
                    return removed("- Element")
                elif isinstance(element_diff, Modified):
                    return modified("~ Element")
                else:
                    return "* Element"

            def element_suffix() -> str:
                if 'ref' in state_element: 
                    return " (" + value_diff(element_diff_key + "['ref']", state_element['ref']).formatted() + ")" 
                else: 
                    return ""

            click.echo(indent(f"{element_prefix()}{element_suffix()}", indent_level+1), file=file)
            for key, value in [(key, value) for key, value in state_element.items() if key != 'ref']:
                diff = value_diff(f"{element_diff_key}['{key}']", value)
                click.echo(indent(f"* {key}: {diff.formatted()}", indent_level+2), file=file)
                
def element_heading(s): return click.style(s, bold=True, underline=True)

def selector(s): return click.style(s, bold=True)

def added(s): return click.style(s, fg='green')

def removed(s): return click.style(s, fg='red')

def modified(s): return click.style(s, fg='blue')

def unmodified(s): return click.style(s, dim=True)

def indent(s: str, level: int) -> str:
    return f"{' ' * level * 2}{s}"