"""
MSIL DMS API Standard Request/Response Models
Aligned with MSIL Swagger specification
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, time


# ============================================
# STANDARD RESPONSE MODELS
# ============================================

class MsilError(BaseModel):
    """MSIL standard error format"""
    errorCode: str
    errorMessage: str


class MsilStandardResponse(BaseModel):
    """MSIL standard response wrapper"""
    data: Optional[Any] = None
    error: bool = False
    errors: List[MsilError] = []


# ============================================
# APPOINTMENT BOOKING MODELS
# ============================================

class AppointmentBookingRequest(BaseModel):
    """Standard appointment booking request (Swagger aligned)"""
    regNo: str = Field(..., description="Vehicle registration number e.g., DL3CCA1985")
    dealerCode: str = Field(..., description="Dealer code e.g., 10744")
    locCode: str = Field(..., description="Location code e.g., OKF")
    appointmentDate: str = Field(..., description="Appointment date in format DD-MMM-YYYY e.g., 25-JUL-2022")
    slotCode: str = Field(..., description="Slot code e.g., 1100-1300")
    slotTimeCode: str = Field(..., description="Slot time code e.g., 1230-1245")
    appointmentTypeCode: str = Field(..., description="Appointment type code e.g., PRM")
    srvTypeCode: str = Field(..., description="Service type code e.g., RR")
    currentSaCode: str = Field(..., description="Service advisor code e.g., 0147")
    odoMeter: str = Field(..., description="Odometer reading")
    userId: str = Field(..., description="User ID who is booking")
    mobileNo: Optional[str] = Field(None, description="Mobile number")
    pickUpType: Optional[str] = Field(None, description="Pickup type")
    pickUpLoc: Optional[str] = Field(None, description="Pickup location")
    pickUpAddress: Optional[str] = Field(None, description="Pickup address")
    pickUpTime: Optional[str] = Field(None, description="Pickup time")
    pickUpRemarks: Optional[str] = Field(None, description="Pickup remarks")
    driver: Optional[str] = Field(None, description="Driver details")
    vehicleNo: Optional[str] = Field(None, description="Service vehicle number")
    dropLoc: Optional[str] = Field(None, description="Drop location")
    dropAddress: Optional[str] = Field(None, description="Drop address")
    dropTime: Optional[str] = Field(None, description="Drop time")
    dropDriver: Optional[str] = Field(None, description="Drop driver")
    demandJobs: Optional[str] = Field(None, description="Demand jobs")
    remarkNonPrevSa: Optional[str] = Field(None, description="Non previous SA remarks")


class HyperLocalBookingRequest(AppointmentBookingRequest):
    """Hyperlocal booking with PSF number"""
    psfNum: str = Field(..., description="PSF number for hyperlocal booking")


class UpdateAppointmentBookingRequest(BaseModel):
    """Update appointment booking request"""
    appointmentNo: str = Field(..., description="Appointment number to update")
    dealerCode: str
    locCode: str
    userId: str
    appointmentDate: Optional[str] = None
    slotCode: Optional[str] = None
    slotTimeCode: Optional[str] = None
    appointmentTypeCode: Optional[str] = None
    srvTypeCode: Optional[str] = None
    currentSaCode: Optional[str] = None
    odoMeter: Optional[str] = None
    pickUpType: Optional[str] = None
    pickUpLoc: Optional[str] = None
    pickUpAddress: Optional[str] = None
    pickUpTime: Optional[str] = None
    pickUpRemarks: Optional[str] = None
    demandJobs: Optional[str] = None
    remarkNonPrevSa: Optional[str] = None


class AppointmentReminderRequest(BaseModel):
    """Send appointment reminder request"""
    appointmentNo: str = Field(..., description="Appointment number")
    mobile: str = Field(..., description="Customer mobile number")
    email: Optional[str] = Field(None, description="Customer email")
    reminderType: str = Field(default="SMS", description="Reminder type: SMS, EMAIL, BOTH")


class ServiceDetailRequest(BaseModel):
    """Service details request"""
    dealerCode: str
    locCode: str
    srvTypeCode: Optional[str] = None
    modelCode: Optional[str] = None


# ============================================
# APPOINTMENT RESPONSE MODELS
# ============================================

class AppointmentData(BaseModel):
    """Appointment data in response"""
    appointmentNo: str
    bookingId: str
    customerMobile: str
    customerName: Optional[str] = None
    vehicleRegistration: str
    vehicleModel: Optional[str] = None
    dealerCode: str
    dealerName: str
    locCode: str
    locationName: Optional[str] = None
    appointmentDate: str
    slotCode: str
    slotTimeCode: str
    appointmentTypeCode: str
    srvTypeCode: str
    currentSaCode: str
    saName: Optional[str] = None
    odoMeter: str
    status: str
    estimatedDuration: Optional[str] = None
    createdAt: str
    updatedAt: Optional[str] = None


class AppointmentListData(BaseModel):
    """List of appointments with pagination"""
    appointments: List[AppointmentData]
    totalCount: int
    pageNo: int
    pageSize: int
    totalPages: int


class CancellationReason(BaseModel):
    """Cancellation reason"""
    code: str
    reason: str
    description: Optional[str] = None


class ServiceType(BaseModel):
    """Service type details"""
    code: str
    name: str
    description: str
    estimatedDuration: str
    availableAt: List[str]  # List of channels: NRM, EXC, COM


class TimeSlot(BaseModel):
    """Time slot information"""
    slotCode: str
    slotTimeCode: str
    startTime: str
    endTime: str
    available: bool
    capacity: int
    booked: int


class CalendarDay(BaseModel):
    """Calendar day with slot availability"""
    date: str  # DD-MMM-YYYY
    dayOfWeek: str
    isWorkingDay: bool
    slots: List[TimeSlot]


# ============================================
# QUERY PARAMETERS
# ============================================

class AppointmentListQuery(BaseModel):
    """Query parameters for listing appointments"""
    customerMobile: Optional[str] = None
    dealerCode: Optional[str] = None
    locCode: Optional[str] = None
    status: Optional[str] = None
    fromDate: Optional[str] = None  # DD-MMM-YYYY
    toDate: Optional[str] = None  # DD-MMM-YYYY
    pageNo: int = 1
    pageSize: int = 10
    sortBy: Optional[str] = "appointmentDate"
    sortOrder: Optional[str] = "DESC"
