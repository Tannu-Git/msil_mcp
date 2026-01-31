import React, { useState } from 'react';
import { Calendar, MapPin, Wrench, Car, User, Phone, Mail, CheckCircle, ArrowLeft, ArrowRight } from 'lucide-react';

interface BookingData {
  // Step 1: Vehicle
  vehicleModel: string;
  registrationNumber: string;
  
  // Step 2: Service
  serviceType: string;
  serviceDate: string;
  preferredTime: string;
  
  // Step 3: Dealer
  dealerCode: string;
  dealerName: string;
  dealerAddress: string;
  
  // Step 4: Customer
  customerName: string;
  customerPhone: string;
  customerEmail: string;
  additionalNotes: string;
}

export default function ServiceBookingWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [bookingData, setBookingData] = useState<BookingData>({
    vehicleModel: '',
    registrationNumber: '',
    serviceType: '',
    serviceDate: '',
    preferredTime: '',
    dealerCode: '',
    dealerName: '',
    dealerAddress: '',
    customerName: '',
    customerPhone: '',
    customerEmail: '',
    additionalNotes: ''
  });
  const [submitted, setSubmitted] = useState(false);

  const updateData = (field: keyof BookingData, value: string) => {
    setBookingData(prev => ({ ...prev, [field]: value }));
  };

  const nextStep = () => {
    if (currentStep < 4) setCurrentStep(prev => prev + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = () => {
    console.log('Booking submitted:', bookingData);
    setSubmitted(true);
  };

  const steps = [
    { number: 1, title: 'Vehicle', icon: Car },
    { number: 2, title: 'Service', icon: Wrench },
    { number: 3, title: 'Dealer', icon: MapPin },
    { number: 4, title: 'Customer', icon: User }
  ];

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Booking Confirmed!</h2>
          <p className="text-gray-600 mb-2">Your service booking has been successfully created.</p>
          <p className="text-gray-600 mb-6">Booking ID: <span className="font-mono font-semibold">BK{Date.now().toString().slice(-8)}</span></p>
          
          <div className="bg-gray-50 rounded-lg p-6 text-left mb-6">
            <h3 className="font-semibold text-gray-900 mb-3">Booking Details:</h3>
            <div className="space-y-2 text-sm">
              <p><span className="font-medium">Vehicle:</span> {bookingData.vehicleModel} ({bookingData.registrationNumber})</p>
              <p><span className="font-medium">Service:</span> {bookingData.serviceType}</p>
              <p><span className="font-medium">Date & Time:</span> {bookingData.serviceDate} at {bookingData.preferredTime}</p>
              <p><span className="font-medium">Dealer:</span> {bookingData.dealerName}</p>
              <p><span className="font-medium">Customer:</span> {bookingData.customerName}</p>
              <p><span className="font-medium">Contact:</span> {bookingData.customerPhone}</p>
            </div>
          </div>
          
          <button
            onClick={() => {
              setSubmitted(false);
              setCurrentStep(1);
              setBookingData({
                vehicleModel: '', registrationNumber: '', serviceType: '', serviceDate: '',
                preferredTime: '', dealerCode: '', dealerName: '', dealerAddress: '',
                customerName: '', customerPhone: '', customerEmail: '', additionalNotes: ''
              });
            }}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Another Booking
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <React.Fragment key={step.number}>
              <div className="flex flex-col items-center flex-1">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  currentStep >= step.number ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  <step.icon className="w-6 h-6" />
                </div>
                <span className={`mt-2 text-sm font-medium ${
                  currentStep >= step.number ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {step.title}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-1 ${
                  currentStep > step.number ? 'bg-blue-600' : 'bg-gray-200'
                }`} style={{ marginTop: '-20px' }} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-white rounded-lg shadow-lg p-8">
        {/* Step 1: Vehicle */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Vehicle Information</h2>
              <p className="text-gray-600">Enter your vehicle details</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vehicle Model *
              </label>
              <select
                value={bookingData.vehicleModel}
                onChange={(e) => updateData('vehicleModel', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Model</option>
                <option value="Swift">Swift</option>
                <option value="Baleno">Baleno</option>
                <option value="Brezza">Brezza</option>
                <option value="Ertiga">Ertiga</option>
                <option value="Dzire">Dzire</option>
                <option value="Alto">Alto</option>
                <option value="WagonR">WagonR</option>
                <option value="Ciaz">Ciaz</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Registration Number *
              </label>
              <input
                type="text"
                value={bookingData.registrationNumber}
                onChange={(e) => updateData('registrationNumber', e.target.value.toUpperCase())}
                placeholder="e.g., DL01AB1234"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>
        )}

        {/* Step 2: Service */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Service Details</h2>
              <p className="text-gray-600">Choose service type and schedule</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Service Type *
              </label>
              <select
                value={bookingData.serviceType}
                onChange={(e) => updateData('serviceType', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Service</option>
                <option value="Regular Service">Regular Service</option>
                <option value="Paid Service">Paid Service</option>
                <option value="AC Service">AC Service</option>
                <option value="Oil Change">Oil Change</option>
                <option value="Wheel Alignment">Wheel Alignment</option>
                <option value="General Repair">General Repair</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preferred Date *
                </label>
                <input
                  type="date"
                  value={bookingData.serviceDate}
                  onChange={(e) => updateData('serviceDate', e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preferred Time *
                </label>
                <select
                  value={bookingData.preferredTime}
                  onChange={(e) => updateData('preferredTime', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="">Select Time</option>
                  <option value="09:00 AM">09:00 AM</option>
                  <option value="10:00 AM">10:00 AM</option>
                  <option value="11:00 AM">11:00 AM</option>
                  <option value="12:00 PM">12:00 PM</option>
                  <option value="02:00 PM">02:00 PM</option>
                  <option value="03:00 PM">03:00 PM</option>
                  <option value="04:00 PM">04:00 PM</option>
                  <option value="05:00 PM">05:00 PM</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Dealer */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Select Dealer</h2>
              <p className="text-gray-600">Choose your preferred service center</p>
            </div>

            <div className="space-y-3">
              {[
                { code: 'DLR001', name: 'Maruti Suzuki Arena (Connaught Place)', address: 'CP, New Delhi - 110001', distance: '2.5 km' },
                { code: 'DLR002', name: 'Nexa Showroom (Rohini)', address: 'Sector 8, Rohini, Delhi - 110085', distance: '5.8 km' },
                { code: 'DLR003', name: 'Maruti Service Center (Dwarka)', address: 'Sector 10, Dwarka, Delhi - 110075', distance: '8.2 km' }
              ].map((dealer) => (
                <label
                  key={dealer.code}
                  className={`block p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    bookingData.dealerCode === dealer.code
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="dealer"
                    value={dealer.code}
                    checked={bookingData.dealerCode === dealer.code}
                    onChange={() => {
                      updateData('dealerCode', dealer.code);
                      updateData('dealerName', dealer.name);
                      updateData('dealerAddress', dealer.address);
                    }}
                    className="sr-only"
                  />
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{dealer.name}</div>
                      <div className="text-sm text-gray-600 mt-1">{dealer.address}</div>
                    </div>
                    <div className="text-sm text-blue-600 font-medium ml-4">{dealer.distance}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Customer */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Customer Information</h2>
              <p className="text-gray-600">Your contact details for confirmation</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name *
              </label>
              <input
                type="text"
                value={bookingData.customerName}
                onChange={(e) => updateData('customerName', e.target.value)}
                placeholder="Enter your full name"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Phone Number *
              </label>
              <input
                type="tel"
                value={bookingData.customerPhone}
                onChange={(e) => updateData('customerPhone', e.target.value)}
                placeholder="Enter 10-digit mobile number"
                pattern="[0-9]{10}"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <input
                type="email"
                value={bookingData.customerEmail}
                onChange={(e) => updateData('customerEmail', e.target.value)}
                placeholder="your.email@example.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes (Optional)
              </label>
              <textarea
                value={bookingData.additionalNotes}
                onChange={(e) => updateData('additionalNotes', e.target.value)}
                placeholder="Any specific requirements or issues?"
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Previous
          </button>

          {currentStep < 4 ? (
            <button
              onClick={nextStep}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              Next
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Confirm Booking
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
