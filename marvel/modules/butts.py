from telegram import ChatAction
import html
import urllib.request
import re
import json
from typing import Optional, List
import time
import urllib
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote_plus, urlencode
import requests
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from marvel.modules.helper_funcs.filters import CustomFilters
from marvel import dispatcher
from marvel.__main__ import STATS, USER_INFO


def butts(bot: Bot, update: Update):
    nsfw = requests.get('http://api.obutts.ru/noise/1').json()[0]["preview"]
    final = "http://media.obutts.ru/{}".format(nsfw)
    update.message.reply_photo(final)
		
__help__ = """
 - * Only For Sudos Now *
 - /boobs: Sends Random Boobs pic.
 - /butts: Sends Random Butts pic.
"""
__mod_name__ = "NSFW"
BUTTS_HANDLER = CommandHandler("butts", butts, filters=CustomFilters.sudo_filter)
dispatcher.add_handler(BUTTS_HANDLER)
