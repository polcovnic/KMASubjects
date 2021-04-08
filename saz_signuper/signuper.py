import logging
import re
from concurrent.futures import ThreadPoolExecutor
import logging

from sender import Sender
from subject import Subject

# setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('signuper.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

class Signuper:
    USE_PROXY = False

    def __init__(self, subjects: list[Subject]):
        self.subjects = subjects
        self.sender = Sender()

    def signup(self, subject: Subject):
        if self.USE_PROXY:
            response = self.sender.send(subject.url)
            if response.status_code == 201:
                logger.info(f'Successfully signed up on {subject} subject')

    def start(self):
        pass
