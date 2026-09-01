from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_seller_or_admin
from app.db.session import get_db
from app.models.site_settings import SiteSettings
from app.models.user import User
from app.schemas.settings import SiteSettingsResponse, SiteSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

# Sensible defaults so the public Contact page isn't empty before an admin
# fills in the real details — matches what was previously hardcoded in the UI.
_DEFAULTS = {
    "phone": "+48 579 383 945",
    "email": "kontakt@wolkago.pl",
    "address": "Wólka Kosowska, Polska",
    "working_hours": "Pon–Pt: 8:00–18:00, Sob: 9:00–14:00",
}


def _get_or_create(db: Session) -> SiteSettings:
    row = db.query(SiteSettings).first()
    if not row:
        row = SiteSettings(**_DEFAULTS)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=SiteSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Public — powers the Contact page."""
    return _get_or_create(db)


@router.put("", response_model=SiteSettingsResponse)
def update_settings(
    payload: SiteSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_seller_or_admin),
):
    row = _get_or_create(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row
