from typing import List, cast
from quickstrom.protocol import *
from deepdiff import DeepDiff, extract
from pprint import pprint
import click

def print_results(results: List[Result]):
    for result in results:
        print("Trace:")
        last_state = None
        for i, element in zip(range(1, len(result.trace) + 1), result.trace):
            if isinstance(element, TraceActions):
                for action in element.actions:
                    label = "Event" if action.isEvent else "Action"
                    heading = element_heading(f"{i}. {label}:")
                    print(indent(f"{heading} {action.id}({', '.join([repr(arg) for arg in action.args])})", 1))
            elif isinstance(element, TraceState):
                print(indent(element_heading(f"{i}. State"), 1))
                state: State = element.state
                diff = DeepDiff(last_state, state)
                print_state_diff(diff, state, indent_level=2)
                last_state = state
        print(
            f"Result: {result.valid.certainty} {result.valid.value}")

def print_state_diff(state_diff: DeepDiff, state: State, indent_level: int): 
    colored = {}
    for key, diffs in state_diff.items():
        for path, diff in diffs.items():
            if key == 'values_changed':
                colored[path] = removed(repr(diff['old_value'])) + " -> " + added(repr(diff['new_value']))
            if key == 'iterable_item_added':
                colored[path] = added(f"{repr(diff)}")
            if key == 'iterable_item_removed':
                colored[path] = removed(f"{repr(diff)}")

    def color_value(diff_key, value) -> str:
        return colored[diff_key] if diff_key in colored else repr(value)

    for sel, elements in state.items():
        print(indent(selector(f"`{sel}`"), indent_level))
        for i, state_element in enumerate(elements):
            element_diff_key = f"root['{sel}'][{i}]"
            element_suffix = " (" + color_value(f"{element_diff_key}['ref']", state_element['ref']) + ")" if 'ref' in state_element else ""
            click.echo(indent(f"- Element{element_suffix}", indent_level+1))
            for key, value in [(key, value) for key, value in state_element.items() if key != 'ref']:
                diff_key = f"{element_diff_key}['{key}']"
                click.echo(indent(f"- {key}: {color_value(diff_key, value)}", indent_level+2))
                
def element_heading(s): return click.style(s, bold=True)

def selector(s): return click.style(s, fg='cyan')

def added(s): return click.style(s, fg='green')

def removed(s): return click.style(s, fg='red')

def modified(s): return click.style(s, fg='yellow')

def indent(s: str, level: int) -> str:
    return f"{' ' * level * 2}{s}"