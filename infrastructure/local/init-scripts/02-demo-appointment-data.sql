-- Demo Appointment Data for MSIL
-- This script populates sample appointment booking data for development and testing

-- Insert demo appointment bookings
INSERT INTO appointment_bookings (
    booking_id, registration_number, appointment_date, appointment_time,
    service_type, preferred_dealer_code, customer_id, status, created_at
) VALUES
-- Upcoming appointments
('APT-2024-001', 'MH01AB1234', '2024-12-20', '10:00', 'Service', 'DLR001', 'CUST001', 'Confirmed', NOW()),
('APT-2024-002', 'KA02CD5678', '2024-12-21', '11:30', 'Maintenance', 'DLR002', 'CUST002', 'Confirmed', NOW()),
('APT-2024-003', 'TN03EF9012', '2024-12-22', '14:00', 'Inspection', 'DLR003', 'CUST003', 'Scheduled', NOW()),
('APT-2024-004', 'DL04GH3456', '2024-12-23', '09:00', 'Service', 'DLR004', 'CUST004', 'Confirmed', NOW()),
-- Past appointments
('APT-2024-005', 'MH05IJ7890', '2024-12-15', '10:00', 'Service', 'DLR001', 'CUST005', 'Completed', NOW()),
('APT-2024-006', 'KA06KL2345', '2024-12-14', '11:30', 'Maintenance', 'DLR002', 'CUST006', 'Completed', NOW()),
-- Cancelled appointment
('APT-2024-007', 'TN07MN6789', '2024-12-10', '15:00', 'Service', 'DLR003', 'CUST007', 'Cancelled', NOW());

-- Insert demo appointment cancellation reasons
INSERT INTO appointment_cancel_reasons (reason_code, reason_description, category) VALUES
('CUST_REQ', 'Customer Request', 'Customer'),
('URGENT_REPAIR', 'Urgent Repair Required', 'Customer'),
('SCHEDULE_CHANGE', 'Schedule Change', 'Customer'),
('DEALER_CLOSED', 'Dealer Closed', 'Dealer'),
('VEHICLE_ISSUE', 'Vehicle Issue', 'Vehicle'),
('WEATHER_DELAY', 'Weather Delay', 'External');

-- Insert demo appointment reminders
INSERT INTO appointment_reminders (
    reminder_id, booking_id, reminder_type, reminder_date_time,
    channel, status, attempt_count, created_at
) VALUES
('REM-001', 'APT-2024-001', 'pre_appointment', '2024-12-19 10:00:00', 'sms', 'Sent', 1, NOW()),
('REM-002', 'APT-2024-001', 'pre_appointment', '2024-12-19 10:00:00', 'email', 'Sent', 1, NOW()),
('REM-003', 'APT-2024-002', 'pre_appointment', '2024-12-20 11:30:00', 'sms', 'Pending', 0, NOW()),
('REM-004', 'APT-2024-003', 'day_before', '2024-12-21 09:00:00', 'email', 'Pending', 0, NOW()),
('REM-005', 'APT-2024-005', 'post_appointment', '2024-12-15 15:00:00', 'email', 'Sent', 1, NOW());

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_booking_id ON appointment_bookings(booking_id);
CREATE INDEX IF NOT EXISTS idx_registration_number ON appointment_bookings(registration_number);
CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointment_bookings(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointment_bookings(status);
CREATE INDEX IF NOT EXISTS idx_reminder_booking_id ON appointment_reminders(booking_id);
