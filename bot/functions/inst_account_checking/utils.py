import random

import aiohttp
import pytz
from aiohttp import ClientSession

kyiv_tz = pytz.timezone('Europe/Kiev')


def get_random_useragent():
    with open('bot/functions/inst_account_checking/useragents.txt', 'r') as file:
        user_agents = file.readlines()
        if user_agents:
            return random.choice(user_agents).strip()
        else:
            return False


def get_headers():
    return {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': 'https://www.instagram.com/explore/search/',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.205", "Chromium";v="131.0.6778.205", "Not_A Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-model': '"Pixel 5"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-platform-version': '"13"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': get_random_useragent(),
        'x-asbd-id': '129477',
        'x-csrftoken': 'FzZs8PooPFgnNWqYcwwpcRQby1AxBovT',
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': 'hmac.AR1LfouFeN4n8qMOhlTVq8JQxUIFvbX0fsm0aausINi9pJYc',
        'x-requested-with': 'XMLHttpRequest',
        'x-web-session-id': '9tc2qs:2klo5l:tu9zpg',
    }


async def get_insta_api(session: ClientSession, params: dict, test_cookies: dict):
    try:
        url = 'https://www.instagram.com/api/v1/web/search/topsearch/'
        async with session.get(url, params=params, cookies=test_cookies, headers=get_headers(), ssl=False) as response:
            if response.status == 200:
                return await response.json()  # Повертаємо JSON відповідь
            else:
                return None
    except:
        return None
