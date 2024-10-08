import bs4
from urllib.parse import urlparse, parse_qs



def extract_id(url):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)

    if 'id' in query:
        return query['id'][0]
    else:
        return None

async def get_app_name(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            text = await response.text()
            soup = bs4.BeautifulSoup(text, 'html.parser')
            app_name = soup.find(itemprop="name").text
            return app_name
        else:
            return False


async def check_app(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return True
        else:
            return False

# async def check_apps(session, apps: list[tuple[str, str]]):
#     results = []
#     for url, name in apps:
#         if await check_app(session, url):
#             results.append((url, name, 'active'))
#         else:
#             results.append((url, name, 'blocked'))
#     return results

# url = ('https://play.google.com/store/apps/details?id=com.supercell.clashroyale')
#
# print(extract_id(url))
