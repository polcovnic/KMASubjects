import logging
import os
import re
import time
from abc import ABCMeta, abstractmethod

import requests

from saz_signuper.sender import Sender

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('saz_signuper/signuper.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Signuper(metaclass=ABCMeta):
    HTML_FILES_FILENAME = 'html_files'
    RESEND_DELAY = 2

    def __init__(self, cookies: list[dict]):
        self.cookies = dict()
        self.resend_attempts = 20
        self.proxy_list = Sender().get_working_proxies()
        self.proxy_attempts = 0
        for cookie in cookies:
            if cookie['domain'] == 'my.ukma.edu.ua':
                self.cookies[cookie['name']] = cookie['value']

    @staticmethod
    def get_csrf(html) -> str:
        s = re.search(r'<meta name="csrf-token" content="(.+)">', html)
        if s is None:
            logger.error("Can't find csrf token")
        return s.group(1)

    @classmethod
    def write_logs_html(cls, file_content: str, status_code, filename='log'):
        if not os.path.exists(cls.HTML_FILES_FILENAME):
            os.makedirs(cls.HTML_FILES_FILENAME)
        with open(f'{cls.HTML_FILES_FILENAME}/{filename}_{int(time.time_ns())}_{status_code}.html', 'w') as file:
            file.write(file_content)

    def log(self, inner_logger: logging.Logger, response, is_post: bool, info=None):
        method = 'POST' if is_post else 'GET'
        if int(response.status_code / 100) == 2:
            inner_logger.info(f'Successfully get groups page, {response.status_code}, {method}')
            self.write_logs_html(response.text, response.status_code)
        elif int(response.status_code / 100) == 4:
            self.write_logs_html(response.text, response.status_code, 'error')
            inner_logger.error(f'Client error {response.status_code}, {method}')
        elif int(response.status_code / 100) == 5:
            inner_logger.warning(f'Server error {response.status_code}, {method}')
            time.sleep(self.RESEND_DELAY)
            self.write_logs_html(response.text, response.status_code, 'warning')
            inner_logger.info(f'Resending {method} request for groups, attempts left: {self.resend_attempts}')
            return self.execute()

    def get(self, url, params=None):
        try:
            response = requests.get(url, params=params, cookies=self.cookies)
        except:  # some error when my ip blocked
            return self._get_with_proxy(self.proxy_list[0], url, params)
        else:
            self._update_cookies(response.cookies)
        logger.info(f'Successfully send GET to: {url}')
        return response

    def post(self, url, data=None, headers=None):
        try:
            response = requests.post(url, data=data, cookies=self.cookies, headers=headers)
        except:  # some error when my ip blocked
            return self._post_with_proxy(self.proxy_list[0], url, data, headers)
        else:
            self._update_cookies(response.cookies)
            logger.info(f'Successfully send POST to: {url}')
        return response

    def _update_cookies(self, cookies):
        for key, value in cookies.items():
            self.cookies[key] = value

    def _get_with_proxy(self, proxy, url, params=None):
        try:
            response = requests.get(url,
                                    proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy},
                                    timeout=15, params=params, cookies=self.cookies)
            self._update_cookies(response.cookies)
            logger.info(f'Successfully send GET to: {url}')
            return response
        except:
            if self.proxy_attempts >= len(self.proxy_list):
                logger.critical(f"Can't send GET through any proxy to: {url}")
                return None
            else:
                return self._get_with_proxy(self.proxy_list[self.proxy_attempts], url, params)

    def _post_with_proxy(self, proxy, url, data, headers):
        try:
            response = requests.post(url,
                                     proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy},
                                     timeout=15, data=data, headers=headers, cookies=self.cookies)
            self._update_cookies(response.cookies)
            logger.info(f'Successfully send POST to: {url}')
            return response
        except:
            if self.proxy_attempts >= len(self.proxy_list):
                logger.critical(f"Can't send POST through any proxy to: {url}")
                return None
            else:
                return self._post_with_proxy(self.proxy_list[self.proxy_attempts], url, data, headers)

    @abstractmethod
    def execute(self):
        pass
