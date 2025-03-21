import os
import random
import cv2
import numpy as np

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


class FaceDetector:
    def __init__(self, model_path, config_path):
        self.model_path = model_path
        self.config_path = config_path
        self.net = cv2.dnn.readNetFromTensorflow(self.model_path, self.config_path)

    def detect_and_save_face(self, input_image_path, output_image_path):
        try:
            image = cv2.imread(input_image_path)
            height, width = image.shape[:2]
        except Exception as e:
            print('Во время чтения изображения возникло исключение: %s.' % e)

        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123], False, False)
        self.net.setInput(blob)
        detections = self.net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                x_start, y_start, x_end, y_end = box.astype(int)

                context = 100
                x_context = max(0, x_start - context)
                y_context = max(0, y_start - context)
                w_context = min(width - x_context, x_end - x_start + 2 * context)
                h_context = min(height - y_context, y_end - y_start + 2 * context)
                face_context = image[y_context:y_context + h_context, x_context:x_context + w_context]
                cv2.imwrite(output_image_path, face_context)

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


def detect_face(image_path):
    try:
        face_detector_instance = FaceDetector(model_path='assets/models/opencv_face_detector_uint8.pb',
                                              config_path='assets/models/opencv_face_detector.pbtxt')
        face_detector_instance.detect_and_save_face(image_path, image_path)
        return True
    except Exception as e:
        return False



def generate_document(account, face_image_path, result_path, grey=False, add_metadata=False):
    try:
        template_interactor = TemplateInteractor('assets/fonts/Montserrat-Medium.ttf',
                                                 'assets/fonts/Montserrat-Bold.ttf', 36,
                                                 'assets/template-nobg.png')
        template_interactor.write_name(account.name)
        template_interactor.write_surname(account.surname)
        template_interactor.write_birthdate('%s.%s.%s' % (account.dayOfBirth if int(account.dayOfBirth) >= 10 else '0' + str(account.dayOfBirth), (account.monthOfBirth if int(account.monthOfBirth) >= 10 else '0' + str(account.monthOfBirth)), (account.yearOfBirth)))
        just_face_path = f'assets/temp/face{account.name}{account.surname}.png'
        template_interactor.insert_photo(face_image_path, just_face_path, grey=grey)
        random_bg = 'assets/backgrounds/' + random.choice(os.listdir('assets/backgrounds'))
        template_interactor.change_result_background(random_bg)
        template_interactor.save_image_jpg(result_path)
        os.remove(just_face_path)

        if add_metadata:
            add_random_metadata(result_path)

        return True
    except Exception as e:
        print(e)
        return False
