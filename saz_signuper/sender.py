import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
import heapq

import requests
from bs4 import BeautifulSoup

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/saz_signuper/sender.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Sender:
    PROXY_LIST_URL = 'https://free-proxy-list.net/'
    PROXY_FILTER = 'elite proxy'
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    HTTP_BIN_URL = 'https://httpbin.org/ip'
    CHROME_EXECUTABLE = 'D:/ChromeDriver/chromedriver_win32/chromedriver.exe'

    def __init__(self):
        self.target_url = None
        self.available_proxies = []
        self.first_available_proxy: str = None
        self.proxy_generator_instance = None
        self._update_proxies()
        self.end_of_getting_proxies = False

    def __get_proxies(self):
        r = requests.get(self.PROXY_LIST_URL)

        soup = BeautifulSoup(r.content, 'html.parser')
        table = soup.find('tbody')
        proxies = []
        for row in table:
            if row.find_all('td')[4].text == self.PROXY_FILTER:
                proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
                proxies.append(proxy)
                # print(proxy)
            else:
                pass
        if len(proxies) == 0:
            logger.warning("Can't get any proxy")
        else:
            logger.debug(f"Successfully got {len(proxies)} proxies")
        return proxies

    def check_for_available_proxy(self, proxy):
        try:
            r = requests.get(self.HTTP_BIN_URL, headers=self.HEADERS,
                             proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy}, timeout=1)
            # print(r.json(), r.status_code)
        except:
            return None
        else:
            if not self.first_available_proxy:
                self.first_available_proxy = proxy
                logger.debug('First available proxy added')
            self.available_proxies.append(proxy)
            logger.debug(f'Another one available proxy added (available proxies = {len(self.available_proxies)})')
            return proxy

    def _get_working_proxy(self):
        self.end_of_getting_proxies = False
        proxy_list = self.__get_proxies()
        executor = ThreadPoolExecutor()
        for proxy in proxy_list:
            executor.submit(self.check_for_available_proxy, proxy)
        executor.shutdown()
        self.end_of_getting_proxies = True
        print(self.end_of_getting_proxies)

    def _proxy_generator(self):
        for proxy in self.available_proxies:
            yield proxy

    def _send_get_request(self, proxy, params):
        try:
            if not self.proxy_generator_instance:
                self.proxy_generator_instance = self._proxy_generator()
            response = requests.get(self.target_url, headers=self.HEADERS,
                                    proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy},
                                    timeout=15, params=params)
            logger.info('Successfully GET response through proxy')
            return response
        except:  # some errors with sending
            try:
                logger.debug("Send GET through another proxy")
                return self._send_get_request(next(self.proxy_generator_instance), params)
            except StopIteration:
                logger.warning('No available proxies found in GET, sending through my ip')
                resp = requests.get(self.target_url, headers=self.HEADERS, params=params)
                logger.warning('Successfully sent GET through my ip')
                return resp

    def _send_post_request(self, proxy, data):
        try:
            if not self.proxy_generator_instance:
                self.proxy_generator_instance = self._proxy_generator()
            response = requests.post(self.target_url, headers=self.HEADERS,
                                     proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy},
                                     timeout=15, data=data)
            logger.info('Successfully POST response through proxy')
            return response
        except:  # some errors with sending
            try:
                logger.debug("Send POST through another proxy")
                return self._send_post_request(next(self.proxy_generator_instance), data)
            except StopIteration:
                logger.warning('No available proxies found in POST, sending through my ip')
                resp = requests.post(self.target_url, headers=self.HEADERS, data=data)
                logger.warning('Successfully sent POST through my ip')
                return resp

    def _update_proxies(self):
        thread = Thread(target=self._get_working_proxy)
        thread.start()
        while self.first_available_proxy is None:
            time.sleep(0.01)
        logger.info('Proxies are updated successfully')

    def get(self, target_url, params=None):
        self.target_url = target_url
        if len(self.available_proxies) == 0:
            self._update_proxies()
        response = self._send_get_request(self.first_available_proxy, params)
        # with open('index.html', 'w', encoding='utf-8') as file:
        #     file.write(response.text)
        # print('Successfully scraped html')
        return response

    def post(self, target_url, data=None):
        self.target_url = target_url
        if len(self.available_proxies) == 0:
            self._update_proxies()
        response = self._send_post_request(self.first_available_proxy, data)
        return response

    def get_working_proxies(self) -> list[str]:
        thread = Thread(target=self._get_working_proxy, daemon=True)
        thread.start()
        return self.available_proxies  # , self.end_of_getting_proxies


if __name__ == '__main__':
    sender = Sender()
    print(sender.get("https://httpbin.org/ip").json())
