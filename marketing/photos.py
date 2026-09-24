"""Shrink guest-uploaded review photos before storing them in the database."""

import io

MAX_SIDE = 1600
JPEG_QUALITY = 82


def compress_photo(fileobj):
    """Return (bytes, content_type) for an uploaded image, resized to MAX_SIDE."""
    from PIL import Image, ImageOps

    fileobj.seek(0)
    try:
        with Image.open(fileobj) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((MAX_SIDE, MAX_SIDE))
            out = io.BytesIO()
            img.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return out.getvalue(), "image/jpeg"
    except Exception:
        # Form validation already confirmed it is an image; keep the original bytes.
        fileobj.seek(0)
        content_type = getattr(fileobj, "content_type", "") or "image/jpeg"
        return fileobj.read(), content_type[:40]
