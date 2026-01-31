"""
MSIL Mock API Server
Simulates MSIL APIM endpoints for development and testing
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import customer, vehicle, dealers, slots, booking

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="MSIL Mock API",
    version="1.0.0",
    description="Mock API server simulating MSIL APIM endpoints"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customer.router, prefix="/api", tags=["Customer"])
app.include_router(vehicle.router, prefix="/api", tags=["Vehicle"])
app.include_router(dealers.router, prefix="/api", tags=["Dealers"])
app.include_router(slots.router, prefix="/api", tags=["Slots"])
app.include_router(booking.router, prefix="/api", tags=["Booking"])


@app.get("/", tags=["Health"])
async def root():
    """Health check"""
    return {
        "service": "MSIL Mock API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "endpoints": [
            "POST /api/customer/resolve",
            "POST /api/vehicle/resolve",
            "POST /api/dealers/nearby",
            "POST /api/slots/available",
            "POST /api/booking/create",
            "GET /api/booking/{booking_id}"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
