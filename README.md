# MoreVans - Logistics and Transportation Platform

## Overview

MoreVans is a comprehensive logistics and transportation platform built with Django REST Framework (backend) and what appears to be a React/Vite frontend. The platform connects customers with transportation providers, drivers, and vehicles for various logistics needs.

## Tech Stack

### Backend
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Real-time**: Django Channels
- **Payment Processing**: Stripe
- **Task Queue**: Django FSM (Finite State Machine)
- **Other**: CORS headers, Pillow for image handling

### Frontend
- **Build Tool**: Vite
- **Framework**: Appears to be React/TypeScript based on file structure

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 13

## Core Features

### 1. Authentication & User Management
- JWT-based authentication with access and refresh tokens
- OTP (One-Time Password) system for:
  - User registration verification
  - Login authentication
  - Password reset
  - Email/phone change verification
- Multiple user types: Customers, Drivers, Providers
- Email verification system with HTML templates

### 2. Core Business Modules

#### User Types
- **Customers**: End users requesting transportation services
- **Drivers**: Individual drivers providing transportation
- **Providers**: Companies or organizations managing fleets

#### Main Features
- **Vehicle Management**: Track and manage different types of vehicles
- **Request System**: Customers can create transportation requests
- **Bidding System**: Providers/drivers can bid on requests
- **Job Management**: Track ongoing transportation jobs
- **Journey Tracking**: Real-time tracking with journey stops
- **Messaging**: In-app messaging between users
- **Notifications**: Push notifications for important events
- **Reviews & Ratings**: Customer feedback system
- **Payment Processing**: Integrated with Stripe
- **Insurance Management**: Track vehicle and driver insurance
- **Customer Support**: Built-in support ticket system

### 3. Advanced Features
- **Pricing Engine**: Dynamic pricing calculations
- **Contract Management**: Handle long-term contracts
- **Location Services**: Integration with Google Maps API
- **Weather Integration**: OpenWeatherMap API integration
- **Document Management**: Driver document uploads and verification
- **System Settings**: Configurable platform settings

## Project Structure

```
/
├── backend/              # Django project configuration
│   ├── settings.py      # Main Django settings
│   ├── urls.py          # URL routing
│   └── migrations/      # Database migrations
├── apps/                # Django applications
│   ├── Authentication/  # User auth and OTP system
│   ├── User/           # User profiles
│   ├── Customer/       # Customer-specific features
│   ├── Driver/         # Driver management
│   ├── Provider/       # Provider/company management
│   ├── Vehicle/        # Vehicle management
│   ├── Request/        # Transportation requests
│   ├── RequestItems/   # Items within requests
│   ├── Bidding/        # Bidding system
│   ├── Job/            # Active jobs
│   ├── JourneyStop/    # Journey waypoints
│   ├── Tracking/       # Real-time tracking
│   ├── Payment/        # Payment processing
│   ├── Pricing/        # Pricing calculations
│   ├── Contract/       # Contract management
│   ├── Insurance/      # Insurance tracking
│   ├── Review/         # Reviews and ratings
│   ├── Message/        # In-app messaging
│   ├── Notification/   # Push notifications
│   ├── Location/       # Location services
│   ├── Services/       # Business services
│   ├── SystemSettings/ # Platform configuration
│   └── Customer_Support/ # Support tickets
├── src/                # Frontend source
│   ├── components/     # React components
│   └── services/       # API services
├── templates/          # Email templates
├── uploads/           # User uploads
└── driver_documents/  # Driver document storage
```

## API Documentation

The platform includes comprehensive API documentation, particularly for the OTP system (see `OTP_API_DOCUMENTATION.md`). Key endpoints include:

- **Authentication**: `/api/auth/` - Login, logout, token refresh
- **Registration**: `/api/auth/register/` - New user registration
- **OTP**: `/api/auth/otp/` - OTP sending and verification
- **Password Management**: Password reset and change functionality

## Development Setup

### Using Docker Compose (Recommended)

1. Clone the repository
2. Create a `.env` file with required environment variables
3. Run: `docker-compose up`

The application will be available at:
- Backend API: `http://localhost:8000`

### Manual Setup

1. Install PostgreSQL
2. Create a virtual environment
3. Install dependencies: `pip install -r require.txt`
4. Set up environment variables
5. Run migrations: `python manage.py migrate`
6. Start server: `python manage.py runserver`

## Environment Variables

Required environment variables:
- `DJANGO_SECRETE_KEY`: Django secret key
- `OPENWEATHERMAP_API_KEY`: Weather API key
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- Database configuration (see docker-compose.yml)

## Testing

The project includes various test files for:
- Email functionality
- SMTP configuration
- OTP system
- Custom email backends

## Security Features

- JWT authentication with refresh tokens
- OTP-based verification
- Rate limiting on OTP requests
- CORS configuration
- Email masking for privacy
- Secure password reset flow

## Current State

This appears to be an MVP-level logistics platform with core functionality implemented. The backend is well-structured with clear separation of concerns across different Django apps. The authentication system is robust with OTP verification, and the platform supports the basic flow of customers requesting transportation, providers/drivers bidding, and job execution with tracking.

## Next Steps for Production

1. Complete frontend implementation
2. Add comprehensive test coverage
3. Implement proper error handling and logging
4. Set up CI/CD pipeline
5. Configure production-ready security settings
6. Add API rate limiting
7. Implement caching strategy
8. Set up monitoring and analytics
9. Complete API documentation for all endpoints
10. Add data validation and sanitization