import logging
import re
import time

import requests

from saz_signuper.signuper import Signuper

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/saz_signuper/group_signuper.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class GroupSignuper(Signuper):
    GROUPS_URL = 'https://my.ukma.edu.ua/curriculum/groups'
    HTML_FILES_FILENAME = f'{Signuper.HTML_FILES_FILENAME}/groups'

    def __init__(self, groups: dict, cookies):
        super().__init__(cookies)
        self.groups = groups

    def execute(self):
        response = self.get(self.GROUPS_URL)
        self.log(logger, response, False)
        # getting csrf token
        token = ''
        try:
            token = self.get_csrf(response.text)
        except AttributeError:
            logger.warning('Html file without csrf')

        data = {'_csrf': token}

        for group_id, group_number in self.groups.items():
            data[f'course_group[{group_id}]'] = group_number

        # response = self.post(self.GROUPS_URL, data=data)
        # self.log(logger, response, True)
        print(response.status_code)
