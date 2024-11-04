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
    async with session.get(url, ssl=False) as response:
        if response.status == 200:
            text = await response.text()
            soup = bs4.BeautifulSoup(text, 'html.parser')
            app_name = soup.find(itemprop="name").text
            return app_name
        else:
            return False


# async def check_app(session, url):
#     async with session.get(url) as response:
#         if response.status == 200:
#             return True
#         else:
#             return False

async def check_app(session, app):
    async with session.get(app.url, ssl=False) as response:
        if response.status == 200:
            return app, True
        else:
            return app, False

