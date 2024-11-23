import io
import zipfile
import os
import time
import random
import subprocess

class VideoTask:
    def __init__(self, video_name, speed_value = None, brightness_value = None,
                 contrast_value = None, saturation_value = None, rotating_angle = None,
                 overlaying_texture_opacity = None, noise_value = None,
                 resize_percentage = None, hue_value = None, uniquification_type = None):
        self.video_name = video_name
        self.speed_value = random.randint(90, 110) if speed_value is None else speed_value
        self.brightness_value = random.uniform(-1, 1) / 10 if brightness_value is None else brightness_value
        self.contrast_value = random.randint(101, 104) / 100 if contrast_value is None else contrast_value
        self.saturation_value = random.randint(101, 104) / 100 if saturation_value is None else saturation_value
        self.rotating_angle = random.choice([0, random.uniform(-0.8, 0.8)]) if rotating_angle is None else rotating_angle
        self.overlaying_texture_opacity = random.randint(0, 3) / 10 if overlaying_texture_opacity is None else overlaying_texture_opacity
        self.noise_value = random.choice([0, random.randint(1, 4)]) if noise_value is None else noise_value
        self.hue_value = random.randint(0, 15) if hue_value is None else hue_value
        self.resize_percentage = random.choice([percentage for percentage in range(86, 100) if percentage != 100]) / 100 if resize_percentage is None else resize_percentage
        self.uniquification_type = uniquification_type



def apply_all_modifications(video_task, output_video_path):
    input_video = video_task.video_name

    vf = (f'eq=brightness={video_task.brightness_value}:contrast={video_task.contrast_value}:'
          f'saturation={video_task.saturation_value}:gamma=1.2:gamma_r=1.0:gamma_g=1.0:gamma_b=1.0, '
          f'rotate={video_task.rotating_angle}*PI/180, '
          f'noise=alls={video_task.noise_value}:allf=t, '
          f'hue=h={video_task.hue_value}, '
          f'scale=trunc(iw*{video_task.resize_percentage}/2)*2:trunc(ih*{video_task.resize_percentage}/2)*2, '
          f'setpts={100/video_task.speed_value}*PTS')

    af = f'atempo={video_task.speed_value/100}'

    ffmpeg_command = [
        'ffmpeg',
        '-y',
        '-i', input_video,
        '-vf', vf,
        '-af', af,
        '-map_metadata', '-1',
        output_video_path
    ]

    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    process.wait()

    if stderr:
        print("FFmpeg encountered an error:")
        print(stderr.decode('utf-8'))


def get_file_size(file_path):
    return os.path.getsize(file_path)

def unique_video_generator(video_path: str, n_copies=5):
    unique_videos = []
    video_name = f'video_{time.strftime("%H%M%S", time.gmtime())}'

    max_zip_size = 50 * 1024 * 1024 - 256
    curr_size = 0

    for i in range(n_copies):
        video_task = VideoTask(video_name=video_path, uniquification_type='random')
        output_video_path = os.path.join(os.path.dirname(video_path), f'{video_name}_uq_{i+1}.mp4')
        apply_all_modifications(video_task, output_video_path)

        if curr_size + get_file_size(output_video_path) > max_zip_size:
            break

        unique_videos.append(output_video_path)
        curr_size += get_file_size(output_video_path)

    zip_buffer = io.BytesIO()
    zip_buffer.name = f'{video_name}_unique.zip'
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for unique_video in unique_videos:
            zip_file.write(unique_video, os.path.basename(unique_video))
            os.remove(unique_video)

    return zip_buffer



# zip_buff = unique_video_generator('../downloads/raye.mp4', 3)
#
# with open(zip_buff.name, 'wb') as f:
#     f.write(zip_buff.getvalue())

#
# video_task = VideoTask(video_name='../downloads/raye.mp4', uniquification_type='random')
# output_video_name = '../downloads/raye_unique.mp4'
# unique_video = apply_all_modifications(video_task, output_video_name)
# print(unique_video)








    # async def process_tasks(self):
    #     while True:
    #         try:
    #             video_task = await self.queue.get()
    #             await self.bot.send_message(279358659, text='video task started ' + video_task.video_name)
    #             start_time = time.time()
    #             print(video_task)
    #             print(vars(video_task))
    #             loop = asyncio.get_event_loop()
    #             temp_folder_name = await utilities.asynchronous_make_n_video_copies(video_task)
    #             unique_videos = []
    #             for uniquification in range(video_task.copies_number):
    #                 current_video_task = VideoTask(
    #                     user_id=video_task.user_id,
    #                     video_name=temp_folder_name + '/' + video_task.video_name.split('/')[3][:-4] + '_' + str(uniquification + 1) + '.mp4',
    #                     uniquification_type='random'
    #                 )
    #
    #                 unique_video = await loop.run_in_executor(None, self.make_video_unique_experimental, current_video_task)
    #                 unique_videos.append(unique_video)
    #
    #             print(video_task.video_name)
    #             zip_filename = video_task.video_name[:-4] + '.zip'
    #             zip_file_to_send = await utilities.asynchronous_get_zip_file_from_video_paths(unique_videos, zip_filename)
    #             await self.bot.send_document(video_task.user_id, zip_file_to_send)
    #             await self.bot.send_message(video_task.user_id, text='Ваше видео успешно уникализировано.', reply_markup=keyboards.random_video_uniquification_finished_menu)
    #             end_time = time.time()
    #             execution_time = end_time - start_time
    #             print("Execution time:", execution_time, "seconds")
    #             await utilities.asynchronous_remove_folder(temp_folder_name)
    #             current_ads_message = await Database.get_current_ads_message()
    #             if current_ads_message is not None and current_ads_message.is_active_ads_message:
    #                 try:
    #                     await current_ads_message.send_message_to_single_user(video_task.user_id, self.bot)
    #                 except Exception as e:
    #                     pass
    #             await utilities.asynchronous_delete_file(zip_filename)
    #             await self.bot.send_message(279358659, text='video task finished ' + video_task.video_name)
    #         except Exception as e:
    #             if 'File too large for uploading' in str(e):
    #                 await self.bot.send_message(
    #                     video_task.user_id,
    #                     text='⚠️ Результат уникализации превысил 50 мб, пожалуйста, попробуйте сжать видео и отправить его снова, чтобы получить результат архивом.'
    #                          'Вы можете сделать это <a href=\'https://www.veed.io/ru-RU/инструменты/видео-компрессор\'>тут</a>.',
    #                     parse_mode = types.ParseMode.HTML,
    #                     reply_markup = keyboards.random_uniquification_finished_menu
    #                 )
    #                 await self.bot.send_message(
    #                     video_task.user_id,
    #                     text='Так как результат уникализации превысил 50 мб, видеофайлы будут отправлены по одному:'
    #                 )
    #
    #                 async for unique_video in utilities.generator_from_list(unique_videos):
    #                     async with aiofiles.open(unique_video, 'rb') as video_file:
    #                         video_bytes = await video_file.read()
    #
    #                     await self.bot.send_document(video_task.user_id, types.InputFile(io.BytesIO(video_bytes), filename=unique_video.split('/')[3]))
    #
    #                 await self.bot.send_message(video_task.user_id, text='Ваше видео успешно уникализировано.',
    #                                             reply_markup=keyboards.random_video_uniquification_finished_menu)
    #
    #                 await utilities.asynchronous_remove_folder(temp_folder_name)
    #                 current_ads_message = await Database.get_current_ads_message()
    #                 if current_ads_message is not None and current_ads_message.is_active_ads_message:
    #                     try:
    #                         await current_ads_message.send_message_to_single_user(video_task.user_id, self.bot)
    #                     except Exception as e:
    #                         pass
    #                 await utilities.asynchronous_delete_file(zip_filename)
    #                 await self.bot.send_message(279358659, text='video task finished ' + video_task.video_name)
    #
    #             await self.bot.send_message(279358659, text='video task error ' + video_task.video_name)
    #             await self.bot.send_message(279358659, text=e)
    #
    #         self.queue.task_done()
            #!!!DELETE TEMPORARY FOLDERS / FILES

