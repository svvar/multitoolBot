from aiohttp import ClientSession


from .inst_db.models import Account, AccountStatus
from .utils import get_insta_api



class InstagramManager:
    def __init__(self):
        self.client_session = None
        self.cookies = None

    async def init_shared(self):
        self.client_session = ClientSession()
        self.cookies = await self.get_last_active_cookie()

    async def check_acc(self, username):
        if not self.cookies:
            return None

        params = {
            'context': 'blended',
            'include_reel': 'true',
            'query': username,  # ник проверяемого акка
            'rank_token': '0.44083207837728877',
            'search_surface': 'web_top_search',
        }
        for cookie in self.cookies:
            test_cookies = {}
            for cook in cookie:
                name = cook.get("name")
                value = cook.get("value")

                if not name or not value:
                    continue
                test_cookies[name] = str(value)

            check = await get_insta_api(self.client_session, params, test_cookies)
            if not check:
                continue
            else:
                for i in check['users']:
                    if username == i['user']['username']:
                        return True
                else:
                    return False

        else:
            return None

    @staticmethod
    async def get_last_active_cookie():
        from .inst_db.db_methods import _get_active_cookies
        where_type = Account.status == AccountStatus.ACTIVE
        cookies = await _get_active_cookies(Account, where_type)
        if cookies:
            return cookies
        else:
            return None

    @staticmethod
    async def return_value(value):
        return value