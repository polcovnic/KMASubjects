import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread

from bs4 import BeautifulSoup

from saz_signuper.sender import Sender
from saz_signuper.signuper import Signuper

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('saz_signuper/subject_signuper.log')
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


class SubjectSignuper(Signuper):
    USE_PROXY = False
    USE_CONCURRENCY = False
    HTML_FILES_FILENAME = f'{Signuper.HTML_FILES_FILENAME}/subjects'

    def __init__(self, subjects: list[Subject], cookies):
        super().__init__(cookies)
        self.subjects = subjects
        if self.USE_PROXY:
            self.sender = Sender()
        self.result_dict: dict[Subject, Future] = {}
        logger.debug('Signuper created')

    def _signup(self, subject: Subject):
        if self.resend_attempts == 0:
            logger.error('Resend attempts ended')
            return False
        # getting page for csrf
        response = self.get(subject.url)
        # GET logging
        self.log(logger, response, False)
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.find('h1')
        # checking for 'failed success' error when status code equals 2xx
        if re.search('exception|error', str(body).lower()) is not None:
            logger.warning(f'Exception with status code {response.status_code}, GET, subject: {subject}')
            self.write_logs_html(response.text, response.status_code)
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
        response = self.post(re.sub(r'/course/(\d+)', r'/next/course/\g<1>/enroll', subject.url),
                             headers={'x-csrf-token': token})
        # POST response logging
        self.log(logger, response, False)

    def log(self, inner_logger: logging.Logger, response, is_post: bool, subject=None):
        method = 'POST' if is_post else 'GET'
        if int(response.status_code / 100) == 2:
            inner_logger.info(f'Successfully signed up on {subject} subject, {response.status_code}')
            self.write_logs_html(response.text, response.status_code)
            return True
        elif int(response.status_code / 100) == 4:
            inner_logger.error(f'Client error {response.status_code}, {method}, subject: {subject}')
            self.write_logs_html(response.text, response.status_code)
        elif int(response.status_code / 100) == 5:
            inner_logger.warning(f'Server error {response.status_code},  POST, subject: {subject}')
            time.sleep(self.RESEND_DELAY)
            inner_logger.info(f'Resending POST request for subject: {subject}, attempts left: {self.resend_attempts}')
            self.write_logs_html(response.text, response.status_code, 'error')
            return self._signup(subject)
        else:
            inner_logger.critical(f"Lol, it's {response.status_code}")
            self.write_logs_html(response.text, response.status_code, 'critical')

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


if __name__ == '__main__':
    signuper = SubjectSignuper([Subject('http://127.0.0.1:5000/python-programming', 'Python course'),
                                Subject('http://127.0.0.1:5000/java-programming', 'Java course')], [])
    print(signuper.execute())
