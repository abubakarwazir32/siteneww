// ════════════════════════════════════════════════════════════════
// SiteSnap — Lovable Frontend Integration
// Yeh code Lovable mein apne existing components mein paste karo
// ════════════════════════════════════════════════════════════════

// 1. APNA RAILWAY URL YAHAN DAALO (deploy ke baad milega)
const BACKEND_URL = "https://your-app.railway.app";  // ← replace karo


// ── SCAN SHURU KARO ─────────────────────────────────────────────
export async function startScan(formData) {
  /**
   * formData = {
   *   target_url: "https://example.com",
   *   max_pages: 50,
   *   login_required: false,
   *   login_username: "",
   *   login_password: "",
   *   login_url: "",
   *   capture_full_page: true,
   * }
   */
  const res = await fetch(`${BACKEND_URL}/api/scans/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });

  if (!res.ok) throw new Error("Scan start failed");
  return await res.json();  // { scan_id, status, ... }
}


// ── LIVE STATUS POLLING ──────────────────────────────────────────
export async function getScanStatus(scanId) {
  const res = await fetch(`${BACKEND_URL}/api/scans/status/${scanId}`);
  if (!res.ok) throw new Error("Status fetch failed");
  return await res.json();
}


// ── SCAN ROKAO ──────────────────────────────────────────────────
export async function stopScan(scanId) {
  const res = await fetch(`${BACKEND_URL}/api/scans/stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scan_id: scanId }),
  });
  return await res.json();
}


// ── POLLING HOOK (React) ─────────────────────────────────────────
// Yeh hook Lovable ke kisi bhi component mein use karo
import { useState, useEffect, useRef } from "react";

export function useScanPolling(scanId) {
  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!scanId) return;

    const poll = async () => {
      try {
        const data = await getScanStatus(scanId);
        setScan(data);

        // Scan khatam ho gaya — polling band karo
        if (["completed", "failed", "stopped"].includes(data.status)) {
          clearInterval(intervalRef.current);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(intervalRef.current);
      }
    };

    poll(); // Pehli baar turant call karo
    intervalRef.current = setInterval(poll, 2500); // Har 2.5 sec mein

    return () => clearInterval(intervalRef.current); // Cleanup
  }, [scanId]);

  return { scan, error };
}


// ── SCREENSHOT DISPLAY ───────────────────────────────────────────
// Backend se base64 screenshot aata hai — yun display karo:
export function screenshotSrc(page) {
  if (page.screenshot_url) return page.screenshot_url;         // Supabase URL
  if (page.screenshot_base64)
    return `data:image/png;base64,${page.screenshot_base64}`; // Base64
  return null;
}


// ════════════════════════════════════════════════════════════════
// LOVABLE PROMPT — Apne Lovable chat mein yeh paste karo:
// ════════════════════════════════════════════════════════════════
/*

Update the SiteSnap app to connect to a real backend API.

Backend base URL: https://your-app.railway.app  (replace with actual)

API Endpoints:
- POST /api/scans/start  → body: { target_url, max_pages, login_required, login_username, login_password, login_url, capture_full_page }  → returns { scan_id, status }
- GET  /api/scans/status/{scan_id}  → returns full scan with pages array
- POST /api/scans/stop  → body: { scan_id }

Integration requirements:
1. New Scan form submits to POST /api/scans/start
2. After scan starts, redirect to /scan/:scan_id page
3. On scan detail page, poll GET /api/scans/status/:scan_id every 2.5 seconds
4. Show live progress: pages_found, pages_captured, current_url, status
5. When scan.pages array has items, render screenshots in the grid
6. Screenshot images: use page.screenshot_base64 as: data:image/png;base64,{value}
7. Stop button calls POST /api/scans/stop
8. When status === "completed", stop polling and show full results
9. Handle errors: show red toast if status === "failed" with scan.error_message

Keep all existing UI design exactly the same. Only wire up the real API calls.

*/
