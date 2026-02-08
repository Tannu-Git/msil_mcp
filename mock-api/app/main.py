"""
MSIL Mock API Server
Simulates MSIL APIM endpoints for development and testing
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import customer, vehicle, dealers, slots, booking, appointments

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

# Authentication Middleware - Validate MSIL headers
@app.middleware("http")
async def validate_msil_auth(request: Request, call_next):
    """
    Validate MSIL authentication headers:
    - Always require x-api-key
    - Require Authorization (Bearer token) for write operations
    """
    # Skip validation for health endpoints
    if request.url.path in ["/", "/health"]:
        return await call_next(request)
    
    # Check x-api-key header
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return JSONResponse(
            status_code=403,
            content={
                "data": None,
                "error": True,
                "errors": [{"errorCode": "MISSING_API_KEY", "errorMessage": "x-api-key header is required"}]
            }
        )
    
    # Check Authorization header for write operations
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "data": None,
                    "error": True,
                    "errors": [{"errorCode": "UNAUTHORIZED", "errorMessage": "Authorization header with Bearer token required for write operations"}]
                }
            )
    
    response = await call_next(request)
    return response

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
app.include_router(appointments.router, tags=["Appointments"])


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
            "GET /api/booking/{booking_id}",
            "POST /v1/api/common/msil/dms/appointment-booking",
            "POST /v1/api/common/msil/dms/appointment-booking-hyperlocal",
            "PUT /v1/api/common/msil/dms/update-appointment-booking",
            "DELETE /v1/api/common/msil/dms/cancel-appointment-booking",
            "GET /v1/api/common/msil/dms/appointment-cancel-reasons",
            "POST /v1/api/common/msil/dms/appointment-remainder",
            "GET /v1/api/common/msil/dms/service-appointments",
            "GET /v1/api/common/msil/dms/service-booking-calendar",
            "POST /v1/api/common/msil/dms/service-details"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
