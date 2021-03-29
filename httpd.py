#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import urllib.request
from io import BytesIO
from os import getenv
from subprocess import run
from zipfile import ZipFile
from config import VERSION, PORT, RELOAD, PATH, IMAGE_NAME, WORKERS, LOGGING_LEVEL, IMAGE_NAME, AHK_URL, AHK_2_URL, HOST
import uvicorn
import coloredlogs
import verboselogs


def setup_logging():
    verboselogs.install()
    coloredlogs.install(level=LOGGING_LEVEL,
                        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    log: verboselogs.VerboseLogger = logging.getLogger(__name__)

    # root = logging.getLogger()
    # fmt = logging.Formatter(fmt='{asctime} [{levelname}] {name}: {message}', datefmt='%Y-%m-%d %H:%M:%S', style='{')
    # #logging.basicConfig(level=LOGGING_LEVEL,
    # #                    format='{asctime} [{levelname}] {name}: {message}', datefmt='%Y-%m-%d %H:%M:%S', style='{')
    # stream = logging.StreamHandler()
    # stream.setFormatter(fmt)
    # root.addHandler(stream)
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    return log


def main():
    global _container_pool
    # Download AutoHotkey
    log.debug('Checking for AutoHotkey')
    if os.path.isfile(os.path.join('ahk', 'AutoHotkeyU64.exe')):
        log.debug('Autohotkey Found')
    else:
        log.debug('Downloading AutoHotkey')
        req = urllib.request.Request(
            AHK_URL,
            headers={'User-Agent': 'https://github.com/G33kDude/CloudAHK'})
        log.spam('autohotkey downloaded')
        resp = urllib.request.urlopen(req)
        with ZipFile(BytesIO(resp.read())) as zipfile:
            zipfile.extract('AutoHotkeyU64.exe', 'ahk')
        log.spam('autohotkey extracted')
    # Download AutoHotkey V2
    log.debug('Checking for AutoHotkey VERSION 2')
    if os.path.isfile(os.path.join('ahk', 'v2', 'AutoHotkeyU64.exe')):
        log.debug('Found!')
    else:
        log.debug('Downloading AutoHotkey')
        req = urllib.request.Request(
            AHK_2_URL,
            headers={'User-Agent': 'https://github.com/G33kDude/CloudAHK'})
        resp = urllib.request.urlopen(req)
        log.debug('extracting')
        with ZipFile(BytesIO(resp.read())) as zipfile:
            zipfile.extract('AutoHotkeyU64.exe', 'ahk/v2')
        log.spam('autohotkey V2 extracted')


    # Build docker image
    log.info('Building Docker Image')
    run(['docker', 'build', '-t', IMAGE_NAME, 'wine-docker'])

    # Start HTTP
    log.info('Starting up Server')
    if RELOAD:
        WORKERS = None
    uvicorn.run(
        "api:cloudapi",
        host=HOST,
        port=PORT,
        log_level=LOGGING_LEVEL,
        root_path=PATH,
        reload=RELOAD,
        workers=WORKERS
    )


if __name__ == "__main__":
    log = setup_logging()
    if WORKERS > 15:  # protection against creating too many workers.
        # if you have a computer that can handle it, remove this line.
        raise Exception
    main()
