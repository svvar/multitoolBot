import aiohttp
import asyncio
import re

from aiohttp_socks import ProxyConnector
from bot.core import config


def extract_links(message: str) -> list:
    fb_url_pattern = r'(https?://(?:\w+\.)?facebook\.com/\S+|www\.(?:\w+\.)?facebook\.com/\S+|\b\d{13,16}\b)'
    return re.findall(fb_url_pattern, message)


async def check_urls(urls: list[str]):
    proxy_url = f"{config.PROXY_PROTOCOL}://{config.PROXY_USERNAME}:{config.PROXY_PASSWORD}@{config.PROXY_HOST}:{config.PROXY_PORT}"
    socks_connector = ProxyConnector.from_url(proxy_url)

    async with aiohttp.ClientSession() as session:
        tasks = [_check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    active = [url for url, status in results if status == 'active']
    blocked = [url for url, status in results if status == 'blocked']
    errors = [url for url, status in results if status == 'error']

    return active, blocked, errors


async def _check_url(session, url):
    try:
        if url.isnumeric():
            full_url = f"https://www.facebook.com/profile.php?id={url}"
        else:
            full_url = url
        async with session.head(full_url, ssl=False) as response:
            if 'Vary' not in response.headers:
                # print(f"{url} - Активний")
                return (url, 'active')
            else:
                # print(f"{url} - Заблокований")
                return (url, 'blocked')
    except Exception as e:
        # print(f"{url} - Error: {str(e)}")
        return (url, 'error')


# if __name__ == '__main__':
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(main())

    # msg = '232edcdhttps://mbasic.facebook.com/profile.php?id=61561485478909,61561485478909'
    # print(extract_links(msg))