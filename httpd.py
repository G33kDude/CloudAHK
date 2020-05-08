#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import socketserver
import http.server
import os
import time
import json
import random
from subprocess import Popen, PIPE, TimeoutExpired, run

from io import BytesIO
from zipfile import ZipFile
import urllib.request


# --- Constants ---

AHK_URL = 'https://www.autohotkey.com/download/ahk.zip'

ADDRESS = ('', 2453) # AHKD

CWD = os.getcwd()

IMAGE_NAME = 'wine'

DOCKER_COMMAND = [
    '/usr/bin/docker', 'run',
    '--rm',                     # Remove the container after termination
    '-i',                       # Keep docker attached to STDIN
    '--network=none',           # Disallow networking inside the container
    '--cpus=1',                 # Max CPU usage, 100% of one core
    '--cap-drop=ALL',           # Disallow most "linux capabilities"
    '-e', 'DISPLAY=:0',         # Use display 0 inside the container
    '-e', 'WINEDEBUG=-all',     # Suppress WINE debug messages
    '-v', f'{CWD}/ahk:/ahk:ro', # Map AHK folder into contianer
    IMAGE_NAME,                 # Use image tagged 'ahk'
    '/bin/sh', '-c',            # Run via sh inside the container
    'Xvfb &>/dev/null & ' +     # Start X server
    'openbox &>/dev/null & ' +  # Start Openbox
    'wine64 Z:/ahk/AutoHotkeyU64.exe /ErrorStdOut \* 2>&1' # Start AHK
]


# --- Helper Functions ---

def run_code(code, timeout=7.0):
    # Generate a random container name
    name = f'ahk_{random.randint(0,0xFFFFFFFF):08x}'
    command = DOCKER_COMMAND.copy()
    command.insert(2, f'--name={name}')

    # Run Docker
    p = Popen(command, stdin=PIPE, stdout=PIPE)
    try:
        return (0, p.communicate(code.encode('utf-8'), timeout)[0].decode('utf-8'))
    except TimeoutExpired:
        # Handle timeouts
        run(['/usr/bin/docker', 'stop', '-t=0', name], timeout=1)
        return (1, p.communicate()[0].decode('utf-8'))


# --- HTTP Server ---

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')

            # Run the code
            start_time = time.perf_counter()
            timeout, result = run_code(body)
            elapsed = time.perf_counter() - start_time

            # Build the response JSON
            response = {
                    'time': None if timeout else elapsed,
                    'stdout': result
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'There was a problem processing your request')
            raise e


# --- Entrypoint ---

def main():
    # Download AutoHotkey
    print('--- Checking for AutoHotkey ---\n')
    if os.path.isfile(os.path.join('ahk', 'AutoHotkeyU64.exe')):
        print('Found!')
    else:
        print('Downloading AutoHotkey')
        req = urllib.request.Request(AHK_URL,
                headers={'User-Agent': 'https://github.com/G33kDude/CloudAHK'})
        resp = urllib.request.urlopen(req)
        with ZipFile(BytesIO(resp.read())) as zipfile:
            zipfile.extract('AutoHotkeyU64.exe', 'ahk')
    print('\n')

    # Build docker image
    print('--- Building Docker Image ---\n')
    run(['docker', 'build', '-t', IMAGE_NAME, 'wine-docker'])
    print('\n')

    # Start HTTP
    print('--- Starting HTTP Server ---\n')
    server = ThreadedHTTPServer(ADDRESS, Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    while True:
        time.sleep(5)

if __name__ == "__main__":
    main()
