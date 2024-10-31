from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import numpy
import io
import cv2
import random
import asyncio
import time
import zipfile
import pilgram

class ImageTask:
    def __init__(self, image_name, border_width = None, hue_value = None, sharpness_value = None, contrast_value = None,
                brightness_value = None, saturation_value = None, noise_value = None, overlaying_texture_opacity = None,
                rotating_angle = None, resize_percentage = None, quality_value = None, instagram_filter = None, uniquification_type = None,
                number_of_copies = None):
        # self.user_id = user_id
        self.image_name = image_name
        self.uniquification_type = uniquification_type
        self.border_width = random.choice([0, random.randint(1, 5)]) if border_width is None else border_width
        self.hue_value =  random.randint(1, 5) / 100 if hue_value is None else hue_value
        self.sharpness_value =  random.randint(101, 105) / 100 if sharpness_value is None else sharpness_value
        self.contrast_value = random.randint(101, 108) / 100 if contrast_value is None else contrast_value
        self.brightness_value = random.randint(101, 108) / 100 if brightness_value is None else brightness_value
        self.saturation_value = random.randint(101, 108) / 100 if saturation_value is None else saturation_value
        self.noise_value = random.choice([0, 0.25]) if noise_value is None else noise_value
        self.overlaying_texture_opacity = random.randint(0, 3) / 10 if overlaying_texture_opacity is None else overlaying_texture_opacity
        self.rotating_angle = random.choice([0, random.uniform(-0.8, 0.8)]) if rotating_angle is None else rotating_angle
        self.resize_percentage = random.choice([percentage for percentage in range(97, 103) if percentage != 100]) / 100 if resize_percentage is None else resize_percentage
        self.quality_value = random.randint(70, 100) if quality_value is None else quality_value
        self.number_of_copies = number_of_copies
        self.instagram_filter = random.choice([0, random.choice([pilgram._1977, pilgram.aden, pilgram.brannan, pilgram.brooklyn, 
                                               pilgram.clarendon, pilgram.earlybird, pilgram.gingham, pilgram.hudson, 
                                               pilgram.kelvin, pilgram.lark, pilgram.lofi, pilgram.maven, pilgram.mayfair, 
                                               pilgram.nashville, pilgram.perpetua, pilgram.reyes, pilgram.rise, pilgram.slumber, 
                                               pilgram.stinson, pilgram.toaster, pilgram.valencia, pilgram.walden, pilgram.xpro2])]) if instagram_filter is None else instagram_filter
class ImageUniqueizer:
    def __init__(self):
        pass

    def change_image_hue(self, image, hue_value):
        image_array = numpy.array(image.convert('HSV'))
        direction = numpy.random.choice([-1, 1])
        image_array[:, :, 0] = (image_array[:, :, 0] + (direction * hue_value * 180)) % 180
        image = Image.fromarray(image_array, 'HSV').convert('RGB')
        return image
    
    def add_noise_to_image(self, image, noise_value):
        image = numpy.array(image)
        noise = numpy.random.normal(scale=noise_value, size=image.shape).astype(numpy.uint8)
        image = numpy.clip(image + noise, 0, 255).astype(numpy.uint8)
        return Image.fromarray(image)

    def rotate_image(self, image, rotating_angle):
        image = image.rotate(rotating_angle, fillcolor = tuple(random.choices(range(256), k=3)))
        return image
        
    def change_image_saturation(self, image, saturation_value):
        image = ImageEnhance.Color(image)
        image = image.enhance(saturation_value)
        return image

    def change_image_brightness(self, image, brightness_value):
        image = ImageEnhance.Brightness(image)
        image = image.enhance(brightness_value)
        return image

    def change_image_sharpness(self, image, sharpness_value):
        image = ImageEnhance.Sharpness(image)
        image = image.enhance(sharpness_value)
        return image

    def change_image_contrast(self, image, contrast_value):
        image = ImageEnhance.Contrast(image)
        image = image.enhance(contrast_value)
        return image
    
    def apply_instagram_filter_to_image(self, image, instagram_filter):
        image = instagram_filter(image)
        return image

    def add_overlaying_texture_to_image(self, image, overlaying_texture_opacity):
        overlaying_texture = Image.open('textures/{texture_number}.png'.format(texture_number = random.randint(1, 50)))
        overlaying_texture = overlaying_texture.resize(image.size)
        overlaying_texture = overlaying_texture.convert('RGBA')

        overlay_background = Image.new('RGBA', image.size, (255, 255, 255, 0))
        overlaying_texture = Image.blend(overlay_background, overlaying_texture, overlaying_texture_opacity)
        
        return Image.alpha_composite(image.convert('RGBA'), overlaying_texture)

    def add_border_to_image(self, image, border_width):
        border_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        image = ImageOps.expand(image, border=border_width, fill=border_color)
        return image


    def make_image_unique(self, image_task):
        image = Image.open(image_task.image_name)
        
        if image_task.saturation_value:
            image = self.change_image_saturation(image, image_task.saturation_value)
        
        if image_task.brightness_value:
            image = self.change_image_brightness(image, image_task.brightness_value)
        
        if image_task.contrast_value:
            image = self.change_image_contrast(image, image_task.contrast_value)

        #if image_task.instagram_filter:
        #    image = self.apply_instagram_filter_to_image(image, image_task.instagram_filter)

        #if image_task.overlaying_texture_opacity:
        #    image = self.add_overlaying_texture_to_image(image, image_task.overlaying_texture_opacity)

        #if image_task.border_width:
        #    image = self.add_border_to_image(image, image_task.border_width)

        if image_task.rotating_angle:
            image = self.rotate_image(image, image_task.rotating_angle)

        if image_task.noise_value:
            image = self.add_noise_to_image(image, image_task.noise_value)

        #image = self.change_image_hue(image, image_task.hue_value)

        if image_task.sharpness_value:
            image = self.change_image_sharpness(image, image_task.sharpness_value) 

        if image_task.resize_percentage:
            image = image.resize((int(image.width * image_task.resize_percentage), int(image.height * image_task.resize_percentage)), Image.BICUBIC)

        image_stream = io.BytesIO()
        
        if image_task.quality_value:
            image.convert('RGB').save(image_stream, format = 'JPEG', quality = image_task.quality_value)
            image_stream.seek(0)
        else:
            image.convert('RGB').save(image_stream, format = 'JPEG', quality = 100)
            image_stream.seek(0)

        return image_stream


def get_size(file):
    file.seek(0, io.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def unique_img_generator(photo_path, n_copies=10):
    unique_images = []
    uniquizer = ImageUniqueizer()
    photo_name = f'photo_{time.strftime("%H%M%S", time.gmtime())}'

    max_zip_size = 50 * 1024 * 1024 - 256
    curr_size = 0

    for _ in range(n_copies):
        image_task = ImageTask(image_name=photo_path, uniquification_type = 'random')
        unique_image = uniquizer.make_image_unique(image_task)
        size = get_size(unique_image)
        if curr_size + size > max_zip_size:
            break

        unique_images.append(unique_image)
        curr_size += size

    zip_buffer = io.BytesIO()
    zip_buffer.name = f'{photo_name}_unique.zip'

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:
        for i, image in enumerate(unique_images):
            image_name = f'{photo_name}_uq{i+1}.jpg'
            zip_file.writestr(image_name, image.getvalue())

    zip_buffer.seek(0)
    return zip_buffer

