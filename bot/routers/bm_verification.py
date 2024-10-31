import asyncio
import uuid
import random
from concurrent.futures import ThreadPoolExecutor

from faker import Faker
from aiogram import types, Router, F
from aiogram.utils.i18n import lazy_gettext as __, gettext as _

from bot.core.storage.company_storage import get_random_company
from bot.functions import svidotstvo_writer

bm_verification_router = Router()
bm_semaphore = asyncio.Semaphore(3)

fake = Faker(locale='uk_UA')


@bm_verification_router.message(F.text == __('📝 Верифікація БМ (укр.)'))
async def bm_verification(message: types.Message):
    await message.answer(_('⏳ Зачекайте, генерується фото...'))

    company = await get_random_company()
    notary = f'{fake.last_name()} {fake.first_name()[0]}.{fake.middle_name()[0]}.'
    number = str(fake.random_int(123456, 999999))
    ua_alphabet_short = 'АБВГДЕЖЗКЛМНОПРСТУХЦЧШЮЯ'
    series = random.choice(ua_alphabet_short) + random.choice(ua_alphabet_short)

    async with bm_semaphore:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            args = [company.name, company.edrpou, company.address, company.registrator, company.registration_date, notary, series, number]
            document_buffered = await loop.run_in_executor(executor, svidotstvo_writer.draw_svidotstvo, *args)

    input_doc = types.BufferedInputFile(document_buffered.getvalue(), filename=f'{uuid.uuid4()}.jpg')
    caption = f'{company.name}\n{company.address}'

    await message.answer_document(input_doc, caption=caption)




