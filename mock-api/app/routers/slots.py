"""
Slots API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


class AvailableSlotsRequest(BaseModel):
    dealer_code: str
    date: str  # YYYY-MM-DD
    service_type: Optional[str] = "regular"


class TimeSlot(BaseModel):
    slot_id: str
    time: str
    available: bool
    capacity: int
    booked: int


class SlotsResponse(BaseModel):
    success: bool
    dealer_code: str
    date: str
    service_type: str
    slots: List[TimeSlot] = []
    message: Optional[str] = None


@router.post("/slots/available", response_model=SlotsResponse)
async def get_available_slots(request: AvailableSlotsRequest):
    """
    Get available appointment slots for a dealer
    """
    dealer_code = request.dealer_code
    date_str = request.date
    service_type = request.service_type or "regular"
    
    # Validate date
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return SlotsResponse(
                success=False,
                dealer_code=dealer_code,
                date=date_str,
                service_type=service_type,
                message="Cannot book slots for past dates"
            )
    except ValueError:
        return SlotsResponse(
            success=False,
            dealer_code=dealer_code,
            date=date_str,
            service_type=service_type,
            message="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Generate available slots
    slots = []
    times = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"
    ]
    
    # Simulate some slots being booked
    import random
    random.seed(hash(f"{dealer_code}{date_str}"))
    
    for i, time in enumerate(times):
        capacity = 3 if service_type == "express" else 5
        booked = random.randint(0, capacity)
        
        slots.append(TimeSlot(
            slot_id=f"{dealer_code}-{date_str}-{i+1:02d}",
            time=time,
            available=booked < capacity,
            capacity=capacity,
            booked=booked
        ))
    
    return SlotsResponse(
        success=True,
        dealer_code=dealer_code,
        date=date_str,
        service_type=service_type,
        slots=slots
    )
