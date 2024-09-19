import yt_dlp
import os

class TooLongVideoError(Exception):
    pass

def _length_check(info):
    duration = info.get('duration')
    if duration and duration > 600:
        raise TooLongVideoError(f"Video duration is too long: {duration} seconds")


def _download_video(ydl_opts, video_url):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # pre_info = ydl.extract_info(video_url, download=False)
            # print(pre_info)
            # _length_check(pre_info)

            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Video successfully downloaded: {filename}")
            return filename

    except Exception as e:
        print(f"Error downloading video: {str(e)}")


def download_tiktok(video_url, save_path='download_videos'):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),
        'format': 'best',
    }

    return _download_video(ydl_opts, video_url)

# def download_youtube(video_url, save_path='download_videos'):
#     if not os.path.exists(save_path):
#         os.makedirs(save_path)
#
#     ydl_opts = {
#         'outtmpl': os.path.join(save_path, '%(id)s.%(xt)s'),
#         # 'listformats': True,
#         # 'format': 'bestvideo[filesize<45M][height<=1080]+bestaudio[ext=m4a]',
#         'format': 'bestvideo',
#         'merge_output_format': 'mp4',  # Optional: specify the output format if you want to merge into mp4
#
#         # 'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
#         # 'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/mp4+best[height<=480]',
#         'noplaylist': True,
#     }
#
#     return _download_video(ydl_opts, video_url)
#
# url = 'https://www.youtube.com/watch?v=N95BMXeUJkk&list=RDN95BMXeUJkk&start_radio=1'
# # url = 'https://www.youtube.com/watch?v=nTlYxaKNqcM'
#
# download_youtube(url)