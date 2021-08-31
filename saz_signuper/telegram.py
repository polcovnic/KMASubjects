import re
import requests
from pyrogram import Client
from pyrogram import filters
from saz_signuper.signuper import Signuper

# userbot
app = Client('polcovnic', phone_number='+380957441355')


def start(signuper: Signuper):
    @app.on_message(filters.chat('@telebot_ch'))
    def from_saz(client, message):
        if re.search('Поточний етап у САЗ', message.text) is not None:
            signuper.execute()
            requests.post()
    app.run()
