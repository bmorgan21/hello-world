# coding: utf-8

import base64
from io import BytesIO
import logging
import mimetypes

from os import path

from flask import send_file as _send_file
import magic
from werkzeug.exceptions import UnsupportedMediaType
from werkzeug.utils import secure_filename

from app.models import File

logger = logging.getLogger(__name__)

_default_upload_mime_types_blacklist = {
    'application/bat', 'application/vnd.ms-cab-compressed', 'application/x-bat', 'application/x-dosexec',
    'application/x-msdos-program', 'application/x-msdownload'
}

_default_upload_extensions_blacklist = {
    ".ade", ".adp", ".bat", ".chm", ".cmd", ".com", ".cpl", ".exe", ".hta", ".ins", ".isp", ".jse", ".lib", ".lnk",
    ".mde", ".msc", ".msp", ".mst", ".pif", ".scr", ".sct", ".shb", ".sys", ".vb", ".vbe", ".vbs", ".vxd", ".wsc",
    ".wsf", ".wsh", ".gadget", ".jar", ".js", ".action", ".apk", ".app", ".dmg", ".bin", ".msi", ".osx", ".reg",
    ".vbscript", ".ws", ""
}


class MimeTypeNotAllowedException(UnsupportedMediaType):
    pass


class FileExtensionNotAllowedException(UnsupportedMediaType):
    pass


class VirusDetectedInFileException(Exception):
    pass


def send_file(file, *args, **kwargs):
    kwargs.setdefault('mimetype', mimetypes.guess_type(file.name)[0])

    return _send_file(BytesIO(base64.b64decode(file.properties['data'])), *args, **kwargs)


def upload_file(file):
    filename = secure_filename(file.filename)
    if not is_extension_allowed(filename):
        raise FileExtensionNotAllowedException("Given filename's extension not allowed for upload.")

    mimetype = guess_mimetype(file)
    if not is_mimetype_allowed(mimetype):
        raise MimeTypeNotAllowedException('Auto-detected MIME type not allowed for upload.')

    return File(name=filename, stream=file)


def guess_mimetype(file):
    current_position = file.tell()
    file.seek(0)
    mimetype = magic.from_buffer(file.read(1024), mime=True)
    file.seek(current_position)

    return mimetype


def is_mimetype_allowed(mimetype):
    return mimetype not in _default_upload_mime_types_blacklist


def is_extension_allowed(filename):
    name, ext = path.splitext(filename)
    return ext not in _default_upload_extensions_blacklist
