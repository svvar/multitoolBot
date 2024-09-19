from exif import (Image, ExposureProgram, LightSource, ExposureMode, Flash, FlashMode, FlashReturn, ColorSpace,
                  WhiteBalance, SceneCaptureType, Sharpness, Saturation, MeteringMode, SensingMethod, GpsAltitudeRef,
                  DATETIME_STR_FORMAT)
import random
import datetime


camera_manufacturers = {
    "Canon": ["EOS 5D Mark IV", "EOS 6D Mark II", "EOS 80D", "EOS R5", "PowerShot G7 X Mark III"],
    "Nikon": ["D850", "D750", "D5600","Z6","Coolpix P1000"],
    "Sony": ["Alpha A7 III", "Alpha A7R IV", "Alpha A6600", "RX100 VII", "Cyber-shot DSC-HX400V"],
    "Fujifilm": ["X-T3", "X-T30", "X-Pro3", "GFX 50R", "FinePix XP140"],
    "Olympus": ["OM-D E-M1 Mark III", "OM-D E-M5 Mark III", "PEN-F", "Tough TG-6", "OM-D E-M10 Mark IV"],
    "Panasonic": ["Lumix GH5", "Lumix G9", "Lumix GX85", "Lumix ZS200","Lumix FZ1000 II"],
    "Samsung": ["Galaxy S21", "Galaxy S20", "Galaxy Note 20", "Galaxy A52", "Galaxy Z Fold 3"],
    "Apple": ["iPhone 12", "iPhone 11", "iPhone XS", "iPhone 8", "iPad Pro"]
}

shutter_speed_value = [0.0005, 0.001, 0.002, 0.004, 0.008, 0.016, 0.033, 0.067, 0.125, 0.250, 0.500, 1.0]
aperture_value = [1.1, 1.5, 1.8, 2.0, 2.2, 2.8, 3.2, 4.0, 5.5, 7.0]
exif_version = ['0210', '0220', '0230', '0232']
focal_length = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
sensitivity = [100, 200, 400, 800, 1600, 3200, 6400]

exposure_program = [ExposureProgram.NORMAL_PROGRAM, ExposureProgram.MANUAL, ExposureProgram.APERTURE_PRIORITY, ExposureProgram.SHUTTER_PRIORITY]
light_source = [LightSource.UNKNOWN, LightSource.DAYLIGHT, LightSource.FLUORESCENT, LightSource.TUNGSTEN, LightSource.FLASH]
exposure_mode = [ExposureMode.AUTO_EXPOSURE, ExposureMode.MANUAL_EXPOSURE]
white_balance = [WhiteBalance.AUTO, WhiteBalance.MANUAL]
scene_capture_type = [SceneCaptureType.STANDARD, SceneCaptureType.LANDSCAPE, SceneCaptureType.PORTRAIT, SceneCaptureType.NIGHT_SCENE]
color_space = ColorSpace.SRGB
sharpness = [Sharpness.NORMAL, Sharpness.SOFT, Sharpness.HARD]
saturation = [Saturation.NORMAL, Saturation.LOW, Saturation.HIGH]
metering_mode = [MeteringMode.UNKNOWN, MeteringMode.AVERAGE, MeteringMode.SPOT, MeteringMode.MULTI_SPOT, MeteringMode.PARTIAL]
sensing_method = [SensingMethod.NOT_DEFINED, SensingMethod.ONE_CHIP_COLOR_AREA_SENSOR, SensingMethod.TWO_CHIP_COLOR_AREA_SENSOR, SensingMethod.THREE_CHIP_COLOR_AREA_SENSOR, SensingMethod.COLOR_SEQUENTIAL_AREA_SENSOR]

flashes = [Flash(flash_mode=FlashMode.COMPULSORY_FLASH_SUPPRESSION, flash_return=FlashReturn.NO_STROBE_RETURN_DETECTION_FUNCTION, flash_fired=False, flash_function_not_present=False, red_eye_reduction_supported=False, reserved=0),
             Flash(flash_mode=FlashMode.COMPULSORY_FLASH_FIRING, flash_return=FlashReturn.STROBE_RETURN_LIGHT_DETECTED, flash_fired=False, flash_function_not_present=False, red_eye_reduction_supported=True, reserved=1),
                Flash(flash_mode=FlashMode.UNKNOWN, flash_return=FlashReturn.NO_STROBE_RETURN_DETECTION_FUNCTION, flash_fired=False, flash_function_not_present=False, red_eye_reduction_supported=False, reserved=1),
                Flash(flash_mode=FlashMode.AUTO_MODE, flash_return=FlashReturn.STROBE_RETURN_LIGHT_DETECTED, flash_fired=False, flash_function_not_present=False, red_eye_reduction_supported=False, reserved=1),
]


def _gen_datetime(min_year=2020, max_year=datetime.datetime.now().year):
    start = datetime.datetime(min_year, 1, 1, 00, 00, 00)
    years = max_year - min_year + 1
    end = start + datetime.timedelta(days=365 * years)
    return start + (end - start) * random.random()


def add_random_metadata(image_path):
    with open(image_path, 'rb') as image_file:
        image = Image(image_file)

    image.make = random.choice(list(camera_manufacturers.keys()))
    image.model = random.choice(camera_manufacturers[image.make])
    image.shutter_speed_value = random.choice(shutter_speed_value)
    image.exposure_time = image.shutter_speed_value
    image.aperture_value = random.choice(aperture_value)
    image.max_aperture_value = image.aperture_value - random.choice([0.1, 0.2, 0.3, 0.4])
    image.f_number = image.aperture_value
    image.photographic_sensitivity = random.choice(sensitivity)
    image.focal_length = random.choice(focal_length)
    image.exposure_program = random.choice(exposure_program)
    image.light_source = random.choice(light_source)
    image.exposure_mode = random.choice(exposure_mode)
    image.white_balance = random.choice(white_balance)
    image.scene_capture_type = random.choice(scene_capture_type)
    image.color_space = color_space
    image.sharpness = random.choice(sharpness)
    image.saturation = random.choice(saturation)
    image.metering_mode = random.choice(metering_mode)
    image.sensing_method = random.choice(sensing_method)

    image.flash = random.choice(flashes)

    image.datetime_original = _gen_datetime().strftime(DATETIME_STR_FORMAT)
    image.datetime_digitized = image.datetime_original
    image.gps_latitude = (float(random.randint(0, 170)), float(random.randint(0, 59)), round(random.uniform(0, 59), 4))
    image.gps_longitude = (float(random.randint(0, 170)), float(random.randint(0, 59)), round(random.uniform(0, 59), 4))
    image.gps_latitude_ref = random.choice(['N', 'S'])
    image.gps_longitude_ref = random.choice(['E', 'W'])
    image.gps_altitude_ref = GpsAltitudeRef.ABOVE_SEA_LEVEL

    with open(image_path, 'wb') as new_image_file:
        new_image_file.write(image.get_file())
