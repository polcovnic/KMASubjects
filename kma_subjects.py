import re
import time
import os.path
import json

import logging
from pyrogram import Client, filters

from saz_signuper.loginer import Loginer
from saz_signuper.subject_signuper import SubjectSignuper, Subject
from saz_signuper.group_signuper import GroupSignuper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('kma_subjects.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

subject_list = [Subject('https://my.ukma.edu.ua/course/242211', 'Client-server developing')]


# subjects = [Subject('http://127.0.0.1:5000/python-programming', 'Python course'),
#             Subject('http://127.0.0.1:5000/java-programming', 'Java course')]


class KmaSubjects:
    def __init__(self, phone_number: str = '', email: str = '', password: str = '', update=False):
        self.phone_number = phone_number
        self.email = email
        self.password = password
        self.app: Client = None  # TODO client
        self.cookies = dict()
        if email == '' or password == '':
            with open('credentials.json', 'r') as file:
                credentials = json.load(file)
                self.email = credentials['email']
                self.password = credentials['password']

        if os.path.exists('cookies.json') and not update:
            with open('cookies.json', 'r') as file:
                self.cookies = json.load(file)
        else:
            self.login()

    def tg_registration(self, confirmation_code):  # TODO tg signup
        pass

    def login(self):
        loginer = Loginer()
        self.cookies = cookies = loginer.execute(self.email, self.password)
        with open('cookies.json', 'w') as file:
            json.dump(cookies, file)

    def signup_to_subjects(self, subjects: list):
        signuper = SubjectSignuper(subjects, self.cookies)
        signuper.execute()

    def signup_in_groups(self, groups: dict):
        signuper = GroupSignuper(groups, self.cookies)
        signuper.execute()

    def signup_when_saz_opens_to_subjects(self, subjects: list[str]):
        @self.app.on_message(filters.chat('my_ukma'))
        def waiting_for_saz_message(client: Client, message: filters.Message):
            if re.search('Поточний етап у САЗ', message.text):
                self.signup_to_subjects(subjects)

    def signup_when_saz_opens_in_groups(self, groups: dict):
        @self.app.on_message(filters.chat('my_ukma'))
        def waiting_for_saz_message(client: Client, message: filters.Message):
            if re.search('Поточний етап у САЗ', message.text):
                self.signup_in_groups(groups)


# def init(email, password):
#     loginer = Loginer()
#     cookies = loginer.execute(email, password)
#     with open('cookies.json', 'w') as file:
#         json.dump(cookies, file)
#     return cookies


groups_to_signup = {
    '242129': 2,
    '242197': 4,
    '242211': 6
}
#
#
# def start(groups: bool, cookies):
#     if groups:
#         group_signuper = GroupSignuper(groups_to_register, cookies)
#         group_signuper.execute()
#     else:
#         signuper = SubjectSignuper(subject_list, cookies)
#         signuper.execute()


# @app.on_message(filters.chat('my_ukma'))
# def waiting_for_saz_message(client: Client, message: filters.Message):
#     if re.search('Поточний етап у САЗ', message.text):
#         start(False)

# UPDATE = False
# if __name__ == '__main__':
# if os.path.exists('cookies.json') and not UPDATE:
#     with open('cookies.json', 'r') as file:
#         cookies = json.load(file)
# else:
#     with open('credentials.json', 'r') as file:
#         credentials = json.load(file)
#     cookies = init(credentials['email'], credentials['password'])
# for cookie in cookies:
#     print(cookie)
# app.run()
# start(True, cookies)


if __name__ == '__main__':
    saz_signuper = KmaSubjects('', '', '', False)
    saz_signuper.signup_in_groups(groups_to_signup)
