"""Main FastAPI application for DING REST API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import users, config, jobs
from core.database import init_db, init_default_config


# Create FastAPI app
app = FastAPI(
    title="DING API",
    description="REST API for DING - Retro Receipt Printer Web Interface",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(config.router)
app.include_router(jobs.router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    init_default_config()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "DING API is running"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to DING API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8508)
