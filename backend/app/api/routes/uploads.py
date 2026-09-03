from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.seller import SellerProfile, SellerStatus
from app.services.storage import upload_image

router = APIRouter(prefix="/uploads", tags=["uploads"])

# test-images still served from local assets (dev/demo only)
ASSETS_ROOT = Path(__file__).resolve().parents[3].parent / "assets" / "test-images"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def _is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT


def _sniff_image_ext(contents: bytes) -> str | None:
    """Verify file content against magic bytes — ignores whatever extension the
    client claims, so a renamed executable cannot bypass the extension check."""
    if contents[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if contents[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if contents[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return ".webp"
    if contents[4:8] == b"ftyp" and contents[8:12] in (
        b"avif", b"avis", b"mif1", b"MA1A", b"MA1B"
    ):
        return ".avif"
    return None


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Auth: admins always allowed; sellers must be approved
    if current_user.role not in (UserRole.admin, UserRole.seller):
        raise HTTPException(status_code=403, detail="Only sellers or admins can upload images")
    if current_user.role == UserRole.seller:
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if not seller or seller.status != SellerStatus.approved:
            raise HTTPException(status_code=403, detail="Seller not approved")

    # Extension allow-list
    if not file.filename or not _is_allowed(file.filename):
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Use jpg/jpeg/png/webp/gif/avif",
        )

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # Magic-byte validation — must match the claimed extension
    sniffed_ext = _sniff_image_ext(contents)
    claimed_ext = Path(file.filename).suffix.lower()
    equivalent_exts = {".jpg", ".jpeg"} if sniffed_ext == ".jpg" else {sniffed_ext}
    if sniffed_ext is None or claimed_ext not in equivalent_exts:
        raise HTTPException(
            status_code=400,
            detail="File content does not match a supported image format",
        )

    # Delegate storage to the storage service (R2 in prod, local disk in dev)
    try:
        url = await upload_image(contents, claimed_ext)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"url": url, "filename": Path(url).name, "original_filename": file.filename}


# ── Test-image helpers (dev/demo only) ────────────────────────────────────────

@router.get("/test-images", response_model=List[str])
def list_test_images():
    """List placeholder images from assets/test-images for demo/dev use."""
    if not ASSETS_ROOT.exists():
        return []
    return sorted(
        p.name for p in ASSETS_ROOT.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT
    )


@router.get("/test-images/{filename}")
def get_test_image(filename: str):
    """Serve a single placeholder image. Path traversal is blocked."""
    resolved_root = ASSETS_ROOT.resolve()
    path = (ASSETS_ROOT / filename).resolve()
    if not path.is_relative_to(resolved_root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    from fastapi.responses import FileResponse
    return FileResponse(str(path))
