from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.routes import chat, cases, demand_notice
from backend.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Legal Assistant AI",
    description="AI-powered legal assistant for consumer protection law",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(demand_notice.router, prefix="/api")

# Serve static files (frontend)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Legal Assistant AI"}

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    print("🚀 Legal Assistant AI starting up...")
    print(f"📡 Server running on {settings.host}:{settings.port}")

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )