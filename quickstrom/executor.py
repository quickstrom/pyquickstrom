import io
import subprocess
import logging
import time
from shutil import which
from dataclasses import dataclass
from PIL import Image
from typing import List, Union, Literal, Any
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import selenium.webdriver.chrome.options as chrome_options
import selenium.webdriver.firefox.options as firefox_options

from quickstrom.protocol import *
from quickstrom.hash import dict_hash
import quickstrom.result as result
import quickstrom.printer as printer
import os

Url = str


@dataclass
class SpecstromError(Exception):
    message: str
    exit_code: int
    log_file: str

    def __str__(self):
        return f"{self.message}, exit code {self.exit_code}"


Browser = Union[Literal['chrome'], Literal['firefox']]


@dataclass
class Check():
    module: str
    origin: str
    browser: Browser
    include_paths: List[str]
    capture_screenshots: bool
    log: logging.Logger = logging.getLogger('quickstrom.executor')

    def execute(self) -> List[result.Result]:
        with open("interpreter.log", "w+") as ilog:
            with self.launch_specstrom(ilog) as p:
                assert p.stdout is not None
                assert p.stdin is not None
                input_messages = message_reader(p.stdout)
                output_messages = message_writer(p.stdin)
                screenshots: Dict[str, result.Screenshot[bytes]] = {}

                def receive():
                    msg = input_messages.read()
                    exit_code = p.poll()
                    if msg is None and exit_code is not None:
                        if exit_code == 0:
                            return None
                        else:
                            raise SpecstromError("Specstrom invocation failed",
                                                 exit_code, ilog.name)
                    else:
                        self.log.debug("Received %s", msg)
                        return msg

                def send(msg):
                    if p.poll() is None:
                        self.log.debug("Sending %s", msg)
                        output_messages.write(msg)
                    else:
                        raise Exception("Done, can't send.")

                def perform_action(driver, action):
                    if action.id == 'click':
                        id = action.args[0]
                        element = WebElement(driver, id)
                        element.click()
                    elif action.id == 'doubleClick':
                        id = action.args[0]
                        element = WebElement(driver, id)
                        ActionChains(driver).double_click(element).perform()
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

                def elements_to_ids(obj):
                    if isinstance(obj, dict):
                        return {
                            key: elements_to_ids(value)
                            for (key, value) in obj.items()
                        }
                    elif isinstance(obj, list):
                        return [elements_to_ids(value) for value in obj]
                    elif isinstance(obj, WebElement):
                        return obj.id
                    else:
                        return obj

                def query_state(driver, deps) -> Any:
                    key = 'QUICKSTROM_CLIENT_SIDE_DIRECTORY'
                    client_side_dir = os.getenv(key)
                    if not client_side_dir:
                        raise Exception(
                            f'Environment variable {key} must be set')
                    file = open(f'{client_side_dir}/queryState.js')
                    script = file.read()
                    return elements_to_ids(
                        driver.execute_async_script(script, deps))

                def screenshot(driver: WebDriver, hash: str):
                    if self.capture_screenshots:
                        bs = driver.get_screenshot_as_png()
                        image = Image.open(io.BytesIO(bs))
                        (width, height) = image.size
                        window_size = driver.get_window_size()
                        scale = round(width / window_size['width'])
                        if scale != round(width / window_size['height']):
                            self.log.warn("Width and height scales do not match for screenshot")
                        screenshots[hash] = result.Screenshot(image=bs,
                                                              width=width,
                                                              height=height,
                                                              scale=scale)

                def attach_screenshots(r: result.Result) -> result.Result:
                    def on_state(state):
                        return result.State(screenshot=screenshots.get(
                            state.hash, None),
                                            queries=state.queries,
                                            hash=state.hash)

                    return result.map_states(r, on_state)

                def run_sessions() -> List[result.Result]:
                    while True:
                        msg = receive()
                        assert msg is not None
                        if isinstance(msg, Start):
                            self.log.info("Starting session")
                            driver = self.new_driver()
                            driver.set_window_size(1200, 600)
                            driver.get(self.origin)
                            # horrible hack that should be removed once we have events!
                            time.sleep(3)
                            self.log.debug("Deps: %s",
                                           json.dumps(msg.dependencies))
                            state = query_state(driver, msg.dependencies)
                            screenshot(driver, dict_hash(state))
                            event = Action(id='loaded',
                                           isEvent=True,
                                           args=[],
                                           timeout=None)
                            send(Event(event=event, state=state))
                            await_session_commands(driver, msg.dependencies)
                        elif isinstance(msg, Done):
                            return [
                                attach_screenshots(
                                    result.from_protocol_result(r))
                                for r in msg.results
                            ]

                def await_session_commands(driver: WebDriver, deps):

                    try:
                        state_version = 1
                        while True:
                            msg = receive()
                            if not msg:
                                raise Exception(
                                    "No more messages from Specstrom, expected RequestAction or End."
                                )
                            elif isinstance(msg, RequestAction):
                                if msg.version == state_version:
                                    self.log.info(
                                        f"Performing action in state {state_version}: {printer.pretty_print_action(msg.action)}"
                                    )
                                    perform_action(driver, msg.action)
                                    state = query_state(driver, deps)
                                    screenshot(driver, dict_hash(state))
                                    state_version += 1
                                    send(Performed(state=state))
                                else:
                                    send(Stale())
                            elif isinstance(msg, End):
                                self.log.info("Ending session")
                                return
                            else:
                                raise Exception(f"Unexpected message: {msg}")
                    finally:
                        driver.close()

                return run_sessions()

    def launch_specstrom(self, ilog):
        includes = list(map(lambda i: "-I" + i, self.include_paths))
        cmd = ["specstrom", "check", self.module
               ] + includes    # + ["+RTS", "-p"]
        self.log.debug("Invoking Specstrom with: %s", " ".join(cmd))
        return subprocess.Popen(cmd,
                                text=True,
                                stdout=subprocess.PIPE,
                                stderr=ilog,
                                stdin=subprocess.PIPE,
                                bufsize=0)

    def new_driver(self):
        if self.browser == 'chrome':
            options = chrome_options.Options()
            options.headless = True
            browser_path = which("chrome") or which("chromium")
            options.binary_location = browser_path    # type: ignore
            chromedriver_path = which('chromedriver')
            if not chromedriver_path:
                raise Exception("chromedriver not found in PATH")
            return webdriver.Chrome(options=options,
                                    executable_path=chromedriver_path)
        elif self.browser == 'firefox':
            options = firefox_options.Options()
            options.headless = True
            options.binary = which("firefox")    # type: ignore
            geckodriver_path = which('geckodriver')
            if not geckodriver_path:
                raise Exception("geckodriver not found in PATH")
            return webdriver.Firefox(options=options,
                                     executable_path=geckodriver_path)
        else:
            raise Exception(f"Unsupported browser: {self.browser}")
