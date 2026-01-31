"""
Booking API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random
import string

router = APIRouter()

# In-memory booking storage for demo
BOOKINGS = {}


class CreateBookingRequest(BaseModel):
    customer_mobile: str
    vehicle_registration: str
    dealer_code: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    service_type: str
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    success: bool
    booking_id: Optional[str] = None
    customer_mobile: Optional[str] = None
    vehicle_registration: Optional[str] = None
    dealer_code: Optional[str] = None
    dealer_name: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    estimated_duration: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[str] = None


def generate_booking_id() -> str:
    """Generate unique booking ID"""
    prefix = "BK"
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{timestamp}{random_part}"


@router.post("/booking/create", response_model=BookingResponse)
async def create_booking(request: CreateBookingRequest):
    """
    Create a new service booking
    """
    # Validate inputs
    if not request.customer_mobile or len(request.customer_mobile) < 10:
        return BookingResponse(
            success=False,
            message="Invalid customer mobile number"
        )
    
    if not request.vehicle_registration:
        return BookingResponse(
            success=False,
            message="Vehicle registration number is required"
        )
    
    if not request.dealer_code:
        return BookingResponse(
            success=False,
            message="Dealer code is required"
        )
    
    # Validate date
    try:
        appointment_date = datetime.strptime(request.appointment_date, "%Y-%m-%d")
        if appointment_date.date() < datetime.now().date():
            return BookingResponse(
                success=False,
                message="Cannot book appointments for past dates"
            )
    except ValueError:
        return BookingResponse(
            success=False,
            message="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Generate booking ID
    booking_id = generate_booking_id()
    
    # Determine dealer name based on code
    dealer_names = {
        "MSIL-PUNE-001": "Maruti Suzuki Arena - Hinjewadi",
        "MSIL-PUNE-002": "Maruti Suzuki NEXA - Baner",
        "MSIL-PUNE-003": "Maruti Suzuki Arena - Kharadi",
        "MSIL-MUM-001": "Maruti Suzuki Arena - Andheri",
        "MSIL-DEL-001": "Maruti Suzuki Arena - Dwarka"
    }
    dealer_name = dealer_names.get(request.dealer_code, f"MSIL Dealer - {request.dealer_code}")
    
    # Estimate duration based on service type
    duration_map = {
        "regular": "3-4 hours",
        "express": "1-2 hours",
        "body_repair": "1-2 days"
    }
    estimated_duration = duration_map.get(request.service_type, "3-4 hours")
    
    # Create booking record
    booking = {
        "booking_id": booking_id,
        "customer_mobile": request.customer_mobile,
        "vehicle_registration": request.vehicle_registration.upper(),
        "dealer_code": request.dealer_code,
        "dealer_name": dealer_name,
        "appointment_date": request.appointment_date,
        "appointment_time": request.appointment_time,
        "service_type": request.service_type,
        "status": "CONFIRMED",
        "estimated_duration": estimated_duration,
        "notes": request.notes,
        "created_at": datetime.now().isoformat()
    }
    
    # Store booking
    BOOKINGS[booking_id] = booking
    
    return BookingResponse(
        success=True,
        booking_id=booking_id,
        customer_mobile=booking["customer_mobile"],
        vehicle_registration=booking["vehicle_registration"],
        dealer_code=booking["dealer_code"],
        dealer_name=booking["dealer_name"],
        appointment_date=booking["appointment_date"],
        appointment_time=booking["appointment_time"],
        service_type=booking["service_type"],
        status=booking["status"],
        estimated_duration=booking["estimated_duration"],
        message=f"Booking confirmed! Your booking ID is {booking_id}. Please arrive at {booking['appointment_time']} on {booking['appointment_date']}.",
        created_at=booking["created_at"]
    )


@router.get("/booking/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str):
    """
    Get booking details by ID
    """
    booking = BOOKINGS.get(booking_id)
    
    if booking:
        return BookingResponse(
            success=True,
            **booking
        )
    else:
        # Return mock booking for demo
        return BookingResponse(
            success=True,
            booking_id=booking_id,
            customer_mobile="9876543210",
            vehicle_registration="MH12AB1234",
            dealer_code="MSIL-PUNE-001",
            dealer_name="Maruti Suzuki Arena - Hinjewadi",
            appointment_date="2026-01-31",
            appointment_time="10:00",
            service_type="regular",
            status="CONFIRMED",
            estimated_duration="3-4 hours",
            message="Booking found",
            created_at=datetime.now().isoformat()
        )
