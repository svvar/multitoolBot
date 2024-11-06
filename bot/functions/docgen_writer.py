import io

from PIL import Image, ImageDraw, ImageFont

font_path_ua = './assets/fonts/timesnrcyrmt_bold.ttf'
template_path_ua = './assets/doc_template.jpg'

font_path_us = './assets/fonts/CourierStd.ttf'
template_path_us_1 = './assets/EIN-FORM-US-1.jpg'
template_path_us_2 = './assets/EIN-FORM-US-2.jpg'

name_font = ImageFont.truetype(font_path_ua, 18)
ordinary_font = ImageFont.truetype(font_path_ua, 16)
text_color_ua = (75, 75, 75)

us_font = ImageFont.truetype(font_path_us, 43)
text_color_us = (50, 50, 50)


def draw_text(draw, text, position, font, max_line_width, text_color, line_height=1, letter_spacing=0.7, alignment='left'):
    x, y = position

    ascent, descent = font.getmetrics()
    line_height_px = (ascent + descent) * line_height

    paragraphs = text.split('\n')

    for paragraph in paragraphs:
        words = paragraph.split(' ')
        lines = []
        while words:
            line = ''
            while words:
                test_line = line + words[0] + ' '
                bbox = font.getbbox(test_line)
                if bbox[2] - bbox[0] <= max_line_width:
                    line = test_line
                    words.pop(0)
                else:
                    break
            if not line.strip():
                line = words.pop(0) + ' '
            lines.append(line)

        for line in lines:
            line_width = 0
            for char in line:
                char_bbox = font.getbbox(char)
                char_width = char_bbox[2] - char_bbox[0]
                line_width += char_width + letter_spacing

            if alignment == 'center':
                line_x = x + (max_line_width - line_width) / 2
            elif alignment == 'right':
                line_x = x + (max_line_width - line_width)
            else:
                line_x = x

            for char in line:
                draw.text((line_x, y), char, font=font, fill=text_color)
                char_bbox = font.getbbox(char)
                char_width = char_bbox[2] - char_bbox[0]
                line_x += char_width + letter_spacing

            y += line_height_px
        # Optionally, add extra spacing after a paragraph
        # y += line_height_px * 0.5  # Adjust the multiplier as needed


def draw_svidotstvo(company_name, edrpou, location, registrator, date, notary, series, number):
    template = Image.open(template_path_ua)
    draw = ImageDraw.Draw(template)

    default_spacing = 0.8
    default_line_height = 1
    text_blocks = [
        {"text": company_name, "position": (170, 250), "font": name_font, "max_width": 500, 'line_height': 1.5, "letter_spacing": default_spacing, "alignment": "center"},
        {"text": edrpou, "position": (375, 332), "font": ordinary_font, "max_width": 200, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": location, "position": (375, 390), "font": ordinary_font, "max_width": 270, 'line_height': 1.4, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": registrator, "position": (375, 480), "font": ordinary_font, "max_width": 270, 'line_height': 1.3, "letter_spacing": default_spacing,  "alignment": "left"},
        {"text": date, "position": (375, 575), "font": ordinary_font, "max_width": 500, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": notary, "position": (507, 899), "font": ordinary_font, "max_width": 200, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": series, "position": (160, 122), "font": ordinary_font, "max_width": 90, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": number, "position": (642, 124), "font": ordinary_font, "max_width": 120, 'line_height': default_line_height,"letter_spacing": default_spacing, "alignment": "left"},
    ]

    for block in text_blocks:
        draw_text(draw, block["text"], block["position"], block["font"], block["max_width"], text_color_ua, block['line_height'], block['letter_spacing'], block["alignment"])

    output = io.BytesIO()
    template.save(output, format='JPEG')
    return output


def draw_us_doc(ein, company_name, address):
    template1 = Image.open(template_path_us_1)
    draw1 = ImageDraw.Draw(template1)

    template2 = Image.open(template_path_us_2)
    draw2 = ImageDraw.Draw(template2)

    company_text = f'{company_name}\n{address}'

    default_spacing = 0.8
    default_line_height = 1

    text_blocks_page_1 = [
        {"text": ein, "position": (1579, 499), "font": us_font, "max_width": 400, 'line_height': 1, "letter_spacing": default_spacing, "alignment": "left"},
        {"text": f'{ein}.', "position": (340, 1374), "font": us_font, "max_width": 400, 'line_height': 1, "letter_spacing": default_spacing, "alignment": "center"},
        {"text": company_text, "position": (455, 704), "font": us_font, "max_width": 800, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"},
    ]

    for block in text_blocks_page_1:
        draw_text(draw1, block["text"], block["position"], block["font"], block["max_width"], text_color_us, block['line_height'], block['letter_spacing'], block["alignment"])

    page_2 = {"text": company_text, "position": (1533, 2873), "font": us_font, "max_width": 800, 'line_height': default_line_height, "letter_spacing": default_spacing, "alignment": "left"}

    draw_text(draw2, page_2["text"], page_2["position"], page_2["font"], page_2["max_width"], text_color_us, page_2['line_height'], page_2['letter_spacing'], page_2["alignment"])

    output1 = io.BytesIO()
    template1.save(output1, format='JPEG')

    output2 = io.BytesIO()
    template2.save(output2, format='JPEG')

    return output1, output2
