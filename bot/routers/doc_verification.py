import asyncio
import uuid
import random
from concurrent.futures import ThreadPoolExecutor

from faker import Faker
from aiogram import types, Router, F
from aiogram.utils.i18n import lazy_gettext as __, gettext as _
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.core.usage_statistics import usage
from bot.core.storage.company_storage import get_random_company, get_random_us_company
from bot.functions import docgen_writer

doc_verification_router = Router()
doc_semaphore = asyncio.Semaphore(3)

fake = Faker(locale='uk_UA')


@doc_verification_router.message(F.text == __('📝 Верифікація БМ (укр.)'))
async def bm_verification(message: types.Message):
    await message.answer(_('⏳ Зачекайте, генерується фото...'))

    company = await get_random_company()
    notary = f'{fake.last_name()} {fake.first_name()[0]}.{fake.middle_name()[0]}.'
    number = str(fake.random_int(123456, 999999))
    ua_alphabet_short = 'АБВГДЕЖЗКЛМНОПРСТУХЦЧШЮЯ'
    series = random.choice(ua_alphabet_short) + random.choice(ua_alphabet_short)

    async with doc_semaphore:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            args = [company.name, company.edrpou, company.address, company.registrator, company.registration_date, notary, series, number]
            document_buffered = await loop.run_in_executor(executor, docgen_writer.draw_svidotstvo, *args)

    input_doc = types.BufferedInputFile(document_buffered.getvalue(), filename=f'{uuid.uuid4()}.jpg')
    caption = f'{company.name}\n{company.address}'

    await message.answer_document(input_doc, caption=caption)
    # usage['fb_business_verification'] += 1
    usage.fb_business_verification += 1


@doc_verification_router.message(F.text == __('📝 Верифікація TikTok (бізнес акк.)'))
async def tiktok_verification(message: types.Message):
    await message.answer(_('⏳ Зачекайте, генерується фото...'))

    ein_prefixes = [
        '10', '12', '60', '67', '50', '53', '01', '02', '03', '04', '05', '06', '11', '13', '14', '16',
        '21', '22', '23', '25', '34', '51', '52', '54', '55', '56', '57', '58', '59', '65', '30', '32',
        '35', '36', '37', '38', '61', '15', '24', '40', '44', '94', '95', '80', '90', '33', '39', '41',
        '42', '43', '48', '62', '63', '64', '66', '68', '71', '72', '73', '74', '75', '76', '77', '82',
        '83', '84', '85', '86', '87', '88', '91', '92', '93', '98', '99', '20', '26', '27', '45', '46',
        '47', '81', '31'
    ]

    ein = random.choice(ein_prefixes) + "-" + str(fake.random_int(1000000, 9999999))
    company = await get_random_us_company()

    async with doc_semaphore:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            args = [ein, company.name, company.address]
            doc1, doc2 = await loop.run_in_executor(executor, docgen_writer.draw_us_doc, *args)

    input_doc1 = types.BufferedInputFile(doc1.getvalue(), filename=f'{uuid.uuid4()}.jpg')
    input_doc2 = types.BufferedInputFile(doc2.getvalue(), filename=f'{uuid.uuid4()}.jpg')
    caption = f'{company.name}\n{company.address}\n{company.state}'

    await message.answer_document(input_doc1, caption=caption)
    await message.answer_document(input_doc2)
    # usage['tiktok_verification'] +=
    usage.tiktok_verification += 1

    # print(usage)