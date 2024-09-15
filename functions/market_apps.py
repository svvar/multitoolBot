import re

async def get_app_name(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            text = await response.text()
            res = re.search(r'<h1.*itemprop="name".*>(.*)</h1>', text)
            app_name = res.group(1)
            return app_name
        else:
            return False


async def check_app(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return True
        else:
            return False

