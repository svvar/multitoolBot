import io

from PIL import Image, ImageDraw, ImageFont

font_path = './assets/fonts/timesnrcyrmt_bold.ttf'
template_path = './assets/doc_template.jpg'

name_font = ImageFont.truetype(font_path, 18)
ordinary_font = ImageFont.truetype(font_path, 16)
text_color = (75, 75, 75)


def draw_text(draw, text, position, font, max_line_width, text_color, line_height=1, letter_spacing=0.7, alignment='left'):
    x, y = position

    lines = []
    words = text.split(' ')
    while words:
        line = ''
        while words:
            test_line = line + words[0] + ' '
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] <= max_line_width:
                line = test_line
                words.pop(0)
            else:
                break
        lines.append(line)

    for line in lines:
        line_width = 0
        for char in line:
            char_bbox = draw.textbbox((0, 0), char, font=font)
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
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            line_x += char_width + letter_spacing

        y += int((bbox[3] - bbox[1]) * line_height)


def draw_svidotstvo(company_name, edrpou, location, registrator, date, notary, series, number):
    template = Image.open(template_path)
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
        draw_text(draw, block["text"], block["position"], block["font"], block["max_width"], text_color, block['line_height'], block['letter_spacing'], block["alignment"])

    output = io.BytesIO()
    template.save(output, format='JPEG')
    return output
