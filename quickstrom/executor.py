import io
import subprocess
import json
import logging

class Check():

    def __init__(self, module: str):
        self.log = logging.getLogger('quickstrom.executor')
        self.module = module

    def execute(self):
        with open("interpreter.log", "w+") as log:
            with subprocess.Popen(["specstrom", "check", self.module], text=True, stdout=subprocess.PIPE, stderr=log, stdin=subprocess.PIPE, bufsize=0) as p:

                def receive():
                    if p.poll() is None:
                        msg = json.loads(p.stdout.readline())
                        self.log.debug("Received %s", msg)
                        return msg
                    else:
                        raise "Done, can't receive."

                def send(msg):
                    self.log.debug("Sending %s", msg)
                    if p.poll() is None:
                        p.stdin.write(json.dumps(msg) + '\n')
                    else:
                        raise "Done, can't send."

                def query(deps):
                    return { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] }

                def run_sessions():
                    while True:
                        msg = receive()
                        if msg['tag'] == 'Start':
                            send({ 'tag': 'Event', 'contents': [{ 'tag': 'Loaded' }, { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] }] })
                            await_session_commands(msg['dependencies'])
                        elif msg['tag'] == 'Done':
                            return msg['results']

                def await_session_commands(deps):
                    self.log.info("Dependencies: %s", deps)
                    while True:
                        msg = receive()
                        if msg['tag'] == 'RequestAction':
                            state = query(deps)
                            send({ 'tag': 'Performed', 'contents': state })
                        elif msg['tag'] == 'End':
                            return

                results = run_sessions()
                print("Results:")
                for result in results:
                    print(f" - {result['valid']['tag']} {result['valid']['contents']}")