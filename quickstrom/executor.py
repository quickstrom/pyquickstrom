import io
import subprocess
import json
import logging

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

#
# driver.set_network_conditions(
#     offline=False,
#     latency=500,
#     throughput=500*1024,
# )
#
# assert "Oskar" in driver.title

Url = str


class SpecstromError(Exception):
    pass


class Check():

    def __init__(self, module: str, origin: Url):
        self.log = logging.getLogger('quickstrom.executor')
        self.module = module
        self.origin = origin

    def execute(self):
        with open("interpreter.log", "w+") as log:
            with subprocess.Popen(["specstrom", "check", self.module], text=True, stdout=subprocess.PIPE, stderr=log, stdin=subprocess.PIPE, bufsize=0) as p:

                def receive():
                    x = p.poll()
                    if p.poll() is None:
                        line = p.stdout.readline().strip()
                        if line == '':
                            return None
                        else:
                            try:
                                msg = json.loads(line)
                                self.log.info("Received %s", msg)
                                return msg
                            except json.JSONDecodeError as err:
                                raise Exception(
                                    f"Can't decode line '{line}', {err}")
                    else:
                        return None

                def send(msg):
                    self.log.info("Sending %s", msg)
                    if p.poll() is None:
                        p.stdin.write(json.dumps(msg) + '\n')
                    else:
                        raise Exception("Done, can't send.")

                def get_element_state(schema, element):
                    element_state = {}
                    for key, sub_schema in schema.items():
                        if key == 'disabled':
                            element_state[key] = not element.is_enabled()
                        else:
                            raise Exception(
                                f"Unsupported element state: {key}")
                    return element_state

                def perform_action(driver, action, timeout):
                    if action['tag'] == 'Click':
                        id = action['contents']
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
                        self.log.info('%s: %s', selector, element_states)

                    return state
                    # return {'[name=foo]': [{'disabled': False}], '[name=bar]': [{'disabled': False}], 'button': [{'ref': 'btn', 'disabled': False}]}

                def run_sessions():
                    while True:
                        msg = receive()
                        if not msg:
                            raise SpecstromError(
                                f"Specstrom invocation failed with exit code {p.poll()}. See {log.name} for details.")
                        elif msg['tag'] == 'Start':
                            chrome_options = Options()
                            chrome_options.add_argument("--headless")
                            driver = webdriver.Chrome(options=chrome_options)
                            driver.get(self.origin)
                            deps = msg['dependencies']
                            state = query(driver, deps)
                            send({'tag': 'Event', 'contents': [
                                 {'tag': 'Loaded'}, state]})
                            await_session_commands(driver, deps)
                        elif msg['tag'] == 'Done':
                            return msg['results']

                def await_session_commands(driver, deps):
                    self.log.info("Dependencies: %s", deps)
                    try:
                        while True:
                            msg = receive()
                            if not msg:
                                raise Exception(
                                    "No more messages from Specstrom, expected RequestAction or End.")
                            elif msg['tag'] == 'RequestAction':
                                perform_action(
                                    driver, msg['action'][0], msg['action'][1])
                                state = query(driver, deps)
                                send({'tag': 'Performed', 'contents': state})
                            elif msg['tag'] == 'End':
                                return
                            else:
                                raise f"Unexpected message: {msg}"
                    finally:
                        driver.close()

                try:
                    results = run_sessions()
                    print("Results:")
                    for result in results:
                        print(
                            f" - {result['valid']['tag']} {result['valid']['contents']}")
                except SpecstromError as err:
                    print(err)
                    exit(1)
