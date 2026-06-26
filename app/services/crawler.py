"""
Crawler Service — SiteSnap ka dil aur dimagh
Playwright use karke website crawl karta hai, screenshots leta hai,
aur login bhi handle karta hai.
"""

import asyncio
import base64
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Set
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.models.scan import (
    ScanCreateRequest, ScanResponse, ScanStatus, PageResult, LoginMode
)

# ── In-memory scan store (production mein Redis ya DB use karo) ──
_scans: Dict[str, ScanResponse] = {}
_stop_signals: Set[str] = set()   # Jis scan ko rokna ho uska ID yahan


# ════════════════════════════════════════════════════════════════
#  PUBLIC FUNCTIONS
# ════════════════════════════════════════════════════════════════

def create_scan(request: ScanCreateRequest) -> str:
    """Naya scan banao, ID return karo"""
    scan_id = str(uuid.uuid4())
    _scans[scan_id] = ScanResponse(
        scan_id=scan_id,
        status=ScanStatus.pending,
        target_url=str(request.target_url),
        started_at=datetime.utcnow(),
    )
    return scan_id


def get_scan(scan_id: str) -> Optional[ScanResponse]:
    """Scan ka current state lao"""
    return _scans.get(scan_id)


def stop_scan(scan_id: str) -> bool:
    """Scan ko stop karne ka signal bhejo"""
    if scan_id in _scans:
        _stop_signals.add(scan_id)
        return True
    return False


async def run_scan(scan_id: str, request: ScanCreateRequest):
    """
    Main crawler — background mein chalta hai.
    FastAPI background task ke zariye call hota hai.
    """
    scan = _scans[scan_id]
    scan.status = ScanStatus.running

    try:
        async with async_playwright() as pw:
            # ── Browser launch karo ──────────────────────────────
            browser: Browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )

            # ── Browser context (viewport + user agent) ──────────
            context: BrowserContext = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                ignore_https_errors=True,
            )

            # ── Login handle karo (agar zaroorat ho) ────────────
            if request.login_required:
                await _handle_login(context, request)

            # ── Crawling shuru karo ──────────────────────────────
            base_domain = _get_domain(str(request.target_url))
            visited: Set[str] = set()
            queue = [str(request.target_url)]

            while queue and len(visited) < request.max_pages:

                # Stop signal check karo
                if scan_id in _stop_signals:
                    _stop_signals.discard(scan_id)
                    scan.status = ScanStatus.stopped
                    await browser.close()
                    return

                url = queue.pop(0)
                if url in visited:
                    continue

                visited.add(url)
                scan.current_url = url
                scan.pages_found = len(visited) + len(queue)

                # ── Page capture karo ────────────────────────────
                page_result = await _capture_page(
                    context, url, base_domain,
                    request.capture_full_page,
                    request.capture_mobile,
                )

                if page_result:
                    scan.pages.append(page_result)
                    scan.pages_captured += 1

                    # Nayi links queue mein daalo
                    for link in page_result.internal_links:
                        if (
                            link not in visited
                            and link not in queue
                            and len(visited) + len(queue) < request.max_pages
                        ):
                            queue.append(link)
                else:
                    scan.pages_failed += 1

                # Server pe zyada load mat daalo
                await asyncio.sleep(0.5)

            await browser.close()
            scan.status = ScanStatus.completed
            scan.completed_at = datetime.utcnow()
            scan.current_url = None

    except Exception as e:
        scan.status = ScanStatus.failed
        scan.error_message = str(e)
        scan.completed_at = datetime.utcnow()


# ════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ════════════════════════════════════════════════════════════════

async def _handle_login(context: BrowserContext, request: ScanCreateRequest):
    """Login page pe jao aur credentials fill karo"""

    if request.login_mode == LoginMode.cookie and request.login_cookie:
        # Cookie directly inject karo — no form needed
        cookies = _parse_cookie_string(request.login_cookie, str(request.target_url))
        await context.add_cookies(cookies)
        return

    # Form-based login
    login_url = request.login_url or str(request.target_url)
    page: Page = await context.new_page()

    try:
        await page.goto(login_url, wait_until="networkidle", timeout=30000)

        # Common username/email field selectors try karo
        username_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[name="username"]',
            'input[name="user"]',
            'input[id*="email"]',
            'input[id*="user"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="username" i]',
        ]

        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[name="pass"]',
        ]

        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
        ]

        # Username field fill karo
        for sel in username_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(request.login_username or "")
                    break
            except Exception:
                continue

        # Password fill karo
        for sel in password_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.fill(request.login_password or "")
                    break
            except Exception:
                continue

        # Submit button click karo
        for sel in submit_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0:
                    await el.click()
                    break
            except Exception:
                continue

        # Login complete hone ka wait karo
        await page.wait_for_load_state("networkidle", timeout=15000)

    except Exception as e:
        # Login fail hua — continue anyway (public pages capture honge)
        print(f"Login attempt failed: {e}")
    finally:
        await page.close()


async def _capture_page(
    context: BrowserContext,
    url: str,
    base_domain: str,
    full_page: bool,
    mobile: bool,
) -> Optional[PageResult]:
    """Ek page visit karo, screenshot lo, links nikalon"""

    page: Page = await context.new_page()
    start_time = time.time()

    try:
        # Mobile viewport chahiye to override karo
        if mobile:
            await page.set_viewport_size({"width": 390, "height": 844})

        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status_code = response.status if response else None

        # Page load hone do (lazy images etc.)
        await page.wait_for_timeout(1500)

        load_time = int((time.time() - start_time) * 1000)

        # ── Page info nikalo ──────────────────────────────────
        title = await page.title()

        meta_desc = await page.evaluate("""
            () => {
                const el = document.querySelector('meta[name="description"]');
                return el ? el.getAttribute('content') : null;
            }
        """)

        # ── Internal links nikalo ─────────────────────────────
        raw_links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
        """)

        internal_links = list({
            _normalize_url(link)
            for link in raw_links
            if _is_internal(link, base_domain) and _normalize_url(link)
        })

        # ── Images count ──────────────────────────────────────
        images_count = await page.evaluate(
            "() => document.querySelectorAll('img').length"
        )

        # ── Screenshot lo ─────────────────────────────────────
        screenshot_bytes = await page.screenshot(
            full_page=full_page,
            type="png",
        )
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        return PageResult(
            url=url,
            title=title or None,
            status_code=status_code,
            load_time_ms=load_time,
            screenshot_base64=screenshot_b64,
            screenshot_url=None,          # Supabase upload ke baad fill ho
            meta_description=meta_desc,
            internal_links=internal_links[:50],  # Max 50 links per page
            images_count=images_count or 0,
            captured_at=datetime.utcnow(),
        )

    except Exception as e:
        print(f"Failed to capture {url}: {e}")
        return None
    finally:
        await page.close()


# ════════════════════════════════════════════════════════════════
#  URL UTILITIES
# ════════════════════════════════════════════════════════════════

def _get_domain(url: str) -> str:
    """https://example.com/path → example.com"""
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def _is_internal(url: str, base_domain: str) -> bool:
    """Check karo link same domain ka hai ya nahi"""
    try:
        domain = _get_domain(url)
        return domain == base_domain or domain.endswith("." + base_domain)
    except Exception:
        return False


def _normalize_url(url: str) -> Optional[str]:
    """Fragment remove karo, trailing slash normalize karo"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        # Fragment (#section) hata do
        clean = parsed._replace(fragment="").geturl()
        return clean.rstrip("/") or clean
    except Exception:
        return None


def _parse_cookie_string(cookie_str: str, url: str) -> list:
    """
    'name=value; name2=value2' format se Playwright cookie list banao
    """
    domain = _get_domain(url)
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            })
    return cookies
