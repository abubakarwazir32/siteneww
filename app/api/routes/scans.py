"""
Scan Routes — Lovable frontend yahan call karega
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.scan import ScanCreateRequest, ScanResponse, ScanStopRequest
from app.services import crawler

router = APIRouter()


@router.post("/start", response_model=ScanResponse)
async def start_scan(
    request: ScanCreateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Naya scan shuru karo.
    Scan ID turant return hoti hai — crawling background mein chalta hai.
    Frontend polling se /status/{scan_id} check karta rahe.
    """
    # Scan entry banao
    scan_id = crawler.create_scan(request)

    # Background mein crawler chalaao (non-blocking)
    background_tasks.add_task(crawler.run_scan, scan_id, request)

    # Turant pending state return karo
    scan = crawler.get_scan(scan_id)
    return scan


@router.get("/status/{scan_id}", response_model=ScanResponse)
async def get_scan_status(scan_id: str):
    """
    Scan ka live status aur captured pages lao.
    Frontend har 2-3 second mein yeh endpoint poll kare.
    """
    scan = crawler.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("/stop", response_model=dict)
async def stop_scan(request: ScanStopRequest):
    """
    Chal rahe scan ko rokao.
    """
    success = crawler.stop_scan(request.scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"message": "Stop signal sent", "scan_id": request.scan_id}


@router.get("/list", response_model=list[ScanResponse])
async def list_scans():
    """
    Abhi memory mein saare scans (production mein DB se aayenge)
    """
    # _scans private hai, isliye crawler module se access karo
    from app.services.crawler import _scans
    return list(_scans.values())
