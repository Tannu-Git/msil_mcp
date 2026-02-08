"""
Models package for mock API
"""
from .msil_models import (
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
    CalendarDay,
    AppointmentListQuery
)

__all__ = [
    "MsilStandardResponse",
    "MsilError",
    "AppointmentBookingRequest",
    "HyperLocalBookingRequest",
    "UpdateAppointmentBookingRequest",
    "AppointmentReminderRequest",
    "ServiceDetailRequest",
    "AppointmentData",
    "AppointmentListData",
    "CancellationReason",
    "ServiceType",
    "TimeSlot",
    "CalendarDay",
    "AppointmentListQuery"
]
