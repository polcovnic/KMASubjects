import re
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread
import logging
import json
import time
import random

import requests
from bs4 import BeautifulSoup

from saz_signuper.sender import Sender

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('saz_signuper/signuper.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Subject:
    def __init__(self, url, name):
        self.url = url
        self.name = name
        self.is_signed_up = False

    def __repr__(self):
        return f'<{self.name}>'


class Signuper:
    USE_PROXY = False
    PHPSESSID_FILENAME = 'saz_signuper/sess_id.json'
    USE_CONCURRENCY = False
    RESEND_DELAY = 2

    def __init__(self, subjects: list[Subject]):
        self.subjects = subjects
        if self.USE_PROXY:
            self.sender = Sender()
        self.result_dict: dict[Subject, Future] = {}
        with open(self.PHPSESSID_FILENAME, 'r') as file:
            self.phpsessid = json.load(file)
        self.resend_attempts = 20
        logger.debug('Signuper created')

    def _signup(self, subject: Subject):
        if self.resend_attempts == 0:
            logger.error('Resend attempts ended')
            return False
        # getting page for csrf
        if self.USE_PROXY:
            response = self.sender.get(subject.url, params={'PHPSESSID': self.phpsessid['value']})
        else:
            response = requests.get(subject.url, cookies={'PHPSESSID': self.phpsessid['value']})
        # GET response logging
        if response.status_code == 200:
            logger.info(f'Successfully get {subject} subject page, 200')
        elif int(response.status_code / 100) == 4:
            logger.error(f'Client error {response.status_code}, GET, subject: {subject}')
        elif int(response.status_code / 100) == 5:
            logger.warning(f'Server error {response.status_code}, GET, subject: {subject}')
            time.sleep(self.RESEND_DELAY)
            logger.info(f'Resending GET request for subject: {subject}, attempts left: {self.resend_attempts}')
            return self._signup(subject)
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find('h1')
        if re.search('exception|error', str(body).lower()) is not None:
            logger.warning(f'Exception with status code {response.status_code}, GET, subject: {subject}')
            self.write_errors_html(response.text)
            time.sleep(self.RESEND_DELAY)
            logger.info(f'Resending POST request for subject: {subject}, attempts left: {self.resend_attempts}')
            return self._signup(subject)

        # getting csrf token
        token = ''
        try:
            token = self.get_csrf(response.text)
        except AttributeError:
            logger.warning('Html file without csrf')
        # sending request to sign up for a subject
        if self.USE_PROXY:
            post_response = self.sender.post(subject.url, data={'csrf': token, 'PHPSESSID': self.phpsessid['value']})
        else:
            post_response = requests.post(subject.url, data={'csrf': token},
                                          cookies={'PHPSESSID': self.phpsessid['value']})
        # POST response logging
        if post_response.status_code == 201:
            logger.info(f'Successfully signed up on {subject} subject, 201')
            return True
        elif int(post_response.status_code / 100) == 4:
            logger.error(f'Client error {response.status_code}, POST, subject: {subject}')
        elif int(post_response.status_code / 100) == 5:
            logger.warning(f'Server error {response.status_code},  POST, subject: {subject}')
            time.sleep(self.RESEND_DELAY)
            logger.info(f'Resending POST request for subject: {subject}, attempts left: {self.resend_attempts}')
            return self._signup(subject)

    def _start_signup(self):
        executor = ThreadPoolExecutor()
        for subject in self.subjects:
            self.result_dict[subject] = executor.submit(self._signup, subject)
        executor.shutdown()

    def execute(self) -> dict:
        if self.USE_CONCURRENCY:
            thread = Thread(target=self._start_signup)
            thread.start()
            thread.join()
        else:
            for subject in self.subjects:
                self._signup(subject)
        return self.result_dict

    @staticmethod
    def get_csrf(html) -> str:
        s = re.search(r'<meta name="csrf-token" content="(.+)">', html)
        if s is None:
            logger.error("Can't find csrf token")
        return s.group(1)

    @staticmethod
    def write_errors_html(file_content: str):
        with open(f'{random.randint(0, 1000)}_{int(time.time())}.html', 'w') as file:
            file.write(file_content)


if __name__ == '__main__':
    signuper = Signuper([Subject('http://127.0.0.1:5000/python-programming', 'Python course'),
                         Subject('http://127.0.0.1:5000/java-programming', 'Java course')])
    print(signuper.execute())
