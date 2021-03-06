import io
import logging
import os
from urllib.parse import urlparse

import requests
from PIL import Image
from django.conf import settings

log = logging.getLogger(__name__)


def upload_image_bytes(
    filename, data, resize=(192, 192), convert_format="JPEG", **kwargs
):
    if not data:
        return None

    if resize:
        try:
            image = Image.open(data)
        except OSError:
            log.warning(f"Bad image data")
            return None

        if convert_format:
            convert_extension = "." + convert_format.lower()
            if convert_format == "JPEG":
                image = image.convert("RGB")
                convert_extension = ".jpg"
        else:
            _, convert_extension = os.path.splitext(filename)

        image.thumbnail(resize)
        saved_image = io.BytesIO()
        saved_image.name = filename
        image.save(saved_image, format=convert_format, **kwargs)
        data = saved_image.getvalue()

        filename = os.path.splitext(filename)[0] + convert_extension

    try:
        uploaded = requests.post(
            url=settings.MEDIA_UPLOAD_URL,
            params={"code": settings.MEDIA_UPLOAD_CODE},
            files={"media": (filename, data)},
        )
    except requests.exceptions.RequestException as ex:
        log.error(f"Image upload error: {ex}")
        return None

    if 200 <= uploaded.status_code <= 299:
        try:
            response_data = uploaded.json()
        except Exception as ex:
            log.exception(f"Image upload error: {ex} ({uploaded.content})")
            return None

        return response_data["uploaded"][0]

    return None


def upload_image_from_url(url, resize=(192, 192), convert_format="JPEG", quality=90):
    if settings.DEBUG or not settings.MEDIA_UPLOAD_URL or not settings.MEDIA_UPLOAD_CODE:
        return url

    if not url:
        return None

    image_name = os.path.basename(urlparse(url).path)
    if "." not in image_name:
        image_name += ".jpg"

    try:
        image_data = io.BytesIO(requests.get(url).content)
    except requests.exceptions.RequestException:
        return None

    return upload_image_bytes(image_name, image_data, resize, convert_format)
