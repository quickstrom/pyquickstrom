import dataclasses
import io
import subprocess
import logging
import threading
import time
from shutil import which
from dataclasses import dataclass
import png
from typing import List, Union, Literal, Any, AnyStr
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

@dataclass
class ClientSideEvents():
    events: List[Action]
    state: State


@dataclass
class Scripts():
    query_state: Callable[[WebDriver, Dict[Selector, Schema]], State]
    install_event_listener: Callable[[WebDriver, Dict[Selector, Schema]], None]
    await_events: Callable[[WebDriver, int], Union[ClientSideEvents, None]]


Browser = Union[Literal['chrome'], Literal['firefox']]


@dataclass
class Cookie():
    domain: str
    name: str
    value: str


@dataclass
class Check():
    module: str
    origin: str
    browser: Browser
    include_paths: List[str]
    capture_screenshots: bool
    cookies: List[Cookie]
    interpreter_log_file: IO
    log: logging.Logger = logging.getLogger('quickstrom.executor')

    def execute(self) -> List[result.PlainResult]:
        scripts = self.load_scripts()

        with self.launch_specstrom(self.interpreter_log_file) as p:
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
                                                exit_code, self.interpreter_log_file.name)
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
                    ActionChains(driver).move_to_element(element).click(element).perform()
                elif action.id == 'doubleClick':
                    id = action.args[0]
                    element = WebElement(driver, id)
                    ActionChains(driver).move_to_element(element).double_click(element).perform()
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

            def screenshot(driver: WebDriver, hash: str):
                if self.capture_screenshots:
                    bs: bytes = driver.get_screenshot_as_png()    # type: ignore
                    (width, height, _, _) = png.Reader(io.BytesIO(bs)).read()
                    window_size = driver.get_window_size()
                    scale = round(width / window_size['width'])
                    if scale != round(height / window_size['height']):
                        self.log.warn(
                            "Width and height scales do not match for screenshot"
                        )
                    screenshots[hash] = result.Screenshot(image=bs,
                                                            width=width,
                                                            height=height,
                                                            scale=scale)

            def attach_screenshots(
                    r: result.PlainResult) -> result.PlainResult:
                def on_state(state):
                    return result.State(screenshot=screenshots.get(
                        state.hash, None),
                                        queries=state.queries,
                                        hash=state.hash)

                return result.map_states(r, on_state)

            def observe_change(driver, deps, state_version, timeout: int):
                self.log.debug(f"Awaiting change with timeout {timeout}")
                change = scripts.await_events(driver, timeout)
                self.log.debug(f"Change: {change}")

                if change is None:
                    self.log.info(f"Timed out!")
                    state = scripts.query_state(driver, deps)
                    screenshot(driver, dict_hash(state))
                    state_version.increment()
                    send(Timeout(state=state))
                else:
                    screenshot(driver, dict_hash(change.state))
                    state_version.increment()
                    send(Events(change.events, change.state))

            def run_sessions() -> List[result.PlainResult]:
                while True:
                    msg = receive()
                    assert msg is not None
                    if isinstance(msg, Start):
                        self.log.info("Starting session")
                        driver = self.new_driver()
                        driver.set_window_size(1200, 1200)

                        # First we need to visit the page in order to set cookies.
                        driver.get(self.origin)
                        for cookie in self.cookies:
                            self.log.debug(f"Setting {cookie}")
                            driver.add_cookie(dataclasses.asdict(cookie))
                        # Now that cookies are set, we have to visit the origin again.
                        driver.get(self.origin)

                        state_version = Counter(initial_value=0)

                        scripts.install_event_listener(driver, msg.dependencies)
                        observe_change(driver, msg.dependencies, state_version, 10000)

                        await_session_commands(driver, msg.dependencies, state_version)
                    elif isinstance(msg, Done):
                        return [
                            attach_screenshots(
                                result.from_protocol_result(r))
                            for r in msg.results
                        ]

            def await_session_commands(driver: WebDriver, deps, state_version):
                try:
                    while True:
                        msg = receive()

                        if not msg:
                            raise Exception(
                                "No more messages from Specstrom, expected RequestAction or End."
                            )
                        elif isinstance(msg, RequestAction):
                            if msg.version == state_version.value:
                                self.log.info(
                                    f"Performing action in state {state_version.value}: {printer.pretty_print_action(msg.action)}"
                                )

                                perform_action(driver, msg.action)

                                if msg.action.timeout is not None:
                                    self.log.debug("Installing change observer")
                                    scripts.install_event_listener(driver, deps)

                                state = scripts.query_state(driver, deps)
                                screenshot(driver, dict_hash(state))
                                state_version.increment()
                                send(Performed(state=state))

                                if msg.action.timeout is not None:
                                    observe_change(driver, deps, state_version, msg.action.timeout)
                            else:
                                self.log.warn(f"Got stale message ({msg}) in state {state_version.value}")
                                send(Stale())
                        elif isinstance(msg, AwaitEvents):
                            if msg.version == state_version.value:
                                scripts.install_event_listener(driver, deps)
                                observe_change(driver, deps, state_version, msg.await_timeout)
                            else:
                                self.log.warn(f"Got stale message ({msg}) in state {state_version.value}")
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

    def load_scripts(self) -> Scripts:
        def map_client_side_events(r): 
            def map_event(e: dict):
                if e['tag'] == 'loaded':
                    return Action(id='loaded', args=[], isEvent=True, timeout=None)
                elif e['tag'] == 'changed':
                    return Action(id='changed', args=[elements_to_refs(e['element'])], isEvent=True, timeout=None)
                else:
                    raise Exception(f"Invalid event tag in: {e}")

            return ClientSideEvents([map_event(e) for e in r['events']], elements_to_refs(r['state'])) if r is not None else None

        result_mappers = {
            'queryState': lambda r: elements_to_refs(r),
            'installEventListener': lambda r: r,
            'awaitEvents': map_client_side_events,
        }

        # can't type this with varargs
        def load_script(name: str) -> Any:
            key = 'QUICKSTROM_CLIENT_SIDE_DIRECTORY'
            client_side_dir = os.getenv(key)
            if not client_side_dir:
                raise Exception(f'Environment variable {key} must be set')
            file = open(f'{client_side_dir}/{name}.js')
            script = file.read()

            def f(driver: WebDriver, *args: List[JsonLike]) -> JsonLike:
                r = driver.execute_async_script(script, args)
                return result_mappers[name](r)

            return f

        return Scripts(
            query_state=load_script('queryState'),
            install_event_listener=load_script('installEventListener'),
            await_events=load_script('awaitEvents'),
        )


def elements_to_refs(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: elements_to_refs(value) for (key, value) in obj.items()}
    elif isinstance(obj, list):
        return [elements_to_refs(value) for value in obj]
    elif isinstance(obj, WebElement):
        return obj.id
    else:
        return obj


class Counter(object):
    def __init__(self, initial_value=0):
        self.value = initial_value
        self._lock = threading.Lock()
        
    def increment(self):
        with self._lock:
            self.value += 1
