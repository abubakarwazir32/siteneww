from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Railway deploy check karne ke liye"""
    return {"status": "ok", "service": "SiteSnap API"}
