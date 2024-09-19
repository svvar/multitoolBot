import os
import random

from .random_metadata import add_random_metadata
from PIL import Image, ImageDraw, ImageFont
from rembg import remove

class Account:
    def __init__(self, name, surname, dayOfBirth, monthOfBirth, yearOfBirth):
        self.name = name
        self.surname = surname
        self.dayOfBirth = dayOfBirth
        self.monthOfBirth = monthOfBirth
        self.yearOfBirth = yearOfBirth


class TemplateInteractor:
    def __init__(self, medium_font_path, bold_font_path, font_size, template_image_path):
        self.medium_font_path = medium_font_path
        self.bold_font = ImageFont.truetype(bold_font_path, font_size)
        self.medium_font = ImageFont.truetype(medium_font_path, font_size)
        self.template_image = Image.open(template_image_path)
        self.draw = ImageDraw.Draw(self.template_image)

    def write_name(self, name):
        self.draw.text((898, 340), 'ИМЯ', font=self.bold_font, fill=(0, 0, 0))
        self.draw.text((898, 385), name, font=self.medium_font, fill=(0, 0, 0))

    def write_surname(self, surname):
        self.draw.text((898, 485), 'ФАМИЛИЯ', font=self.bold_font, fill=(0, 0, 0))
        self.draw.text((898, 527), surname, font=self.medium_font, fill=(0, 0, 0))

    def write_birthdate(self, birthdate):
        self.draw.text((898, 637), 'ГОД РОЖДЕНИЯ', font=self.bold_font, fill=(0, 0, 0))
        self.draw.text((898, 688), birthdate, font=self.medium_font, fill=(0, 0, 0))

    def crop_to_content(self, image):
        gray = image.convert('L')
        binary = gray.point(lambda x: 0 if x == 0 else 255, '1')

        bbox = binary.getbbox()

        if bbox:
            cropped_image = image.crop(bbox)
            return cropped_image
        else:
            return image

    def remove_photo_background(self, photo_to_paste_path, just_face_path):
        photo_to_paste = Image.open(photo_to_paste_path)
        photo_to_paste_without_background = remove(photo_to_paste)
        photo_to_paste_without_background = self.crop_to_content(photo_to_paste_without_background)
        photo_to_paste_without_background.save(just_face_path)
        return just_face_path



    def insert_photo(self, photo_path, just_face_path, grey=False):
        face = Image.open(self.remove_photo_background(photo_path, just_face_path))

        if grey:
            face = face.convert('LA')

        polygon_coordinates = [(543, 366), (825, 365), (825, 732), (543, 730)]

        left = min(polygon_coordinates, key=lambda x: x[0])[0]
        top = min(polygon_coordinates, key=lambda x: x[1])[1]
        right = max(polygon_coordinates, key=lambda x: x[0])[0]
        bottom = max(polygon_coordinates, key=lambda x: x[1])[1]

        width = right - left
        height = bottom - top
        new_width = width
        new_height = int(face.height * (new_width / face.width))

        photo_to_paste_resized = face.resize((new_width, new_height))

        self.template_image.paste(photo_to_paste_resized, (left, bottom - new_height), photo_to_paste_resized)

    def change_result_background(self, background_path):
        id_image = self.template_image

        background_image = Image.open(background_path)
        background_image = background_image.resize(id_image.size)
        background_image.paste(id_image, (0, 0), id_image)

        self.template_image = background_image

    def save_image_jpg(self, output_path):

        self.template_image.convert("RGB").save(output_path)


def generate_document(account, face_image_path, result_path, grey=False, add_metadata=False):
    try:
        template_interactor = TemplateInteractor('fonts/Montserrat-Medium.ttf',
                                                 'fonts/Montserrat-Bold.ttf', 36,
                                                 'faces/template-nobg.png')
        template_interactor.write_name(account.name)
        template_interactor.write_surname(account.surname)
        template_interactor.write_birthdate('%s.%s.%s' % (account.dayOfBirth if int(account.dayOfBirth) >= 10 else '0' + str(account.dayOfBirth), (account.monthOfBirth if int(account.monthOfBirth) >= 10 else '0' + str(account.monthOfBirth)), (account.yearOfBirth)))
        just_face_path = f'faces/temp/face{account.name}{account.surname}.png'
        template_interactor.insert_photo(face_image_path, just_face_path, grey=grey)
        random_bg = 'faces/backgrounds/' + random.choice(os.listdir('faces/backgrounds'))
        template_interactor.change_result_background(random_bg)
        template_interactor.save_image_jpg(result_path)
        os.remove(just_face_path)

        if add_metadata:
            add_random_metadata(result_path)
    except Exception as e:
        print(e)
