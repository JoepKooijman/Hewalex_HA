import os
from PCWU import *
import logging
import sys

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.info('Starting Hewalex MQTT HA Integration')

def initPCWU():
    config_file = os.path.join(os.path.dirname(__file__), 'hewalexconfig.ini')
    dev = PCWU(config_file,logger)

if __name__ == "__main__":
    initPCWU()