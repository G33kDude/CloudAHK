#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import random
import time
from subprocess import PIPE, Popen, TimeoutExpired, run

import verboselogs
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse

from config import DESCRIPTION, TITLE, VERSION

# --- Constants ---

cloudapi = FastAPI(
    title=TITLE,
    description=DESCRIPTION,
    version=VERSION
)

CONTAINERS = 1

CWD = os.getcwd()

IMAGE_NAME = 'wine'

LANGUAGES = {
    'ahk': 'wine64 explorer /desktop=shell,800x600 Z:/ahk/AutoHotkeyU64.exe /ErrorStdOut /CP65001 \* 2>&1 ; wineboot -k',
    'ahk2': 'wine64 explorer /desktop=shell,800x600 Z:/ahk/v2/AutoHotkeyU64.exe /ErrorStdOut /CP65001 \* 2>&1 ; wineboot -k',
    'rlx': 'sh /ahk/relax/compile_and_run.sh ; wineboot -k',
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
        '--memory=100m',            # Limit container memory to 500MB
        '--memory-swap=100m',       # Don't allow any swap memory
        '-e', 'DISPLAY=:0',         # Use display 0 inside the container
        '-v', f'{CWD}/ahk:/ahk:ro',  # Map AHK folder into contianer
        IMAGE_NAME,                 # Use image tagged 'ahk'
        '/bin/sh', '-c',            # Run via sh inside the container
        'Xvfb -screen 0 800x600x24 &>/dev/null & ' +     # Start X server
        # 'openbox & ' +              # Start Openbox
        'wine64 explorer'
    ])
    # await asyncio.sleep(0.1)
    log.verbose(f'container made: {name}')
    if enter_pool:
        _container_pool.append(name)
    else:
        return name


async def run_code(code, language, timeout=7.0):
    global _container_pool
    try:
        name = _container_pool.pop(0)
    except IndexError as e:
        log.error(e)
        name = await alloc_container(False)

    # Run Docker
    p = Popen([
        'docker', 'exec',
        '-i',
        '-e', 'DISPLAY=:0',
        '-e', 'WINEDEBUG=-all',
        '-w', '/tmp',
        name,
        '/bin/sh', '-c',
        LANGUAGES[language]
    ], stdin=PIPE, stdout=PIPE)

    try:
        output = p.communicate(code.encode(
            'utf-8'), timeout)[0]  # .decode('utf-8')
        return (0, output)
    except TimeoutExpired:
        # Handle timeouts
        run(['/usr/bin/docker', 'stop', '-t=0', name], timeout=1)
        return (1, p.communicate()[0])  # .decode('utf-8'))
    finally:
        await alloc_container()


@cloudapi.get('/')
def root():
    return {'text': 'I\'m an api beep boop.'}


@cloudapi.get('/containers')
def container_amt():
    global _container_pool
    return {'num': len(_container_pool)}


@cloudapi.post('/format/{langauge}')
async def format_code(language: str, request: Request):
    if language != 'ahk':
        return JSONResponse(status_code=404, content={"message": "Unsupported language."})


@cloudapi.post('/{language}/run')
async def run_lang(language: str, request: Request):
    code = await request.body()
    code = code.decode('utf-8')
    log.info('Received code', code)
    legacy_language = language
    if not language.lower() in ['ahk', 'ahk2', 'rlx']:
        code = f'#!/usr/bin/env {language}\n' + code
    if code.startswith('#!'):
        check_lang = code.lstrip().lstrip(
            '#!/usr/bin/env').splitlines(1)[0].strip()
        log.debug(check_lang)
        language = check_lang
        legacy_language = 'unix'
    log.debug(language)
    if legacy_language in ['ahk', 'ahk2']:
        code = '#Include <Print>\n' + code

    # Run the code
    start_time = time.perf_counter()
    timeout, result = await run_code(code, legacy_language)
    elapsed = time.perf_counter() - start_time

    # Build the response JSON`
    response = {
        'time': None if timeout else elapsed,
        'stdout': result,
        'language': language
    }
    return response


async def main():
    for i in range(1):
        await alloc_container()

log: verboselogs.VerboseLogger = verboselogs.VerboseLogger(__name__)
asyncio.create_task(main())
