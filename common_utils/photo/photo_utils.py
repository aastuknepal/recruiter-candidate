import io
import os
from PIL import Image, ImageOps
from rest_framework.exceptions import ValidationError

# Default maximum photo size limit in MB (can be adjusted here or via Configuration in DB)
DEFAULT_MAX_PHOTO_UPLOAD_SIZE_MB = 20

# Compression default configurations (matching dartachalani implementation)
DEFAULT_IMAGE_QUALITY = 85
DEFAULT_MAX_WIDTH = 1920
DEFAULT_MAX_HEIGHT = 1080
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def get_max_photo_upload_size_mb():
    """
    Fetch max photo upload size limit in MB from Configuration database model via ConfigService.
    Falls back to DEFAULT_MAX_PHOTO_UPLOAD_SIZE_MB (20 MB) if missing or invalid.
    """
    try:
        from apps.setup.utils.configurations import ConfigService

        fetched_val = ConfigService.get(
            "MAX_PHOTO_UPLOAD_SIZE_MB", DEFAULT_MAX_PHOTO_UPLOAD_SIZE_MB
        )
        if fetched_val is not None:
            max_mb = int(fetched_val)
            if max_mb > 0:
                return max_mb
    except Exception:
        pass
    return DEFAULT_MAX_PHOTO_UPLOAD_SIZE_MB


def compress_image(
    file_input,
    filename,
    quality=DEFAULT_IMAGE_QUALITY,
    max_width=DEFAULT_MAX_WIDTH,
    max_height=DEFAULT_MAX_HEIGHT,
):
    """
    Production-grade image compression function using Pillow (matching dartachalani backend).

    Args:
        file_input: File path, file-like object, or bytes of the image.
        filename: Original file name.
        quality: JPEG compression quality (default: 85).
        max_width: Maximum image width (default: 1920).
        max_height: Maximum image height (default: 1080).

    Returns:
        tuple: (compressed_bytes, new_filename) or (None, filename) on failure.
    """
    try:
        img = Image.open(file_input)

        # Convert to RGB if necessary (handles RGBA, P, grayscale, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Auto-orient the image based on EXIF data
        img = ImageOps.exif_transpose(img)

        # Resize if larger than max dimensions while maintaining aspect ratio
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()

        # Generate new filename with .jpg extension
        base, _ = os.path.splitext(filename)
        new_filename = f"{base}.jpg"

        # Save as progressive JPEG for optimal web performance
        img.save(
            buffer, format="JPEG", quality=quality, optimize=True, progressive=True
        )
        return buffer.getvalue(), new_filename
    except Exception as e:
        print(f"Error compressing image {filename}: {e}")
        return None, filename


def compress_photo_file(
    file_obj,
    quality=DEFAULT_IMAGE_QUALITY,
    max_width=DEFAULT_MAX_WIDTH,
    max_height=DEFAULT_MAX_HEIGHT,
):
    """
    Compress a Django File / UploadedFile object if it is an image.

    Args:
        file_obj: Django File, UploadedFile, or ImageField file object.
        quality: Compression quality.
        max_width: Maximum width.
        max_height: Maximum height.

    Returns:
        Compressed Django File object (InMemoryUploadedFile),
        or original file_obj if compression is not applicable or fails.
    """
    if not file_obj or not hasattr(file_obj, "name"):
        return file_obj

    filename = getattr(file_obj, "name", "")
    if not filename:
        return file_obj

    ext = os.path.splitext(filename)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return file_obj

    try:
        compressed_bytes, new_filename = compress_image(
            file_obj,
            filename,
            quality=quality,
            max_width=max_width,
            max_height=max_height,
        )

        if compressed_bytes is not None:
            from django.core.files.uploadedfile import InMemoryUploadedFile

            new_file = InMemoryUploadedFile(
                file=io.BytesIO(compressed_bytes),
                field_name=getattr(file_obj, "field_name", "file"),
                name=new_filename,
                content_type="image/jpeg",
                size=len(compressed_bytes),
                charset=None,
            )
            return new_file
    except Exception as e:
        print(f"Failed to compress photo file {filename}: {e}")

    return file_obj


def validate_photo_file(file_obj):
    """
    Validate uploaded photo file size against max MB limit and compress image if valid.

    Args:
        file_obj: Django File/ImageField object

    Returns:
        Compressed or original file_obj if valid.

    Raises:
        ValidationError: If photo size exceeds the allowed limit (20 MB default).
    """
    if not file_obj or not hasattr(file_obj, "size"):
        return file_obj

    max_mb = get_max_photo_upload_size_mb()
    max_bytes = max_mb * 1024 * 1024

    file_size = getattr(file_obj, "size", 0)
    if file_size > max_bytes:
        current_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"Photo size cannot exceed {max_mb} MB. Current size: {current_mb:.2f} MB"
        )

    # Perform image compression if the file is a valid image
    return compress_photo_file(file_obj)

