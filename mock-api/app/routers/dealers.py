"""
Dealers API endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.data.mock_data import DEALERS

router = APIRouter()


class NearbyDealersRequest(BaseModel):
    city: str
    area: Optional[str] = None
    service_type: Optional[str] = "regular"


class Dealer(BaseModel):
    dealer_code: str
    name: str
    address: str
    city: str
    area: str
    distance_km: float
    rating: float
    phone: str
    services: List[str]
    working_hours: str


class DealersResponse(BaseModel):
    success: bool
    dealers: List[Dealer] = []
    total: int = 0
    message: Optional[str] = None


@router.post("/dealers/nearby", response_model=DealersResponse)
async def get_nearby_dealers(request: NearbyDealersRequest):
    """
    Find dealers near a location
    """
    city = request.city.lower().strip()
    area = request.area.lower().strip() if request.area else None
    service_type = request.service_type or "regular"
    
    # Filter dealers by city
    matching_dealers = []
    
    for dealer_code, dealer in DEALERS.items():
        if dealer["city"].lower() == city:
            # Check if dealer provides requested service
            if service_type in dealer["services"]:
                # Calculate mock distance based on area match
                distance = 2.5
                if area and area in dealer["area"].lower():
                    distance = 1.5
                elif not area:
                    distance = 3.0 + (hash(dealer_code) % 10)
                
                matching_dealers.append(Dealer(
                    dealer_code=dealer_code,
                    name=dealer["name"],
                    address=dealer["address"],
                    city=dealer["city"],
                    area=dealer["area"],
                    distance_km=distance,
                    rating=dealer["rating"],
                    phone=dealer["phone"],
                    services=dealer["services"],
                    working_hours=dealer["working_hours"]
                ))
    
    # Sort by distance
    matching_dealers.sort(key=lambda x: x.distance_km)
    
    if not matching_dealers:
        # Return default dealers for demo
        matching_dealers = [
            Dealer(
                dealer_code="MSIL-PUNE-001",
                name="Maruti Suzuki Arena - Hinjewadi",
                address="Plot 45, Phase 1, Hinjewadi IT Park",
                city="Pune",
                area="Hinjewadi",
                distance_km=2.5,
                rating=4.5,
                phone="+91-20-67890123",
                services=["regular", "express", "body_repair"],
                working_hours="9:00 AM - 6:00 PM"
            ),
            Dealer(
                dealer_code="MSIL-PUNE-002",
                name="Maruti Suzuki NEXA - Baner",
                address="Survey 42, Baner Road",
                city="Pune",
                area="Baner",
                distance_km=4.2,
                rating=4.7,
                phone="+91-20-67890124",
                services=["regular", "express"],
                working_hours="9:00 AM - 7:00 PM"
            )
        ]
    
    return DealersResponse(
        success=True,
        dealers=matching_dealers[:5],  # Return top 5
        total=len(matching_dealers)
    )
