#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import random
import time
from subprocess import PIPE, Popen, TimeoutExpired, run

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

# --- Constants ---

cloudapi = FastAPI(
    title='CloudAHK',
    description='An API that lets you execute autohotkey code remotely.',
    version='v0'
)

AHK_URL = 'https://www.autohotkey.com/download/ahk.zip'

CONTAINERS = 1

CWD = os.getcwd()

IMAGE_NAME = 'wine'

LANGUAGES = {
    'ahk': 'wine64 Z:/ahk/AutoHotkeyU64.exe /include Z:/ahk/CloudAHK.ahk /ErrorStdOut=UTF-8 /CP65001 \* 2>&1 ; wineboot -k',
    'ahk1': 'wine64 Z:/ahk/AutoHotkeyU64.exe /include Z:/ahk/CloudAHK.ahk /ErrorStdOut=UTF-8 /CP65001 \* 2>&1 ; wineboot -k',
    'ahk2': 'wine64 Z:/ahk2/AutoHotkeyU64.exe /include Z:/ahk2/CloudAHK.ahk /ErrorStdOut=UTF-8 /CP65001 \* 2>&1 ; wineboot -k',
    'unix': 'tee tmp.bin &>/dev/null && chmod +x tmp.bin &>/dev/null && ./tmp.bin 2>&1 ; wineboot -k'
}

# --- Globals ---


_container_pool = []


# --- Helper Functions ---

async def alloc_container(enter_pool=True):
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
        '--memory=500m',            # Limit container memory to 500MB
        '--memory-swap=500m',       # Don't allow any swap memory
        '-e', 'DISPLAY=:0',         # Use display 0 inside the container
        '-v', f'{CWD}/ahk:/ahk:ro',  # Map AHK folder into contianer
        '-v', f'{CWD}/ahk2:/ahk2:ro',  # Map AHK folder into contianer
        IMAGE_NAME,                 # Use image tagged 'ahk'
        '/bin/sh', '-c',            # Run via sh inside the container
        'Xvfb &>/dev/null & ' +     # Start X server
        'openbox & ' +              # Start Openbox
        'wine64 notepad'
    ])
    await asyncio.sleep(0.1)
    print(f'container made: {name}')
    if enter_pool:
        _container_pool.append(name)
    else:
        return name


async def run_code(code, language, timeout=7.0):
    global _container_pool
    try:
        name = _container_pool.pop(0)
    except IndexError as e:
        print(e)
        name = await alloc_container(False)

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
        await alloc_container()

@cloudapi.get('/')
def root():
    return {'text':'I\'m an api beep boop.'}

@cloudapi.get('/containers')
def container_amt():
    global _container_pool
    return {'num': len(_container_pool)}

@cloudapi.post('/{language}')
async def ace_legacy_run(language: str, request: Request):
    '''DEPRECATED. Use \'/{language}/run\''''
    return RedirectResponse(url=f'/cloudahk/api/v0/{language}/run', status_code=307)

@cloudapi.post('/run/{language}')
async def legacy_run(language: str, request: Request):
    '''DEPRECATED. Use \'/{language}/run\''''
    return RedirectResponse(url=f'/cloudahk/api/v0/{language}/run', status_code=308)


@cloudapi.post('/{language}/run')
async def run_lang(language: str, request: Request):
    code = await request.body()
    code = code.decode('utf-8')
    print('Received code', code)
    if code.startswith('#!'):
        language = 'unix'
    if code.startswith(';v2'):
        language = 'ahk2'

    # Run the code
    start_time = time.perf_counter()
    timeout, result = await run_code(code, language)
    elapsed = time.perf_counter() - start_time

    # Build the response JSON
    response = {
        'time': None if timeout else elapsed,
        'stdout': result
    }
    return response


async def main():
    for i in range(2):
        await alloc_container()


asyncio.create_task(main())
