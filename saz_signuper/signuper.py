import re
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread
import logging
import json

import requests

from sender import Sender

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('signuper.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


class Subject:
    def __init__(self, url):
        self.url = url
        self.is_signed_up = False


class Signuper:
    USE_PROXY = False
    PHPSESSID_FILENAME = 'sess_id.json'

    def __init__(self, subjects: list[Subject]):
        self.subjects = subjects
        self.sender = Sender()
        self.result_dict: dict[Subject, Future] = {}
        with open(self.PHPSESSID_FILENAME, 'w') as file:
            self.phpsessid = json.load(file)

    def _signup(self, subject: Subject):
        # getting page for csrf
        if self.USE_PROXY:
            response = self.sender.get(subject.url, params={'PHPSESSID': self.phpsessid})
        else:
            response = requests.get(subject.url, params={'PHPSESSID': self.phpsessid})
        # GET response logging
        if response.status_code == 200:
            logger.info(f'Successfully get {subject} subject page')
        elif response.status_code / 100 == 4:
            logger.error(f'Client error {response.status_code}')
        elif response.status_code / 100 == 5:
            logger.info(f'Server error {response.status_code}')
            self._signup(subject)
        # getting csrf token
        token = self.get_csrf(response.text)
        # sending request to sign up for a subject
        if self.USE_PROXY:
            post_response = self.sender.post(subject.url, data={'csrf': token, 'PHPSESSID': self.phpsessid})
        else:
            post_response = requests.post(subject.url, data={'csrf': token, 'PHPSESSID': self.phpsessid['value']})
        # POST response logging
        if post_response.status_code == 201:
            logger.info(f'Successfully signed up on {subject} subject')
            return True
        elif response.status_code / 100 == 4:
            logger.error(f'Client error {response.status_code}')
        elif response.status_code / 100 == 5:
            logger.info(f'Server error {response.status_code}')
            return self._signup(subject)

    def _start_signup(self):
        executor = ThreadPoolExecutor()
        for subject in self.subjects:
            self.result_dict[subject] = executor.submit(self._signup, subject)
        executor.shutdown()

    def start(self) -> dict:
        thread = Thread(target=self._start_signup)
        thread.start()
        thread.join()
        return self.result_dict

    @staticmethod
    def get_csrf(html) -> str:
        m = re.match(r'\<meta name\=\"csrf\-token\" content\=\"([^"]+)"\>', html)
        return m.group(1)
