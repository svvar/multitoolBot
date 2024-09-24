from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import requests
import re
import os

options = Options()
options.add_argument('--headless=new')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--remote-debugging-port=9222")


def save_tiktok_video(video_url, download_folder):
    driver = webdriver.Chrome(options=options)
    driver.get(video_url)
    video = driver.find_element(By.TAG_NAME, 'video')
    src = video.get_attribute('src')

    cookies = driver.get_cookies()
    driver.quit()

    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    response = session.get(src, stream=True)

    if response.status_code != 200:
        return None

    url_regex = '(?<=\.com/)(.+?)(?=\?|$)'
    regex_url = re.findall(url_regex, video_url)[0]
    video_fn = regex_url.replace('/', '_') + '.mp4'

    max_size_bytes = 1024 * 1024 * 47

    with open(os.path.join(download_folder, video_fn), 'wb') as f:
        downloaded_bytes = 0
        for chunk in response.iter_content(chunk_size=1024):
            if downloaded_bytes >= max_size_bytes:
                break
            if chunk:
                f.write(chunk)
                downloaded_bytes += 1024
        print('Downloaded')
    return os.path.join(download_folder, video_fn)

