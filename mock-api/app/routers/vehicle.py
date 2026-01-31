"""
Vehicle API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import re

from app.data.mock_data import VEHICLES

router = APIRouter()


class VehicleResolveRequest(BaseModel):
    registration_number: str


class VehicleResponse(BaseModel):
    success: bool
    vehicle_id: Optional[str] = None
    registration_number: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    color: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    last_service_date: Optional[str] = None
    next_service_due: Optional[str] = None
    odometer_reading: Optional[int] = None
    message: Optional[str] = None


@router.post("/vehicle/resolve", response_model=VehicleResponse)
async def resolve_vehicle(request: VehicleResolveRequest):
    """
    Get vehicle details from registration number
    """
    reg_number = request.registration_number.upper().replace(" ", "").replace("-", "")
    
    # Validate registration format (basic Indian format)
    pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}$'
    if not re.match(pattern, reg_number):
        return VehicleResponse(
            success=False,
            message="Invalid registration number format. Expected format: MH12AB1234"
        )
    
    # Look up vehicle
    vehicle = VEHICLES.get(reg_number)
    
    if vehicle:
        return VehicleResponse(
            success=True,
            vehicle_id=vehicle["vehicle_id"],
            registration_number=vehicle["registration_number"],
            model=vehicle["model"],
            variant=vehicle["variant"],
            color=vehicle["color"],
            year=vehicle["year"],
            fuel_type=vehicle["fuel_type"],
            last_service_date=vehicle["last_service_date"],
            next_service_due=vehicle["next_service_due"],
            odometer_reading=vehicle["odometer_reading"]
        )
    else:
        # For demo, create mock vehicle for any valid registration
        models = ["Swift", "Baleno", "Brezza", "Dzire", "Ertiga", "XL6"]
        import random
        model = random.choice(models)
        
        return VehicleResponse(
            success=True,
            vehicle_id=f"VEH{reg_number[-6:]}",
            registration_number=reg_number,
            model=f"Maruti Suzuki {model}",
            variant="ZXI+",
            color="Pearl White",
            year=2023,
            fuel_type="Petrol",
            last_service_date="2025-10-15",
            next_service_due="2026-04-15",
            odometer_reading=15000
        )
