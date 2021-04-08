import logging
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

import requests
from bs4 import BeautifulSoup

# setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('sender.log')
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


class Sender:
    PROXY_LIST_URL = 'https://free-proxy-list.net/'
    PROXY_TYPE = 'elite proxy'
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    HTTP_BIN = 'https://httpbin.org/ip'
    CHROME_EXECUTABLE = 'D:/ChromeDriver/chromedriver_win32/chromedriver.exe'

    def __init__(self):
        self.target_url = None
        self.available_proxies = []
        self.first_available_proxy: str = None
        self.proxy_generator_instance = None
        self._update_proxies()

    def get_proxies(self):
        r = requests.get(self.PROXY_LIST_URL)
        soup = BeautifulSoup(r.content, 'html.parser')
        table = soup.find('tbody')
        proxies = []
        for row in table:
            if row.find_all('td')[4].text == self.PROXY_TYPE:
                proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
                proxies.append(proxy)
            else:
                pass
        return proxies

    def check_for_available_proxy(self, proxy):
        try:
            r = requests.get(self.HTTP_BIN, headers=self.HEADERS,
                             proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy}, timeout=1)
            # print(r.json(), r.status_code)
        except:
            return None
        else:
            if not self.first_available_proxy:
                self.first_available_proxy = proxy
                logger.debug('First available proxy added')
            self.available_proxies.append(proxy)
            logger.debug(f'Another one available proxy added (available proxies = {len(self.available_proxies)}')
            return proxy

    def _get_working_proxy(self):
        proxy_list = self.get_proxies()
        executor = ThreadPoolExecutor()
        for proxy in proxy_list:
            executor.submit(self.check_for_available_proxy, proxy)
        executor.shutdown()

    def _proxy_generator(self):
        for proxy in self.available_proxies:
            yield proxy

    def _send_request(self, proxy):
        try:
            if not self.proxy_generator_instance:
                self.proxy_generator_instance = self._proxy_generator()
            response = requests.get(self.target_url, headers=self.HEADERS,
                                    proxies={'http': 'http://' + proxy, 'https': 'http://' + proxy}, timeout=15)
            logger.info('Successfully get response through proxy')
            return response
        except:  # some send error
            try:
                logger.debug("Send through another proxy")
                return self._send_request(next(self.proxy_generator_instance))
            except StopIteration:
                logger.warning('No available proxies found, sending through my ip')
                resp = requests.get(self.target_url, headers=self.HEADERS)
                logger.warning('Successfully sent through my ip')
                return resp

    def _update_proxies(self):
        thread = Thread(target=self._get_working_proxy)
        thread.start()
        while self.first_available_proxy is None:
            time.sleep(0.01)

    def send(self, target_url):
        self.target_url = target_url
        if len(self.available_proxies) == 0:
            self._update_proxies()
        print(self.available_proxies)
        response = self._send_request(self.first_available_proxy)
        # with open('index.html', 'w', encoding='utf-8') as file:
        #     file.write(response.text)
        # print('Successfully scraped html')
        return response

    def get_working_proxies(self) -> list[str]:
        if len(self.available_proxies) == 0:
            thread = Thread(target=self._get_working_proxy)
            thread.start()
            while self.first_available_proxy is None:
                time.sleep(0.01)
        return self.available_proxies


if __name__ == '__main__':
    sender = Sender()
    sender.send('https://docs.python.org/3/library/concurrent.futures.html')
