import time
import json
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from saz_signuper.sender import Sender

# setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/saz_signuper/loginer.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


class LeakOfDataException(Exception):
    pass


class Loginer:
    WITH_PROXY = False  # having some problems with it
    WRITE_COOKIE_TO_FILE = True

    MS_URL = 'https://login.microsoftonline.com/'
    SAZ_URL = 'https://my.ukma.edu.ua/auth/o365'

    # MS elements
    LC_MS_LOGIN_ID = 'i0116'
    LC_MS_NEXT_BUTTON_ID = 'idSIButton9'
    LC_MS_PASSWORD_ID = 'i0118'

    def __init__(self):
        self.chrome: webdriver.Chrome = None
        self._init_chrome()

    def _init_chrome(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            if self.WITH_PROXY:
                chrome_options.add_argument(f'--proxy-server={Sender().get_working_proxies()[0]}')
            self.chrome = webdriver.Chrome(options=chrome_options,
                                           executable_path='D:/ChromeDriver/chromedriver_win32/chromedriver.exe')
        except Exception as e:
            logger.error("Can't start chrome")
            raise e
        else:
            logger.debug('Chrome started successfully')

    def _ms_login_in(self, email, password):
        self.chrome.get(self.MS_URL)
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.visibility_of_element_located(
                (By.ID, self.LC_MS_LOGIN_ID)
            )
        )
        # filling email
        login_input_field = self.chrome.find_element_by_id(self.LC_MS_LOGIN_ID)
        login_input_field.send_keys(email)
        next_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        next_button.click()
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.visibility_of_element_located(
                (By.ID, self.LC_MS_PASSWORD_ID)
            )
        )
        # filling password
        password_input_field = self.chrome.find_element_by_id(self.LC_MS_PASSWORD_ID)
        password_input_field.send_keys(password)
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.visibility_of_element_located(
                (By.ID, self.LC_MS_NEXT_BUTTON_ID)
            )
        )
        sign_in_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        sign_in_button.click()
        WebDriverWait(self.chrome, 10).until(
            expected_conditions.visibility_of_element_located(
                (By.ID, self.LC_MS_NEXT_BUTTON_ID)
            )
        )
        # do not exit button
        sign_in_button = self.chrome.find_element_by_id(self.LC_MS_NEXT_BUTTON_ID)
        sign_in_button.click()

    def _saz_sign_in(self):
        self.chrome.get(self.SAZ_URL)  # this url redirects to MS365 auth
        self.phpsessid = self.chrome.get_cookie('PHPSESSID')  # getting important cookie

        # if self.WRITE_COOKIE_TO_FILE:  # writing this cookie to a file
        #     with open(self.PHPSESSID_FILENAME, 'w') as file:
        #         json.dump(self.phpsessid, file)

    def execute(self, email=None, password=None) -> list:  # returns cookies
        if not (email and password):  # checking for not nullable credentials
            logger.warning("Loginer has started without email or password or both")
            raise LeakOfDataException()
        # logging in MS365
        try:
            self._ms_login_in(email, password)
        except Exception:
            logger.error("Can't login in MS365")
        else:
            logger.info('Successfully logged in MS365')
        # logging in SAZ
        try:
            self._saz_sign_in()
        except Exception:
            logger.error("Can't login in SAZ")
        else:
            logger.info('Successfully logged in SAZ')

        cookies = self.chrome.get_cookies()
        self.chrome.close()
        return cookies


if __name__ == '__main__':
    sender = Loginer()
    email = input('Enter your email: ')
    password = input('Enter your password: ')
    cookies = sender.execute(email, password)
    for cookie in cookies:
        print(cookie)
