from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import scans, health

app = FastAPI(
    title="SiteSnap API",
    description="Website crawler & screenshot backend",
    version="1.0.0"
)

# CORS — Lovable frontend ko allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production mein apna Lovable domain dalo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes register karo
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(scans.router, prefix="/api/scans", tags=["Scans"])
