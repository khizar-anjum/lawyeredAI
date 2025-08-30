from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.routes import chat, cases, demand_notice, auth, payment
from backend.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="NYC Legal Assistant AI",
    description="AI-powered legal assistant with authentication and payment processing",
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
app.include_router(auth.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(demand_notice.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NYC Legal Assistant AI"}

@app.get("/login")
async def login_page():
    """Serve login page"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/login.html")

@app.get("/")
async def root():
    """Serve main app page"""
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

# Serve static files (frontend) - but exclude root and login
app.mount("/static", StaticFiles(directory="frontend"), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )