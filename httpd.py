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

LANGUAGES = {
    'ahk': 'wine64 Z:/ahk/AutoHotkeyU64.exe /ErrorStdOut /CP65001 \* 2>&1 ; wineboot -k',
    'rlx': 'sh /ahk/relax/compile_and_run.sh'
}


# --- Globals ---

_container_pool = []


# --- Helper Functions ---

def alloc_container():
    global _container_pool
    name = f'ahk_{random.randint(0,0xFFFFFFFF):08x}'
    Popen([
        'docker', 'run',
        '--name', name,
        '--init',
        '--rm',                     # Remove the container after termination
        '-d',                       # Detach and run in the background
        '--network=none',           # Disallow networking inside the container
        '--cpus=1',                 # Max CPU usage, 100% of one core
        '--cap-drop=ALL',           # Disallow most "linux capabilities"
        '-e', 'DISPLAY=:0',         # Use display 0 inside the container
        '-v', f'{CWD}/ahk:/ahk:ro', # Map AHK folder into contianer
        IMAGE_NAME,                 # Use image tagged 'ahk'
        '/bin/sh', '-c',            # Run via sh inside the container
        'Xvfb &>/dev/null & ' +     # Start X server
        'openbox & ' +              # Start Openbox
        'wine64 explorer'
    ])
    _container_pool.append(name)
    

def run_code(code, language, timeout=7.0):
    global _container_pool
    name = _container_pool.pop(0)

    # Run Docker
    p = Popen([
        'docker', 'exec',
        '-i',
        # '-e', 'DISPLAY=:0',
        '-e', 'WINEDEBUG=-all',
        '-w', '/tmp',
        name,
        '/bin/sh', '-c',
        LANGUAGES[language]
    ], stdin=PIPE, stdout=PIPE)

    try:
        output = p.communicate(code.encode('utf-8'), timeout)[0].decode('utf-8')
        return (0, output)
    except TimeoutExpired:
        # Handle timeouts
        run(['/usr/bin/docker', 'stop', '-t=0', name], timeout=1)
        return (1, p.communicate()[0].decode('utf-8'))
    finally:
       alloc_container()


# --- HTTP Server ---

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            print('Received body', body)
            language = 'rlx' if 'rlx' in self.path else 'ahk'

            # Run the code
            start_time = time.perf_counter()
            timeout, result = run_code(body, language)
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

    print('--- Initializing Container Pool ---\n')
    for i in range(3):
        alloc_container()

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
