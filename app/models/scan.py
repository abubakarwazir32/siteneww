from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ScanStatus(str, Enum):
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"
    stopped   = "stopped"


class LoginMode(str, Enum):
    none   = "none"
    form   = "form"      # Username/password form login
    cookie = "cookie"    # Cookie string paste karo


# ── Request body jab user naya scan shuru kare ──────────────────
class ScanCreateRequest(BaseModel):
    target_url: str                        # Website URL
    max_pages: int = 50                    # Kitne pages crawl karein
    login_required: bool = False
    login_mode: LoginMode = LoginMode.none
    login_url: Optional[str] = None        # Login page URL (optional)
    login_username: Optional[str] = None
    login_password: Optional[str] = None
    login_cookie: Optional[str] = None     # Cookie string (agar cookie mode ho)
    capture_full_page: bool = True         # Full-page ya sirf viewport
    capture_mobile: bool = False           # Mobile viewport bhi?
    follow_subdomains: bool = False


# ── Ek page ka data ─────────────────────────────────────────────
class PageResult(BaseModel):
    url: str
    title: Optional[str]
    status_code: Optional[int]
    load_time_ms: Optional[int]
    screenshot_url: Optional[str]          # Supabase Storage public URL
    screenshot_base64: Optional[str]       # Base64 (agar storage nahi use karni)
    meta_description: Optional[str]
    internal_links: List[str] = []
    images_count: int = 0
    captured_at: Optional[datetime]


# ── Scan ka full response ────────────────────────────────────────
class ScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    target_url: str
    pages_found: int = 0
    pages_captured: int = 0
    pages_failed: int = 0
    current_url: Optional[str] = None     # Abhi kaunsa page capture ho raha
    pages: List[PageResult] = []
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str] = None


# ── Stop scan request ────────────────────────────────────────────
class ScanStopRequest(BaseModel):
    scan_id: str
