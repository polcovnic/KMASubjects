import time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from sender import Sender

proxy_list = Sender().get_working_proxies()


class LeakOfDataException(Exception):
    pass


class SeleniumChromeSender:
    WITH_PROXY = False  # having some problems with it
    WRITE_COOKIE_TO_FILE = True

    MS_URL = 'https://login.microsoftonline.com/'
    SAZ_URL = 'https://my.ukma.edu.ua/auth/o365'
    PHPSESSID_FILENAME = 'sess_id.json'

    # MS elements
    LC_MS_LOGIN_ID = 'i0116'
    LC_MS_NEXT_BUTTON_ID = 'idSIButton9'
    LC_MS_PASSWORD_ID = 'i0118'

    # LC_SAZ

    def __init__(self, email=None, password=None):
        self.sender = Sender()
        self.working_proxies = self.sender.get_working_proxies()
        self.chrome: webdriver.Chrome = None
        self.email: str = email
        self.password = password
        self._init_chrome()

    def _init_chrome(self):
        chrome_options = webdriver.ChromeOptions()
        if self.WITH_PROXY:
            chrome_options.add_argument(f'--proxy-server={self.working_proxies[0]}')
        self.chrome = webdriver.Chrome(options=chrome_options,
                                       executable_path='D:/ChromeDriver/chromedriver_win32/chromedriver.exe')

    def _ms_login_in(self):
        self.chrome.get(self.MS_URL)
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.presence_of_element_located(
                (By.ID, self.LC_MS_LOGIN_ID)
            )
        )
        # filling email
        login_input_field = self.chrome.find_element_by_id(self.LC_MS_LOGIN_ID)
        login_input_field.send_keys(self.email)
        next_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        next_button.click()
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.presence_of_element_located(
                (By.ID, self.LC_MS_PASSWORD_ID)
            )
        )
        # filling password
        password_input_field = self.chrome.find_element_by_id(self.LC_MS_PASSWORD_ID)
        password_input_field.send_keys(self.password)
        time.sleep(1)  # doesn't work without delay
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.presence_of_element_located(
                (By.ID, self.LC_MS_NEXT_BUTTON_ID)
            )
        )
        sign_in_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        sign_in_button.click()
        time.sleep(1)
        # do not exit button
        sign_in_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        sign_in_button.click()

    def _saz_sign_up(self):
        self.chrome.get(self.SAZ_URL)  # this url redirects to MS365 auth
        self.phpsessid = self.chrome.get_cookie('PHPSESSID')  # getting important cookie

        if self.WRITE_COOKIE_TO_FILE:  # writing this cookie to a file
            with open(self.PHPSESSID_FILENAME, 'w') as file:
                json.dump(self.phpsessid, file)

    def execute(self, email=None, password=None):
        if self.email is None:
            self.email = email
        if self.password is None:
            self.password = password
        if not (email and password):  # checking for not nullable credentials
            raise LeakOfDataException()
        self._ms_login_in()
        self._saz_sign_up()


if __name__ == '__main__':
    sender = SeleniumChromeSender()
    email = input('Enter your email: ')
    password = input('Enter your password: ')
    sender.execute(email, password)
