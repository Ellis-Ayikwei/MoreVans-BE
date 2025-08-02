# Provider Registration Implementation

## Overview

This document outlines the complete implementation of the provider registration system for MoreVans, which handles user creation, provider profile creation, and address management in a single API endpoint.

## Key Components

### 1. Enhanced ServiceProviderAddress Model

**File:** `apps/Provider/models.py`

The `ServiceProviderAddress` model has been enhanced to support multiple address types:

- **Address Types:**
  - `home` - Home address
  - `business` - Business address
  - `non_uk` - Non-UK address
  - `registered` - Registered business address
  - `operational` - Operational address
  - `billing` - Billing address
  - `correspondence` - Correspondence address

- **Key Features:**
  - Support for multiple addresses per provider
  - Address verification tracking
  - UK postcode validation
  - Primary address designation
  - Business name association for business addresses
  - Full address formatting
  - UK address detection

### 2. ProviderRegistrationSerializer

**File:** `apps/Provider/serializer.py`

A comprehensive serializer that handles the complete provider registration process:

- **User Creation:**
  - Email, password, first/last name
  - Username, phone numbers
  - User type set to "provider"

- **Provider Creation:**
  - Business details (name, type, VAT status)
  - Vehicle count parsing
  - Work types processing

- **Address Creation:**
  - Home address (always created)
  - Business address (if separate business address selected)
  - Non-UK address (if non-UK address selected)

- **Validation:**
  - Password confirmation
  - Email/username uniqueness
  - Required field validation
  - Conditional field validation

### 3. RegisterProviderAPIView

**File:** `apps/Authentication/views.py`

API endpoint for provider registration:

- **Endpoint:** `POST /api/auth/register/provider/`
- **Features:**
  - Rate limiting
  - Transaction-based creation
  - OTP email verification
  - Comprehensive error handling
  - Success/error responses

## API Usage

### Request Format

```json
{
  "first_name": "Ellis",
  "last_name": "Ayikwei",
  "email": "ellisyou59@gmail.com",
  "password": "@Toshib12345",
  "confirm_password": "@Toshib12345",
  "username": "ellisyou5",
  "mobile_number": "0248138722",
  "phone_number": "0248138722",
  "business_name": "Tradehut",
  "business_type": "limited",
  "vat_registered": "yes",
  "number_of_vehicles": "2-5",
  "work_types": ["Home removals", "Office removals", "Parcel delivery"],
  "address_line_1": "A123/4",
  "address_line_2": "asdfs",
  "city": "Accra",
  "postcode": "SW1 AAA",
  "country": "Ghana",
  "has_separate_business_address": true,
  "business_address_line_1": "Tradehut",
  "business_address_line_2": "Accra-Kumasi Road, Kumasi, Ghana",
  "business_city": "Kumasi",
  "business_postcode": "3242",
  "business_country": "Ghana",
  "has_non_uk_address": false,
  "accepted_privacy_policy": true
}
```

### Response Format

**Success (201 Created):**
```json
{
  "message": "Provider registration successful. Please check your email for verification.",
  "user_id": "uuid",
  "provider_id": "uuid",
  "email": "ellisyou59@gmail.com",
  "status": "pending_verification"
}
```

**Error (400 Bad Request):**
```json
{
  "message": "Registration failed. Please check the provided information.",
  "errors": {
    "email": ["Email address is already registered"],
    "password": ["Passwords do not match"]
  }
}
```

## Database Schema

### ServiceProviderAddress Table

```sql
CREATE TABLE service_provider_address (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address_type VARCHAR(20) NOT NULL DEFAULT 'home',
    address_line_1 VARCHAR(255) NOT NULL,
    address_line_2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    postcode VARCHAR(20) NOT NULL,
    state VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'United Kingdom',
    business_name VARCHAR(200),
    is_primary BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    verification_date TIMESTAMP,
    verification_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    provider_id UUID REFERENCES service_provider(id) ON DELETE CASCADE
);
```

## Features

### 1. Multiple Address Support

Providers can have multiple addresses:
- **Home Address:** Primary address for the provider
- **Business Address:** Separate business location
- **Non-UK Address:** International addresses

### 2. Address Verification

- Automatic verification for registration addresses
- Verification method tracking
- Verification date recording
- Support for different verification methods

### 3. Work Types Processing

The system automatically:
- Maps frontend work types to service names
- Creates missing services if they don't exist
- Links services to the provider

### 4. Vehicle Count Parsing

Converts string vehicle counts to integers:
- "1" → 1
- "2-5" → 3 (average)
- "6-10" → 8 (average)
- "11+" → 15 (representative)
- "No Vehicle" → 0

### 5. OTP Email Verification

- Automatic OTP generation and sending
- Email verification required for account activation
- Rate limiting and cooldown protection

## Testing

A comprehensive test script is provided (`test_provider_registration.py`) that:

1. **Validates Serializer:** Tests all validation rules
2. **Creates Data:** Tests user, provider, and address creation
3. **Verifies Database:** Confirms records are properly saved
4. **Tests Duplicates:** Ensures duplicate prevention works
5. **Tests Address Model:** Verifies address functionality

### Running Tests

```bash
python test_provider_registration.py
```

## Security Features

1. **Rate Limiting:** Prevents abuse with AnonRateThrottle
2. **Password Validation:** Django's built-in password validation
3. **Transaction Safety:** All operations wrapped in database transactions
4. **Input Validation:** Comprehensive field validation
5. **Duplicate Prevention:** Email and username uniqueness checks

## Error Handling

The system provides detailed error responses for:
- Validation errors
- Database errors
- Email sending failures
- Duplicate registrations
- Missing required fields

## Integration Points

### Frontend Integration

The API is designed to work seamlessly with the React frontend:
- Matches frontend data structure exactly
- Handles all address scenarios
- Supports all business types
- Processes work types correctly

### Email System Integration

- Uses existing OTP system
- Sends verification emails automatically
- Handles email failures gracefully
- Provides fallback responses

### Database Integration

- Uses existing User and ServiceProvider models
- Extends with new ServiceProviderAddress model
- Maintains referential integrity
- Supports cascading deletes

## Future Enhancements

1. **Address Geocoding:** Automatic coordinate generation
2. **Address Verification:** Third-party address verification
3. **Document Upload:** Integration with document verification
4. **Background Checks:** Automated background verification
5. **Payment Integration:** Stripe account creation

## Maintenance

### Database Migrations

When deploying, ensure to run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Monitoring

Monitor the following for system health:
- Registration success rates
- Email delivery rates
- Database performance
- Error rates and types

## Support

For issues or questions:
1. Check the test script output
2. Review Django logs
3. Verify database connectivity
4. Check email configuration
5. Review rate limiting settings 