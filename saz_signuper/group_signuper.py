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
file_handler = logging.FileHandler('saz_signuper/group_signuper.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class GroupSignuper:
    PHPSESSID_FILENAME = 'saz_signuper/cookies.json'
    GROUPS_URL = 'https://my.ukma.edu.ua/curriculum/groups'
    RESEND_DELAY = 2

    def __init__(self, groups: dict):
        self.groups = groups
        with open(self.PHPSESSID_FILENAME, 'r') as file:
            self.phpsessid = json.load(file)
        self.resend_attempts = 20

    def signup(self):
        response = requests.get(self.GROUPS_URL, cookies={'PHPSESSID': self.phpsessid['value']})
        csrf_cookie = response.cookies['_csrf']
        if response.status_code == 200:
            logger.info('Successfully get groups page, 200')
        elif int(response.status_code / 100) == 4:
            logger.error('Client error {response.status_code}, GET')
        elif int(response.status_code / 100) == 5:
            logger.warning('Server error {response.status_code}, GET')
            time.sleep(self.RESEND_DELAY)
            logger.info('Resending GET request for groups, attempts left: {self.resend_attempts}')
            return self.signup()

        # getting csrf token
        token = ''
        try:
            token = self.get_csrf(response.text)
        except AttributeError:
            logger.warning('Html file without csrf')

        data = {'_csrf': token}

        for group_id, group_number in self.groups.items():
            data[f'course_group[{group_id}]'] = group_number

        print(data)
        # todo want to do like browser(with cookies)
        cookies = {'PHPSESSID': self.phpsessid['value'], '_csrf': csrf_cookie}

        response = requests.post(self.GROUPS_URL, data=data, cookies=cookies)
        logger.info(f'Status code: {response.status_code}')
        with open('groups.html', 'w') as file:
            file.write(response.text)
        print(response.status_code)

    @staticmethod
    def get_csrf(html) -> str:
        s = re.search(r'<meta name="csrf-token" content="(.+)">', html)
        if s is None:
            logger.error("Can't find csrf token")
        return s.group(1)
