import os
import time
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def sanitize_filename(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Referer": "https://www.bershka.com/",
}

def download_file(url, base_url, download_folder, cookies=None):
    parsed_url = urlparse(url)
    if parsed_url.scheme in ['http', 'https']:
        local_path = os.path.join(download_folder, parsed_url.path.lstrip('/'))
        # local_filename = os.path.join(local_path, sanitize_filename(url))
        ensure_directory_exists(local_path)

        cookies = {cookie['name']: cookie['value'] for cookie in cookies}
        with requests.get(url, stream=True, timeout=3, headers=headers, cookies=cookies) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_path
    else:
        print(f"Skipping data URL: {url}")
        return None

def save_page_with_selenium(url, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(8)

    try:
        driver.get(url)
        cookies = driver.get_cookies()
    except TimeoutException as e:
        pass
    time.sleep(3)  # Wait for the page to load completely


    from cleaner import clean_source, clean_index
    page_source = driver.page_source
    with open(os.path.join(download_folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page_source)
    clean_index(os.path.join(download_folder, 'index.html'))

    soup = BeautifulSoup(page_source, 'html.parser')
    tags = soup.find_all(['img', 'link', 'script', 'source'])

    for tag in tags:
        asset_url = None
        if tag.name == 'img':
            src = tag.get('src')
            if src and not src.startswith('data:'):
                asset_url = urljoin(url, src)
        elif tag.name == 'link':
            if tag.get('rel') in (['stylesheet'], ['preload'], ['icon']) or os.path.basename(urlparse(tag.get('href')).path).endswith(('.ico', '.png', '.jpg', '.jpeg', '.svg')):
                href = tag.get('href')
                if href and not href.startswith('data:'):
                    asset_url = urljoin(url, href)
        elif tag.name == 'script':
            src = tag.get('src')
            if src and not src.startswith('data:'):
                asset_url = urljoin(url, src)
        elif tag.name == 'source':
            src = tag.get('srcset')
            if src and not src.startswith('data:'):
                asset_url = urljoin(url, src)

        if asset_url:
            try:
                download_file(asset_url, url, download_folder, cookies)
            except Exception as e:
                print(f"Failed to download {asset_url}: {e}")

    driver.quit()

url = 'https://habr.com/ru/articles/669766/'
url = 'https://ru-brightdata.com/blog/how-tos-ru/web-scraping-with-python'
# url = 'https://github.com/rajatomar788/pywebcopy/wiki/Classes'
# url = 'https://qna.habr.com/q/968887'
# url = 'https://www.pullandbear.com/ua/%D0%B4%D0%B6%D0%B8%D0%BD%D1%81%D0%B8-%D0%BF%D1%80%D1%8F%D0%BC%D0%BE%D0%B3%D0%BE-%D0%BA%D1%80%D0%BE%D1%8E-l07685522?pelement=621942709&cS=415'
# url = 'https://rozetka.com.ua/ua/'
# url = 'https://stackoverflow.com/questions/52142180/saving-pages-with-selenium'
url = 'https://uk.wikipedia.org/wiki/%D0%92%D0%B5%D0%B1%D1%81%D0%B0%D0%B9%D1%82'
download_folder = '../site_save2'
save_page_with_selenium(url, download_folder)

print("Download completed!")
