from os import getenv
from dotenv import load_dotenv
import logging
import verboselogs
load_dotenv()
from os import getcwd

LOGGING_LEVEL = verboselogs.SPAM
VERSION = getenv('VERSION')
PORT = int(getenv('PORT'))
RELOAD = False
WORKERS = 8
IMAGE_NAME = 'wine'
PATH = getenv('PATH').format(VERSION)
IMAGE_NAME = 'wine'
AHK_URL = 'https://www.autohotkey.com/download/ahk.zip'
AHK_2_URL = 'https://www.autohotkey.com/download/ahk-v2.zip'
HOST = "0.0.0.0"
TITLE = 'CLOUDAHK'
DESCRIPTION = 'An API for running autohotkey code in docker'

# change this to change max concurrent requests
# switch to True for developing
RELOAD = True
CONTAINERS = 1

CWD = getcwd()

IMAGE_NAME = 'wine'

IMAGE_NAME = 'wine'
