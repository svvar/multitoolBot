import pyktok
import os

pyktok.specify_browser('chrome')


def save_tiktok_video(video_url):
    res = pyktok.save_tiktok(video_url, save_video=True, return_fns=True)
    return os.path.join(os.curdir, res['video_fn'])

