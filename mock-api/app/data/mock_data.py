"""
Mock data for MSIL API simulation
"""

# Customer data
CUSTOMERS = {
    "9876543210": {
        "customer_id": "CUST001234",
        "name": "Rahul Sharma",
        "mobile": "9876543210",
        "email": "rahul.sharma@email.com",
        "address": "Flat 302, Green Valley Apartments, Hinjewadi",
        "city": "Pune"
    },
    "9876543211": {
        "customer_id": "CUST001235",
        "name": "Priya Patel",
        "mobile": "9876543211",
        "email": "priya.patel@email.com",
        "address": "House 45, Sector 7, Baner",
        "city": "Pune"
    },
    "9876543212": {
        "customer_id": "CUST001236",
        "name": "Amit Kumar",
        "mobile": "9876543212",
        "email": "amit.kumar@email.com",
        "address": "B-201, Tech Park Residency, Whitefield",
        "city": "Bangalore"
    },
    "9123456789": {
        "customer_id": "CUST001237",
        "name": "Demo User",
        "mobile": "9123456789",
        "email": "demo@msil.com",
        "address": "Demo Address, Hinjewadi",
        "city": "Pune"
    }
}

# Vehicle data
VEHICLES = {
    "MH12AB1234": {
        "vehicle_id": "VEH001234",
        "registration_number": "MH12AB1234",
        "model": "Maruti Suzuki Swift",
        "variant": "ZXI+",
        "color": "Pearl White",
        "year": 2023,
        "fuel_type": "Petrol",
        "last_service_date": "2025-07-15",
        "next_service_due": "2026-01-15",
        "odometer_reading": 18500
    },
    "MH12CD5678": {
        "vehicle_id": "VEH001235",
        "registration_number": "MH12CD5678",
        "model": "Maruti Suzuki Baleno",
        "variant": "Alpha",
        "color": "Nexa Blue",
        "year": 2024,
        "fuel_type": "Petrol",
        "last_service_date": "2025-10-20",
        "next_service_due": "2026-04-20",
        "odometer_reading": 8200
    },
    "MH14EF9012": {
        "vehicle_id": "VEH001236",
        "registration_number": "MH14EF9012",
        "model": "Maruti Suzuki Brezza",
        "variant": "ZXI+ AT",
        "color": "Splendid Silver",
        "year": 2022,
        "fuel_type": "Petrol",
        "last_service_date": "2025-09-10",
        "next_service_due": "2026-03-10",
        "odometer_reading": 32000
    },
    "KA01MN3456": {
        "vehicle_id": "VEH001237",
        "registration_number": "KA01MN3456",
        "model": "Maruti Suzuki Ertiga",
        "variant": "VXI CNG",
        "color": "Auburn Red",
        "year": 2023,
        "fuel_type": "Petrol + CNG",
        "last_service_date": "2025-11-05",
        "next_service_due": "2026-05-05",
        "odometer_reading": 25000
    },
    "DL8CAB7890": {
        "vehicle_id": "VEH001238",
        "registration_number": "DL8CAB7890",
        "model": "Maruti Suzuki Dzire",
        "variant": "ZXI",
        "color": "Magma Grey",
        "year": 2024,
        "fuel_type": "Petrol",
        "last_service_date": "2025-12-01",
        "next_service_due": "2026-06-01",
        "odometer_reading": 5500
    }
}

# Dealer data
DEALERS = {
    "MSIL-PUNE-001": {
        "name": "Maruti Suzuki Arena - Hinjewadi",
        "address": "Plot 45, Phase 1, Hinjewadi IT Park, Pune - 411057",
        "city": "Pune",
        "area": "Hinjewadi",
        "rating": 4.5,
        "phone": "+91-20-67890123",
        "services": ["regular", "express", "body_repair"],
        "working_hours": "9:00 AM - 6:00 PM"
    },
    "MSIL-PUNE-002": {
        "name": "Maruti Suzuki NEXA - Baner",
        "address": "Survey 42, Baner Road, Near Orchid School, Pune - 411045",
        "city": "Pune",
        "area": "Baner",
        "rating": 4.7,
        "phone": "+91-20-67890124",
        "services": ["regular", "express"],
        "working_hours": "9:00 AM - 7:00 PM"
    },
    "MSIL-PUNE-003": {
        "name": "Maruti Suzuki Arena - Kharadi",
        "address": "EON IT Park Road, Kharadi, Pune - 411014",
        "city": "Pune",
        "area": "Kharadi",
        "rating": 4.3,
        "phone": "+91-20-67890125",
        "services": ["regular", "express", "body_repair"],
        "working_hours": "9:00 AM - 6:00 PM"
    },
    "MSIL-PUNE-004": {
        "name": "Maruti Suzuki Arena - Wakad",
        "address": "Datta Mandir Road, Wakad, Pune - 411057",
        "city": "Pune",
        "area": "Wakad",
        "rating": 4.4,
        "phone": "+91-20-67890126",
        "services": ["regular", "express"],
        "working_hours": "9:00 AM - 6:00 PM"
    },
    "MSIL-MUM-001": {
        "name": "Maruti Suzuki Arena - Andheri",
        "address": "Link Road, Andheri West, Mumbai - 400053",
        "city": "Mumbai",
        "area": "Andheri",
        "rating": 4.6,
        "phone": "+91-22-67890127",
        "services": ["regular", "express", "body_repair"],
        "working_hours": "9:00 AM - 7:00 PM"
    },
    "MSIL-BLR-001": {
        "name": "Maruti Suzuki Arena - Whitefield",
        "address": "ITPL Main Road, Whitefield, Bangalore - 560066",
        "city": "Bangalore",
        "area": "Whitefield",
        "rating": 4.5,
        "phone": "+91-80-67890128",
        "services": ["regular", "express", "body_repair"],
        "working_hours": "9:00 AM - 6:00 PM"
    },
    "MSIL-DEL-001": {
        "name": "Maruti Suzuki Arena - Dwarka",
        "address": "Sector 12, Dwarka, New Delhi - 110078",
        "city": "Delhi",
        "area": "Dwarka",
        "rating": 4.4,
        "phone": "+91-11-67890129",
        "services": ["regular", "express", "body_repair"],
        "working_hours": "9:00 AM - 6:00 PM"
    }
}
