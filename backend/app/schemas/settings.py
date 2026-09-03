from typing import Optional

from pydantic import BaseModel, Field


class SiteSettingsResponse(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    working_hours: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    contact_note: Optional[str] = None
    terms_content: Optional[str] = None

    class Config:
        from_attributes = True


class SiteSettingsUpdate(BaseModel):
    """All fields optional — admin can update any subset of contact fields at a time."""

    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    working_hours: Optional[str] = Field(None, max_length=255)
    facebook_url: Optional[str] = Field(None, max_length=500)
    instagram_url: Optional[str] = Field(None, max_length=500)
    whatsapp_number: Optional[str] = Field(None, max_length=32)
    contact_note: Optional[str] = None
    terms_content: Optional[str] = None
