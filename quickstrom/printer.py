from typing import List
from quickstrom.protocol import *

def print_results(results: List[Result]):
    for result in results:
        print("Trace:")
        for i, element in zip(range(1, len(result.trace) + 1), result.trace):
            if isinstance(element, TraceActions):
                for action in element.actions:
                    label = "Event" if action.isEvent else "Action"
                    print(f"  {i}. {label}: {action.id}({', '.join([repr(arg) for arg in action.args])})")
            elif isinstance(element, TraceState):
                print(f"  {i}. State")
                state: State = element.state
                for selector, elements in state.items():
                    print(f"    `{selector}`")
                    for state_element in elements:
                        print(f"      - {state_element}")
        print(
            f"Result: {result.valid.certainty} {result.valid.value}")
