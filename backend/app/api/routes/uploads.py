import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.seller import SellerProfile, SellerStatus

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Resolve upload dir: backend/uploads/products
BASE_DIR = Path(__file__).resolve().parents[3]  # backend/
UPLOAD_ROOT = BASE_DIR / "uploads" / "products"
ASSETS_ROOT = BASE_DIR.parent / "assets" / "test-images"  # project-root/assets/test-images
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT


def _sniff_image_ext(contents: bytes) -> str | None:
    """Identify the real image format from its magic bytes, ignoring whatever
    extension the client claims — a renamed .exe with a .png extension would
    otherwise sail through the extension-only check above."""
    if contents[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if contents[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if contents[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return ".webp"
    if contents[4:8] == b"ftyp" and contents[8:12] in (b"avif", b"avis", b"mif1", b"MA1A", b"MA1B"):
        return ".avif"
    return None


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.admin, UserRole.seller):
        raise HTTPException(status_code=403, detail="Only sellers or admins can upload images")
    if current_user.role == UserRole.seller:
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if not seller or seller.status != SellerStatus.approved:
            raise HTTPException(status_code=403, detail="Seller not approved")
    if not file.filename or not _is_allowed(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed. Use jpg/jpeg/png/webp/gif/avif")
    
    # read and check size
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    sniffed_ext = _sniff_image_ext(contents)
    claimed_ext = Path(file.filename).suffix.lower()
    equivalent_exts = {".jpg", ".jpeg"} if sniffed_ext == ".jpg" else {sniffed_ext}
    if sniffed_ext is None or claimed_ext not in equivalent_exts:
        raise HTTPException(status_code=400, detail="File content doesn't match a supported image format")

    ext = claimed_ext
    unique = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_ROOT / unique
    dest.write_bytes(contents)

    # URL served via StaticFiles mount at /uploads
    url = f"/uploads/products/{unique}"
    return {"url": url, "filename": unique, "original_filename": file.filename}


@router.get("/test-images", response_model=List[str])
def list_test_images():
    """
    Lists files in assets/test-images for seller to pick as placeholder until real uploads.
    Public; returns URLs relative to /assets or /uploads? For now returns filenames that can be prefixed.
    """
    if not ASSETS_ROOT.exists():
        return []
    files = []
    for p in sorted(ASSETS_ROOT.iterdir()):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            # expose as reference; frontend can use /assets/test-images/<file> if served, but we return backend URL if mounted separately
            # For now return a marker path that frontend can use as /test-images/<file> via static? We'll just return filename and let frontend construct preview via API.
            files.append(p.name)
    return files


@router.get("/test-images/{filename}")
def get_test_image(filename: str):
    # serve file from assets/test-images without auth (for preview)
    resolved_root = ASSETS_ROOT.resolve()
    path = (ASSETS_ROOT / filename).resolve()
    if not path.is_relative_to(resolved_root):
        raise HTTPException(status_code=404, detail="Not found")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    from fastapi.responses import FileResponse
    return FileResponse(str(path))
