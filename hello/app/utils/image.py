# coding: utf-8

import base64
from io import BytesIO

from flask import send_file
from PIL import ExifTags, Image, ImageOps


def _handle_rotation(im):
    if not hasattr(im, '_getexif'):
        return im

    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            if im._getexif():
                exif = dict(im._getexif().items())

                if orientation in exif:
                    if exif[orientation] == 3:
                        im = im.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        im = im.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        im = im.rotate(90, expand=True)

    return im


def open_image(image):
    stream = BytesIO(base64.b64decode(image.file.properties['data']))
    im = Image.open(stream)
    im = _handle_rotation(im)

    wp = image.bottom_right_x - image.top_left_x
    hp = image.bottom_right_y - image.top_left_y

    if wp == 1 and hp == 1:
        # full size in both direction
        return im

    im_width = im.size[0]
    im_height = im.size[1]

    width = wp * im_width
    height = hp * im_height

    x = image.top_left_x * im_width
    y = image.top_left_y * im_height

    return im.crop((x, y, x + width, y + height))


def fit_image(*args, **kwargs):
    kwargs.setdefault('method', Image.ANTIALIAS)
    return ImageOps.fit(*args, **kwargs)


def send_image(im, *args, **kwargs):
    output = BytesIO()
    im.save(output, 'jpeg')

    output.seek(0)

    kwargs['mimetype'] = 'image/jpeg'
    return send_file(output, *args, **kwargs)
