"""File validation utilities."""

from app.schemas.error import ErrorCodes, ErrorDetail

# Magic bytes for image formats
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
}


def get_mime_type_from_content(content: bytes) -> str | None:
    """
    Detect MIME type from file content using magic bytes.

    More secure than trusting Content-Type header.
    """
    # Check manual signatures for JPEG and PNG
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return None


def validate_image_file(
    content: bytes,
    content_type: str | None,
    filename: str,
    max_size: int,
    allowed_types: list[str],
) -> ErrorDetail | None:
    """
    Validate an uploaded image file.

    Args:
        content: File content as bytes
        content_type: Declared Content-Type header
        filename: Original filename
        max_size: Maximum file size in bytes
        allowed_types: List of allowed MIME types

    Returns:
        ErrorDetail if validation fails, None if valid
    """
    # Check file size
    if len(content) > max_size:
        max_mb = max_size / (1024 * 1024)
        return ErrorDetail(
            code=ErrorCodes.FILE_TOO_LARGE,
            message=f"File size exceeds maximum allowed size of {max_mb:.0f} MB",
            details={"max_size_bytes": max_size, "actual_size_bytes": len(content)},
        )

    # Check file is not empty
    if len(content) == 0:
        return ErrorDetail(
            code=ErrorCodes.INVALID_REQUEST,
            message="File is empty",
        )

    # Detect actual MIME type from content (don't trust headers)
    detected_type = get_mime_type_from_content(content)

    if not detected_type:
        return ErrorDetail(
            code=ErrorCodes.INVALID_FILE_FORMAT,
            message="Could not determine file type",
        )

    # Check if detected type is allowed
    if detected_type not in allowed_types:
        return ErrorDetail(
            code=ErrorCodes.INVALID_FILE_FORMAT,
            message=f"File type '{detected_type}' is not allowed. Allowed types: {', '.join(allowed_types)}",
            details={"detected_type": detected_type, "allowed_types": allowed_types},
        )

    return None
