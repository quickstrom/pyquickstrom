import io
import subprocess
import json
import jsonlines
import logging
import time
from dataclasses import dataclass
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from quickstrom.printer import print_results
from quickstrom.protocol import *

Url = str


@dataclass
class SpecstromError(Exception):
    message: str
    exit_code: int
    log_file: str

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
                input_messages = message_reader(p.stdout)
                output_messages = message_writer(p.stdin)

                def receive():
                    msg = input_messages.read()
                    exit_code = p.poll()
                    if msg is None and exit_code is not None:
                        if exit_code == 0:
                            return None
                        else:
                            raise SpecstromError(
                                "Specstrom invocation failed", exit_code, ilog.name)
                    else:
                        self.log.debug("Received %s", msg)
                        return msg

                def send(msg):
                    if p.poll() is None:
                        self.log.debug("Sending %s", msg)
                        output_messages.write(msg)
                    else:
                        raise Exception("Done, can't send.")

                def get_element_css_values(element, schema):
                    css_values = {}
                    for name, schema in schema.items():
                        css_values[name] = element.value_of_css_property(name)
                    return css_values

                def get_element_state(driver, schema, element):
                    element_state = {}
                    for key, sub_schema in schema.items():
                        if key == 'ref':
                            element_state[key] = element.id
                        elif key == 'enabled':
                            element_state[key] = element.is_enabled()
                        elif key == 'visible':
                            element_state[key] = element.is_displayed()
                        elif key == 'active':
                            active = driver.switch_to.active_element
                            element_state[key] = element.id == active.id if active else False
                        elif key == 'value':
                            element_state[key] = element.get_property('value')
                        elif key == 'css':
                            element_state[key] = get_element_css_values(
                                element, sub_schema)
                        elif key == 'textContent':
                            element_state[key] = element.get_property(
                                'textContent')
                        elif key == 'checked':
                            element_state[key] = element.get_property(
                                'checked')
                        else:
                            raise Exception(
                                f"Unsupported element state: {key}")
                    return element_state

                def perform_action(driver, action):
                    if action.id == 'click':
                        id = action.args[0]
                        element = WebElement(driver, id)
                        element.click()
                    elif action.id == 'focus':
                        id = action.args[0]
                        element = WebElement(driver, id)
                        element.send_keys("")
                    elif action.id == 'keyPress':
                        char = action.args[0]
                        element = driver.switch_to.active_element
                        element.send_keys(char)
                    else:
                        raise Exception(f'Unsupported action: {action}')

                def query(driver, deps):
                    state = {}
                    for selector, schema in deps.items():
                        elements = driver.find_elements_by_css_selector(
                            selector)
                        element_states = []
                        for element in elements:
                            element_state = get_element_state(
                                driver, schema, element)
                            element_states.append(element_state)
                        state[selector] = element_states

                    return state

                def run_sessions():
                    while True:
                        msg = receive()
                        assert msg is not None
                        if isinstance(msg, Start):
                            self.log.info("Starting session")
                            chrome_options = Options()
                            chrome_options.add_argument("--headless")
                            driver = webdriver.Chrome(options=chrome_options)
                            driver.get(self.origin)
                            # horrible hack that should be removed once we have events!
                            #time.sleep(3)
                            state = query(driver, msg.dependencies)
                            event = {'id': 'loaded', 'isEvent': True,
                                     'args': [], 'timeout': None}
                            send({'tag': 'Event', 'contents': [event, state]})
                            await_session_commands(driver, msg.dependencies)
                        elif isinstance(msg, Done):
                            return msg.results

                def await_session_commands(driver: WebDriver, deps):
                    try:
                        actionCount = 0
                        driver.get_screenshot_as_file(f"/tmp/quickstrom-{actionCount}.png")
                        while True:
                            msg = receive()
                            if not msg:
                                raise Exception(
                                    "No more messages from Specstrom, expected RequestAction or End.")
                            elif isinstance(msg, RequestAction):
                                actionCount += 1
                                self.log.info(
                                    f"Performing action #{actionCount}")
                                perform_action(driver, msg.action)
                                state = query(driver, deps)
                                driver.get_screenshot_as_file(f"/tmp/quickstrom-{actionCount}.png")
                                send({'tag': 'Performed', 'contents': state})
                            elif isinstance(msg, End):
                                self.log.info("Ending session")
                                return
                            else:
                                raise Exception(f"Unexpected message: {msg}")
                    finally:
                        driver.close()

                try:
                    results = run_sessions()
                    print_results(results)
                except SpecstromError as err:
                    print(err)
                    print(
                        f"See interpreter log file for details: {err.log_file}")
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
