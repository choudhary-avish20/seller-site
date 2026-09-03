"""
Storage service — abstracts image persistence behind a single interface.

When R2 env vars are set (production):
    - Uploads go to Cloudflare R2 via the S3-compatible API
    - Returns a permanent public HTTPS URL (served from R2's CDN)

When R2 env vars are not set (local dev):
    - Falls back to writing files to backend/uploads/products/ on disk
    - Returns a relative path URL (/uploads/products/<filename>)
    - The /uploads StaticFiles mount in main.py serves these in dev

Callers only call upload_image() and get back a URL string — they never need
to know or care which backend is active.
"""

import logging
import uuid
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Local disk fallback path (backend/uploads/products/)
_LOCAL_UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "products"


def _get_r2_client():
    """Build a boto3 S3 client pointed at Cloudflare R2.
    R2 is S3-compatible but uses a custom endpoint:
      https://<account_id>.r2.cloudflarestorage.com
    """
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",  # R2 uses "auto" as the region
    )


def _ext_to_content_type(ext: str) -> str:
    return {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
        ".gif":  "image/gif",
        ".avif": "image/avif",
    }.get(ext.lower(), "application/octet-stream")


async def upload_image(contents: bytes, ext: str) -> str:
    """Upload image bytes and return a public URL string.

    Args:
        contents: Raw image bytes (already validated and size-checked by the caller).
        ext:      File extension including the dot, e.g. ".jpg", ".webp".

    Returns:
        A URL string:
        - R2 active  → full HTTPS URL: "https://pub-xxx.r2.dev/products/<uuid>.jpg"
        - Local dev  → relative path:  "/uploads/products/<uuid>.jpg"

    Raises:
        RuntimeError: If the upload to R2 fails. Let the route handler catch this
                      and return an appropriate HTTP error.
    """
    unique_name = f"{uuid.uuid4().hex}{ext}"

    if settings.r2_configured:
        return await _upload_to_r2(contents, unique_name, ext)
    else:
        return _save_to_disk(contents, unique_name)


async def _upload_to_r2(contents: bytes, filename: str, ext: str) -> str:
    """Put the object in R2 under the 'products/' prefix and return the public URL."""
    key = f"products/{filename}"
    content_type = _ext_to_content_type(ext)

    try:
        client = _get_r2_client()
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=contents,
            ContentType=content_type,
            # CacheControl helps browsers and Cloudflare edge cache images aggressively.
            # Images are content-addressed (UUID filename) so cache-busting is not needed.
            CacheControl="public, max-age=31536000, immutable",
        )
        public_url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"
        logger.info(f"Uploaded to R2: {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"R2 upload failed for {filename}: {e}")
        raise RuntimeError(f"Image upload to R2 failed: {e}") from e


def _save_to_disk(contents: bytes, filename: str) -> str:
    """Write image bytes to the local uploads directory and return a relative URL."""
    _LOCAL_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    dest = _LOCAL_UPLOAD_ROOT / filename
    dest.write_bytes(contents)
    logger.debug(f"Saved image to disk: {dest}")
    return f"/uploads/products/{filename}"
