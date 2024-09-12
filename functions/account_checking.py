import aiohttp
import asyncio
import re


# def read_file(file_path: str) -> list:


def extract_links(message: str) -> list:
    fb_url_pattern = r'(https?://(?:\w+\.)?facebook\.com/\S+|www\.(?:\w+\.)?facebook\.com/\S+)'
    return re.findall(fb_url_pattern, message)


async def check_urls(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [_check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    active = [url for url, status in results if status == 'active']
    blocked = [url for url, status in results if status == 'blocked']
    errors = [url for url, status in results if status == 'error']

    return active, blocked, errors


async def _check_url(session, url):
    try:
        async with session.head(url) as response:
            if 'Vary' not in response.headers:
                # print(f"{url} - Активний")
                return (url, 'active')
            else:
                # print(f"{url} - Заблокований")
                return (url, 'blocked')
    except Exception as e:
        # print(f"{url} - Error: {str(e)}")
        return (url, 'error')


if __name__ == '__main__':
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(main())

    msg = '232edcdhttps://mbasic.facebook.com/profile.php?id=61561485478909,61561485478909'
    print(extract_links(msg))