from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.core.storage.usage_stats_storage import update_usage_stats


class UsageData:
    def __init__(self):
        self.fb_acc_check = 0
        self.two_fa = 0
        self.tiktok_downloader = 0
        self.play_apps_check = 0
        self.id_generator = 0
        self.unique_media = 0
        self.selfie_generator = 0
        self.fb_business_verification = 0
        self.tiktok_verification = 0
        self.text_rewrite = 0
        self.password_generator = 0
        self.name_generator = 0
        self.fan_page_name_generator = 0
        self.fan_page_address_generator = 0
        self.fan_page_phone_generator = 0
        self.fan_page_quote_generator = 0
        self.fan_page_all_generator = 0

    def reset(self):
        self.fb_acc_check = 0
        self.two_fa = 0
        self.tiktok_downloader = 0
        self.play_apps_check = 0
        self.id_generator = 0
        self.unique_media = 0
        self.selfie_generator = 0
        self.fb_business_verification = 0
        self.tiktok_verification = 0
        self.text_rewrite = 0
        self.password_generator = 0
        self.name_generator = 0
        self.fan_page_name_generator = 0
        self.fan_page_address_generator = 0
        self.fan_page_phone_generator = 0
        self.fan_page_quote_generator = 0
        self.fan_page_all_generator = 0


usage = UsageData()


async def dump_statistics_task():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(dump_statistics, 'interval', hours=1)
    scheduler.start()


async def dump_statistics():
    global usage
    usage_snapshot = {key: value for key, value in usage.__dict__.items() if not key.startswith('__') and value != 0}
    await update_usage_stats(usage_snapshot)
    usage.reset()



