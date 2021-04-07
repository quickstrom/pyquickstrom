import io
import subprocess
import json
import logging
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

Selector = str
Url = str
Schema = Dict[str, object] # mypy doesn't support recursive types :(

@dataclass
@dataclass_json
class Start():
    dependencies: Dict[Selector, Schema]

@dataclass
@dataclass_json
class End(): pass

@dataclass
class SpecstromError(Exception):
    message: str
    exit_code: int
    logs: List[str]

    def __str__(self): return f"{self.message}, exit code {self.exit_code}"


@dataclass
class Check():
    module: str
    origin: str
    include_paths: List[str]
    log: logging.Logger = logging.getLogger('quickstrom.executor')

    def execute(self):
        with open("interpreter.log", "w+") as ilog:
            with self.launch_specstrom(ilog) as p:
                def receive():
                    line = p.stdout.readline().strip()
                    if line == '' and p.poll():
                        return None
                    else:
                        try:
                            self.log.debug("Received JSON: %s", line)
                            return json.loads(line)
                        except json.JSONDecodeError as err:
                            raise Exception(
                                f"Can't decode line '{line}', {err}")

                def send(msg):
                    if p.poll() is None:
                        encoded = json.dumps(msg)
                        self.log.debug("Sending JSON: %s", encoded)
                        p.stdin.write(encoded + '\n')
                    else:
                        raise Exception("Done, can't send.")

                def get_element_state(schema, element):
                    element_state = {}
                    for key, sub_schema in schema.items():
                        if key == 'ref':
                            element_state[key] = element.id
                        elif key == 'enabled':
                            element_state[key] = element.is_enabled()
                        else:
                            raise Exception(
                                f"Unsupported element state: {key}")
                    return element_state

                def perform_action(driver, action):
                    if action['id'] == 'click':
                        id = action['args'][0]
                        element = WebElement(driver, id)
                        element.click()
                    else:
                        raise Exception(f'Unsupported action: {action}')

                def query(driver, deps):
                    state = {}
                    for selector, schema in deps.items():
                        elements = driver.find_elements_by_css_selector(
                            selector)
                        element_states = []
                        for element in elements:
                            element_state = get_element_state(schema, element)
                            element_states.append(element_state)
                        state[selector] = element_states

                    return state

                def run_sessions():
                    while True:
                        msg = receive()
                        if msg is None:
                            logs = ilog.readlines()
                            raise SpecstromError(
                                "Specstrom invocation failed", p.poll(), logs)
                        elif msg['tag'] == 'Start':
                            self.log.info("Starting session")
                            chrome_options = Options()
                            chrome_options.add_argument("--headless")
                            driver = webdriver.Chrome(options=chrome_options)
                            driver.get(self.origin)
                            deps = msg['dependencies']
                            state = query(driver, deps)
                            event = {'id': 'loaded', 'isEvent': True, 'args': [], 'timeout': None }
                            send({'tag': 'Event', 'contents': [event, state]})
                            await_session_commands(driver, deps)
                        elif msg['tag'] == 'Done':
                            return msg['results']

                def await_session_commands(driver: WebDriver, deps):
                    try:
                        while True:
                            msg = receive()
                            if not msg:
                                raise Exception(
                                    "No more messages from Specstrom, expected RequestAction or End.")
                            elif msg['tag'] == 'RequestAction':
                                perform_action(driver, msg['action'])
                                state = query(driver, deps)
                                send({'tag': 'Performed', 'contents': state})
                            elif msg['tag'] == 'End':
                                self.log.info("Ending session")
                                return
                            else:
                                raise Exception(f"Unexpected message: {msg}")
                    finally:
                        driver.close()

                try:
                    results = run_sessions()
                    for result in results:
                        print(f"Result: {result['valid']['tag']} {result['valid']['contents']}")
                        print("Trace:")
                        trace = result['trace']
                        for i, element in zip(range(1, len(trace) + 1), trace):
                            if element['tag'] == 'TraceAction':
                                for action in element['contents']:
                                    label = "Event" if action['isEvent'] else "Action"
                                    print(f"  {i}. {label}: {action['id']}({', '.join(action['args'])})")
                            else:
                                state = element['contents']
                                print(f"  {i}. State")
                                for selector, elements in state.items():
                                    print(f"    `{selector}`")
                                    for element in elements:
                                        print(f"      - {element}")
                except SpecstromError as err:
                    print(err)
                    print("\n" + "\n".join(err.logs))
                    exit(1)

    def launch_specstrom(self, ilog):
        includes = list(map(lambda i: "-I" + i, self.include_paths))
        cmd = ["specstrom", "check", self.module] + includes + ["+RTS", "-p"]
        self.log.debug("Invoking Specstrom with: %s", " ".join(cmd))
        return subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=ilog,
            stdin=subprocess.PIPE,
            bufsize=0)
