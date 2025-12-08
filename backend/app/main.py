"""
Developer Self-Service Portal - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import services, deployments, environments, secrets, observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Developer Self-Service Portal API",
    description="API for managing services, deployments, environments, secrets, and observability",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include API routers
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["deployments"])
app.include_router(environments.router, prefix="/api/environments", tags=["environments"])
app.include_router(secrets.router, prefix="/api/secrets", tags=["secrets"])
app.include_router(observability.router, prefix="/api", tags=["observability"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

