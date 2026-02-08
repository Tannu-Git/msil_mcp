"""
MSIL DMS Appointment API Endpoints
Aligned with Swagger specification: msil-common-sam-preprod-dms-preprod-swagger.json
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional
from datetime import datetime, timedelta
import random
import string

from app.models.msil_models import (
    MsilStandardResponse,
    MsilError,
    AppointmentBookingRequest,
    HyperLocalBookingRequest,
    UpdateAppointmentBookingRequest,
    AppointmentReminderRequest,
    ServiceDetailRequest,
    AppointmentData,
    AppointmentListData,
    CancellationReason,
    ServiceType,
    TimeSlot,
    CalendarDay
)

router = APIRouter()

# In-memory storage for demo
APPOINTMENTS = {}
APPOINTMENT_COUNTER = 22005900


def generate_appointment_no() -> str:
    """Generate MSIL-style appointment number"""
    global APPOINTMENT_COUNTER
    APPOINTMENT_COUNTER += 1
    return f"SB{APPOINTMENT_COUNTER}"


def parse_msil_date(date_str: str) -> datetime:
    """Parse MSIL date format: DD-MMM-YYYY"""
    try:
        return datetime.strptime(date_str, "%d-%b-%Y")
    except:
        # Fallback to ISO format
        return datetime.fromisoformat(date_str)


def format_msil_date(dt: datetime) -> str:
    """Format date to MSIL format: DD-MMM-YYYY"""
    return dt.strftime("%d-%b-%Y").upper()


# ============================================
# 1. POST /v1/api/common/msil/dms/appointment-booking
# ============================================

@router.post("/v1/api/common/msil/dms/appointment-booking")
async def appointment_booking(
    request: AppointmentBookingRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Book service appointment (Standard flow)
    """
    try:
        # Validate date
        try:
            appt_date = parse_msil_date(request.appointmentDate)
            if appt_date.date() < datetime.now().date():
                return MsilStandardResponse(
                    data=None,
                    error=True,
                    errors=[MsilError(
                        errorCode="INVALID_DATE",
                        errorMessage="Cannot book appointments for past dates"
                    )]
                ).dict()
        except Exception as e:
            return MsilStandardResponse(
                data=None,
                error=True,
                errors=[MsilError(
                    errorCode="DATE_PARSE_ERROR",
                    errorMessage=f"Invalid date format. Use DD-MMM-YYYY"
                )]
            ).dict()
        
        # Generate appointment number
        appointment_no = generate_appointment_no()
        booking_id = f"BK{datetime.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
        
        # Mock dealer data
        dealer_names = {
            "10744": "Vipul Maruti - Okhla",
            "10266": "Saboo RKS Motor - Nacharam",
            "11037": "FSM Motors - Delhi",
            "5303": "Pristine Autotech - Mumbai"
        }
        dealer_name = dealer_names.get(request.dealerCode, f"MSIL Dealer - {request.dealerCode}")
        
        # Create appointment record
        appointment = AppointmentData(
            appointmentNo=appointment_no,
            bookingId=booking_id,
            customerMobile=request.mobileNo or "9876543210",
            customerName="Customer",
            vehicleRegistration=request.regNo,
            vehicleModel="Maruti Swift",
            dealerCode=request.dealerCode,
            dealerName=dealer_name,
            locCode=request.locCode,
            locationName=f"Location {request.locCode}",
            appointmentDate=request.appointmentDate,
            slotCode=request.slotCode,
            slotTimeCode=request.slotTimeCode,
            appointmentTypeCode=request.appointmentTypeCode,
            srvTypeCode=request.srvTypeCode,
            currentSaCode=request.currentSaCode,
            saName=f"Service Advisor {request.currentSaCode}",
            odoMeter=request.odoMeter,
            status="CONFIRMED",
            estimatedDuration="3-4 hours",
            createdAt=datetime.now().isoformat(),
            updatedAt=None
        )
        
        # Store
        APPOINTMENTS[appointment_no] = appointment.dict()
        
        return MsilStandardResponse(
            data=appointment.dict(),
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(
                errorCode="BOOKING_FAILED",
                errorMessage=str(e)
            )]
        ).dict()


# ============================================
# 2. POST /v1/api/common/msil/dms/appointment-booking-hyperlocal
# ============================================

@router.post("/v1/api/common/msil/dms/appointment-booking-hyperlocal")
async def appointment_booking_hyperlocal(
    request: HyperLocalBookingRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Book service appointment with PSF (Hyperlocal flow)
    """
    try:
        # Reuse standard booking logic
        appointment_no = generate_appointment_no()
        booking_id = f"BK{datetime.now().strftime('%y%m%d')}{random.randint(1000, 9999)}"
        
        appointment = AppointmentData(
            appointmentNo=appointment_no,
            bookingId=booking_id,
            customerMobile=request.mobileNo or "9876543210",
            customerName="Customer (Hyperlocal)",
            vehicleRegistration=request.regNo,
            vehicleModel="Maruti Swift",
            dealerCode=request.dealerCode,
            dealerName=f"MSIL Dealer - {request.dealerCode}",
            locCode=request.locCode,
            locationName=f"Location {request.locCode}",
            appointmentDate=request.appointmentDate,
            slotCode=request.slotCode,
            slotTimeCode=request.slotTimeCode,
            appointmentTypeCode=request.appointmentTypeCode,
            srvTypeCode=request.srvTypeCode,
            currentSaCode=request.currentSaCode,
            saName=f"SA {request.currentSaCode}",
            odoMeter=request.odoMeter,
            status="CONFIRMED",
            estimatedDuration="2-3 hours",
            createdAt=datetime.now().isoformat(),
            updatedAt=None
        )
        
        APPOINTMENTS[appointment_no] = appointment.dict()
        
        return MsilStandardResponse(
            data={**appointment.dict(), "psfNum": request.psfNum},
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="HYPERLOCAL_BOOKING_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 3. PUT /v1/api/common/msil/dms/update-appointment-booking
# ============================================

@router.put("/v1/api/common/msil/dms/update-appointment-booking")
async def update_appointment_booking(
    request: UpdateAppointmentBookingRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Update existing appointment
    """
    try:
        if request.appointmentNo not in APPOINTMENTS:
            return MsilStandardResponse(
                data=None,
                error=True,
                errors=[MsilError(
                    errorCode="APPOINTMENT_NOT_FOUND",
                    errorMessage=f"Appointment {request.appointmentNo} not found"
                )]
            ).dict()
        
        appointment = APPOINTMENTS[request.appointmentNo]
        
        # Update fields
        if request.appointmentDate:
            appointment["appointmentDate"] = request.appointmentDate
        if request.slotCode:
            appointment["slotCode"] = request.slotCode
        if request.slotTimeCode:
            appointment["slotTimeCode"] = request.slotTimeCode
        if request.currentSaCode:
            appointment["currentSaCode"] = request.currentSaCode
        if request.odoMeter:
            appointment["odoMeter"] = request.odoMeter
        
        appointment["updatedAt"] = datetime.now().isoformat()
        appointment["status"] = "UPDATED"
        
        APPOINTMENTS[request.appointmentNo] = appointment
        
        return MsilStandardResponse(
            data=appointment,
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="UPDATE_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 4. DELETE /v1/api/common/msil/dms/cancel-appointment-booking
# ============================================

@router.delete("/v1/api/common/msil/dms/cancel-appointment-booking")
async def cancel_appointment_booking(
    appointmentNo: str = Query(..., description="Appointment number"),
    cancelReason: str = Query(..., description="Cancellation reason"),
    dealerCode: str = Query(...),
    locCd: str = Query(...),
    userId: str = Query(...),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Cancel appointment booking
    """
    try:
        if appointmentNo not in APPOINTMENTS:
            return MsilStandardResponse(
                data=None,
                error=True,
                errors=[MsilError(
                    errorCode="APPOINTMENT_NOT_FOUND",
                    errorMessage=f"Appointment {appointmentNo} not found"
                )]
            ).dict()
        
        appointment = APPOINTMENTS[appointmentNo]
        appointment["status"] = "CANCELLED"
        appointment["updatedAt"] = datetime.now().isoformat()
        appointment["cancellationReason"] = cancelReason
        appointment["cancelledBy"] = userId
        
        APPOINTMENTS[appointmentNo] = appointment
        
        return MsilStandardResponse(
            data={
                "appointmentNo": appointmentNo,
                "status": "CANCELLED",
                "cancelReason": cancelReason,
                "message": "Appointment cancelled successfully"
            },
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="CANCELLATION_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 5. GET /v1/api/common/msil/dms/appointment-cancel-reasons
# ============================================

@router.get("/v1/api/common/msil/dms/appointment-cancel-reasons")
async def get_cancel_reasons(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Get list of cancellation reasons
    """
    reasons = [
        CancellationReason(code="RESCHEDULED", reason="Want to reschedule", description="Customer wants different date/time"),
        CancellationReason(code="EMERGENCY", reason="Personal emergency", description="Urgent personal matter"),
        CancellationReason(code="VEHICLE_NOT_READY", reason="Vehicle not ready", description="Vehicle preparation issue"),
        CancellationReason(code="COST_CONCERN", reason="Cost concerns", description="Service cost related"),
        CancellationReason(code="BOOKED_ELSEWHERE", reason="Booked at another dealer", description="Found alternative service"),
        CancellationReason(code="TRAVEL", reason="Out of town", description="Customer traveling"),
        CancellationReason(code="OTHER", reason="Other reasons", description="Other unspecified reasons")
    ]
    
    return MsilStandardResponse(
        data=[r.dict() for r in reasons],
        error=False,
        errors=[]
    ).dict()


# ============================================
# 6. POST /v1/api/common/msil/dms/appointment-remainder
# ============================================

@router.post("/v1/api/common/msil/dms/appointment-remainder")
async def send_appointment_reminder(
    request: AppointmentReminderRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Send appointment reminder (SMS/Email)
    """
    try:
        if request.appointmentNo not in APPOINTMENTS:
            return MsilStandardResponse(
                data=None,
                error=True,
                errors=[MsilError(errorCode="APPOINTMENT_NOT_FOUND", errorMessage="Appointment not found")]
            ).dict()
        
        appointment = APPOINTMENTS[request.appointmentNo]
        
        return MsilStandardResponse(
            data={
                "appointmentNo": request.appointmentNo,
                "reminderSent": True,
                "reminderType": request.reminderType,
                "sentTo": request.mobile,
                "message": f"Reminder sent successfully via {request.reminderType}",
                "timestamp": datetime.now().isoformat()
            },
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="REMINDER_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 7. GET /v1/api/common/msil/dms/service-appointments
# ============================================

@router.get("/v1/api/common/msil/dms/service-appointments")
async def list_service_appointments(
    customerMobile: Optional[str] = Query(None),
    dealerCode: Optional[str] = Query(None),
    locCode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    fromDate: Optional[str] = Query(None),
    toDate: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    List service appointments with filtering and pagination
    """
    try:
        # Filter appointments
        filtered = list(APPOINTMENTS.values())
        
        if customerMobile:
            filtered = [a for a in filtered if a.get("customerMobile") == customerMobile]
        if dealerCode:
            filtered = [a for a in filtered if a.get("dealerCode") == dealerCode]
        if locCode:
            filtered = [a for a in filtered if a.get("locCode") == locCode]
        if status:
            filtered = [a for a in filtered if a.get("status") == status]
        
        # Date filtering
        if fromDate:
            from_dt = parse_msil_date(fromDate)
            filtered = [a for a in filtered if parse_msil_date(a.get("appointmentDate", "01-JAN-2026")) >= from_dt]
        if toDate:
            to_dt = parse_msil_date(toDate)
            filtered = [a for a in filtered if parse_msil_date(a.get("appointmentDate", "01-JAN-2026")) <= to_dt]
        
        # Pagination
        total_count = len(filtered)
        total_pages = (total_count + pageSize - 1) // pageSize
        start_idx = (pageNo - 1) * pageSize
        end_idx = start_idx + pageSize
        paginated = filtered[start_idx:end_idx]
        
        result = AppointmentListData(
            appointments=paginated,
            totalCount=total_count,
            pageNo=pageNo,
            pageSize=pageSize,
            totalPages=total_pages
        )
        
        return MsilStandardResponse(
            data=result.dict(),
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="LIST_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 8. GET /v1/api/common/msil/dms/service-booking-calendar
# ============================================

@router.get("/v1/api/common/msil/dms/service-booking-calendar")
async def get_booking_calendar(
    dealerCode: str = Query(...),
    date: str = Query(..., description="Date in DD-MMM-YYYY format"),
    serviceType: Optional[str] = Query(None),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Get available slots for a specific date
    """
    try:
        target_date = parse_msil_date(date)
        
        # Generate slots for the day
        slots = []
        time_slots = [
            ("0900-1100", "0900-0915"),
            ("0900-1100", "0945-1000"),
            ("0900-1100", "1030-1045"),
            ("1100-1300", "1100-1115"),
            ("1100-1300", "1145-1200"),
            ("1100-1300", "1230-1245"),
            ("1400-1600", "1400-1415"),
            ("1400-1600", "1445-1500"),
            ("1400-1600", "1530-1545"),
            ("1600-1800", "1600-1615"),
            ("1600-1800", "1645-1700"),
            ("1600-1800", "1730-1745"),
        ]
        
        for slot_code, slot_time_code in time_slots:
            # Random availability
            capacity = 5
            booked = random.randint(0, 5)
            
            slots.append(TimeSlot(
                slotCode=slot_code,
                slotTimeCode=slot_time_code,
                startTime=slot_time_code.split("-")[0],
                endTime=slot_time_code.split("-")[1],
                available=booked < capacity,
                capacity=capacity,
                booked=booked
            ))
        
        calendar_day = CalendarDay(
            date=format_msil_date(target_date),
            dayOfWeek=target_date.strftime("%A"),
            isWorkingDay=target_date.weekday() < 6,  # Mon-Sat
            slots=slots
        )
        
        return MsilStandardResponse(
            data=calendar_day.dict(),
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="CALENDAR_FETCH_FAILED", errorMessage=str(e))]
        ).dict()


# ============================================
# 9. POST /v1/api/common/msil/dms/service-details
# ============================================

@router.post("/v1/api/common/msil/dms/service-details")
async def get_service_details(
    request: ServiceDetailRequest,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed service information
    """
    try:
        service_types = [
            ServiceType(
                code="RR",
                name="Regular Service",
                description="Routine maintenance and inspection",
                estimatedDuration="3-4 hours",
                availableAt=["NRM", "EXC", "COM"]
            ),
            ServiceType(
                code="PRM",
                name="Premium Service",
                description="Comprehensive service with detailed inspection",
                estimatedDuration="5-6 hours",
                availableAt=["NRM", "EXC"]
            ),
            ServiceType(
                code="ES",
                name="Express Service",
                description="Quick service for minor maintenance",
                estimatedDuration="1-2 hours",
                availableAt=["NRM", "EXC", "COM"]
            ),
            ServiceType(
                code="BR",
                name="Body Repair",
                description="Accident repair and painting",
                estimatedDuration="2-3 days",
                availableAt=["NRM", "EXC"]
            )
        ]
        
        # Filter by service type if requested
        if request.srvTypeCode:
            service_types = [s for s in service_types if s.code == request.srvTypeCode]
        
        return MsilStandardResponse(
            data={
                "dealerCode": request.dealerCode,
                "locCode": request.locCode,
                "serviceTypes": [s.dict() for s in service_types]
            },
            error=False,
            errors=[]
        ).dict()
    
    except Exception as e:
        return MsilStandardResponse(
            data=None,
            error=True,
            errors=[MsilError(errorCode="SERVICE_DETAILS_FAILED", errorMessage=str(e))]
        ).dict()
