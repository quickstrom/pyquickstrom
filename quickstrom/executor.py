import io
import subprocess
import json

class Check():

    def __init__(self, module: str):
        self.module = module


    def execute(self):
        with open("interpreter.log", "w+") as log:
            with subprocess.Popen(["specstrom", "check", self.module], text=True, stdout=subprocess.PIPE, stderr=log, stdin=subprocess.PIPE, bufsize=1) as p:

                def receive():
                    if p.poll() is None:
                        print("Receiving")
                        return json.loads(p.stdout.readline())
                    else:
                        print("Done, can't receive.")

                def send(msg):
                    print("Sending")
                    if p.poll() is None:
                        p.stdin.write(json.dumps(msg) + '\n')

                send({ 'tag': 'Event', 'contents': [{ 'tag': 'Loaded' }, { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] }] })
                while True:
                    print(receive())
                    send({ 'tag': 'Performed', 'contents': { 'foo': [{ 'disabled': False }], 'bar': [{ 'disabled': False }], 'button': [{ 'ref': 'btn', 'disabled': False }] } })