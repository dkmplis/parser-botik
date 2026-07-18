import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / 'data' / 'user-config.json'
ALLOWED_USER_PATH = BASE_DIR / 'data' / 'allowed_user.json'
BOT_TOKEN = os.getenv('BOT_TOKEN')

HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'undefined',
    'content-type': 'application/json',
    'origin': 'https://www.kufar.by',
    'priority': 'u=1, i',
    'referer': 'https://www.kufar.by/',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'x-searchid': '2f6451a4-be31-4b35-8faa-23bc2a897df1',
    'x-segmentation': 'routing=web_generalist;platform=web;application=ad_view;taxonomy-version=2',
}

PARAMS = {
    'cmp': '0',
    'lang': 'ru',
    'ot': '1',
    'rgn': '7',
    'size': '20',
    'sort': 'lst.d'
}

KUFAR_URL = 'https://api.kufar.by/search-api/v2/search/rendered-paginated'


KUFAR_IMAGE_URL = 'https://rms6.kufar.by/v1/list_thumbs_2x/'

HEADERS_FOR_IMAGE = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'Referer': 'https://www.kufar.by/',
}
