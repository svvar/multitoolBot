import re
import time

from sqlalchemy import Column, Integer, Text, create_engine, select, delete, update, insert
from sqlalchemy.orm import declarative_base, sessionmaker

from selenium import webdriver
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


from bs4 import BeautifulSoup


Base = declarative_base()
engine = create_engine('sqlite:///quotes.sqlite')
# sync_engine = create_engine('sqlite:///../quotes.sqlite')

session = sessionmaker(bind=engine)

class UAQuotes(Base):
    __tablename__ = 'ua_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)

class RUQuotes(Base):
    __tablename__ = 'ru_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)

class ENQuotes(Base):
    __tablename__ = 'en_quotes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote = Column(Text)


# def cleanup_long_quotes():
#     with session() as s:
#         for table in [UAQuotes, RUQuotes, ENQuotes]:
#             quotes = s.execute(select(table)).scalars().all()
#             for quote in quotes:
#                 if quote.quote is None:
#                     s.execute(delete(table).where(table.id == quote.id))
#                 elif len(quote.quote) > 110:
#                     s.execute(delete(table).where(table.id == quote.id))
#
#         s.commit()
#
#
# cleanup_long_quotes()

def get_all_quotes():
    with session() as s:
        ua_quotes = s.execute(select(UAQuotes.quote)).scalars().all()


        return ua_quotes

def insert_quote(quote):
    with session() as s:
        s.execute(insert(UAQuotes).values(quote=quote))
        s.commit()


# driver = webdriver.Chrome()
#
# driver.get('https://generator-online.com/uk/quote/')
#
# btn = driver.find_element(By.XPATH, '//*[@id="wrapper"]/main/section[1]/div[2]/div[2]/div[2]/button')
# btn.click()
#
# WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, 'blockquote')))
#
# time.sleep(2)
#
# # lang = driver.find_element(By.XPATH, '//*[@id="accordion-body-1"]/div/div/div[3]')
# # lang.click()
#
# all_in_db = get_all_quotes()
# already_parsed = []
#
# for i in range(600):
#     btn.click()
#     time.sleep(0.3)
#     blockquote = driver.find_element(By.TAG_NAME, 'blockquote')
#     text = blockquote.find_element(By.TAG_NAME, 'p').text
#
#     if text not in all_in_db and text not in already_parsed and len(text) < 110:
#         insert_quote(text)
#         already_parsed.append(text)
#     print(text)

already_present = get_all_quotes()

soup = BeautifulSoup(open('xx.html', encoding='utf-8'), 'html.parser')

quotes = soup.find_all('p', class_='has-large-font-size')
print(quotes)

for quote in quotes:
    srch = re.search(r'“(.*)”', quote.text)
    if srch:
        quote_text = srch.group(1)
        if quote_text not in already_present and len(quote_text) < 110:
            insert_quote(quote_text)
            print(quote_text)
