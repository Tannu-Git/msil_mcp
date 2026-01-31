"""
Customer API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.data.mock_data import CUSTOMERS

router = APIRouter()


class CustomerResolveRequest(BaseModel):
    mobile: str


class CustomerResponse(BaseModel):
    success: bool
    customer_id: Optional[str] = None
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    message: Optional[str] = None


@router.post("/customer/resolve", response_model=CustomerResponse)
async def resolve_customer(request: CustomerResolveRequest):
    """
    Resolve customer details from mobile number
    """
    mobile = request.mobile.replace(" ", "").replace("-", "")
    
    # Remove country code if present
    if mobile.startswith("+91"):
        mobile = mobile[3:]
    if mobile.startswith("91") and len(mobile) == 12:
        mobile = mobile[2:]
    
    # Validate mobile number
    if len(mobile) != 10 or not mobile.isdigit():
        return CustomerResponse(
            success=False,
            message="Invalid mobile number format. Please provide a 10-digit mobile number."
        )
    
    # Look up customer
    customer = CUSTOMERS.get(mobile)
    
    if customer:
        return CustomerResponse(
            success=True,
            customer_id=customer["customer_id"],
            name=customer["name"],
            mobile=customer["mobile"],
            email=customer["email"],
            address=customer["address"],
            city=customer["city"]
        )
    else:
        # For demo, create a mock customer for any valid mobile
        return CustomerResponse(
            success=True,
            customer_id=f"CUST{mobile[-6:]}",
            name="Demo Customer",
            mobile=mobile,
            email=f"customer{mobile[-4:]}@email.com",
            address="Demo Address",
            city="Pune"
        )
