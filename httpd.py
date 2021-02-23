#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import urllib.request
from io import BytesIO
from subprocess import run
from zipfile import ZipFile

import uvicorn

AHK_URL = 'https://www.autohotkey.com/download/ahk.zip'

# change this to change max concurrent requests
WORKERS = 8
VERSION = 'dev'
# switch to True for developing
RELOAD = False

PATH = f'/cloudahk/api/{VERSION}'
#PATH = ""
PORT = 2453  # AHKD

IMAGE_NAME = 'wine'


def main():
    global _container_pool
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
    print('--- Starting up Server ---\n')
    if RELOAD:
        uvicorn.run("api:cloudapi", host="0.0.0.0", port=PORT,
                    log_level="info", root_path=PATH, reload=True, )
    else:
        uvicorn.run("api:cloudapi", host="0.0.0.0", port=PORT,
                    log_level="info", root_path=PATH, workers=WORKERS)


if __name__ == "__main__":
    if WORKERS > 15:  # protection against creating too many containers.
        # if you have a computer that can handle it, remove this line.
        raise Exception
    main()
