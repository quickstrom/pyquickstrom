import io
import subprocess
import json

class Check():

    def __init__(self, module: str):
        self.module = module

    def execute(self):
        with open("interpreter.log", "w+") as log:
            with subprocess.Popen(["specstrom", "check", self.module], text=True, stdout=subprocess.PIPE, stderr=log, stdin=subprocess.PIPE, bufsize=0) as p:

                def receive():
                    if p.poll() is None:
                        msg = json.loads(p.stdout.readline())
                        #print("Received", msg)
                        return msg
                    else:
                        print("Done, can't receive.")

                def send(msg):
                    #print("Sending", msg)
                    if p.poll() is None:
                        p.stdin.write(json.dumps(msg) + '\n')
                    else:
                        print("Done, can't send.")

                def run_sessions():
                    while True:
                        msg = receive()
                        if msg['tag'] == 'Start':
                            send({ 'tag': 'Event', 'contents': [{ 'tag': 'Loaded' }, { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] }] })
                            await_session_commands()
                        elif msg['tag'] == 'Done':
                            return msg['results']

                def await_session_commands():
                    while True:
                        msg = receive()
                        if msg['tag'] == 'RequestAction':
                            send({ 'tag': 'Performed', 'contents': { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] } })
                        elif msg['tag'] == 'End':
                            return

                results = run_sessions()
                print("Results:")
                for result in results:
                    print(f" - {result['valid']['tag']} {result['valid']['contents']}")