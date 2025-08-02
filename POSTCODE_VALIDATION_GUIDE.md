# Postcode Validation APIs Guide

## Overview

Your MoreVans backend now uses a **simplified Google Maps API** for postcode validation and address lookup. This provides clean, structured address data with proper address components.

## Available APIs

### 1. **Comprehensive Postcode Validation** (Recommended)
**Endpoint:** `/api/locations/validate-postcode-comprehensive/<postcode>/`

**Features:**
- ✅ Uses Google Maps API for reliable results
- ✅ Returns structured address components
- ✅ Includes coordinates and detailed info
- ✅ Clean, consistent data format

**Example Response:**
```json
{
    "is_valid": true,
    "source": "google_maps",
    "postcode": "SW1A 1AA",
    "message": "Postcode is valid. Found 3 addresses.",
    "addresses": [
        {
            "formatted_address": "Buckingham Palace, London SW1A 1AA, UK",
            "address_line_1": "Buckingham Palace",
            "address_line_2": "",
            "city_town": "London",
            "county": "England",
            "postcode": "SW1A 1AA",
            "country": "United Kingdom",
            "coordinates": {
                "lat": 51.501009,
                "lng": -0.124625
            },
            "source": "google_maps"
        }
    ],
    "total_addresses": 3
}
```

### 2. **Comprehensive Address Lookup**
**Endpoint:** `/api/locations/postcode-addresses-comprehensive/<postcode>/`

**Features:**
- ✅ Gets all available addresses for a postcode
- ✅ Structured address components
- ✅ Coordinates and detailed info
- ✅ Clean data format

**Example Response:**
```json
{
    "is_valid": true,
    "postcode": "SW1A 1AA",
    "addresses": [
        {
            "formatted_address": "Buckingham Palace, London SW1A 1AA, UK",
            "address_line_1": "Buckingham Palace",
            "address_line_2": "",
            "city_town": "London",
            "county": "England",
            "postcode": "SW1A 1AA",
            "country": "United Kingdom",
            "coordinates": {
                "lat": 51.501009,
                "lng": -0.124625
            },
            "source": "google_maps"
        }
    ],
    "total_found": 3,
    "source": "google_maps"
}
```

## Address Structure

Each address in the response includes these structured components:

| Field | Description | Example |
|-------|-------------|---------|
| `formatted_address` | Full formatted address | "Buckingham Palace, London SW1A 1AA, UK" |
| `address_line_1` | Street number and name | "Buckingham Palace" |
| `address_line_2` | Additional address info | "Flat 2, Building name" |
| `city_town` | City or town name | "London" |
| `county` | County or region | "England" |
| `postcode` | Postal code | "SW1A 1AA" |
| `country` | Country name | "United Kingdom" |
| `coordinates` | Latitude and longitude | `{"lat": 51.501009, "lng": -0.124625}` |
| `source` | Data source | "google_maps" |

## Setup Instructions

### 1. Configure Google Maps API Key
Add to your `.env` file:

```bash
GOOGLE_MAPS_API_KEY=your-google-maps-api-key-here
```

### 2. Enable Required Google APIs
In Google Cloud Console, enable these APIs:
- Google Maps JavaScript API
- Places API
- Geocoding API

### 3. Test the API
```bash
# Test postcode validation
curl "http://localhost:8000/api/locations/validate-postcode-comprehensive/SW1A1AA"

# Test address lookup
curl "http://localhost:8000/api/locations/postcode-addresses-comprehensive/SW1A1AA"
```

## Testing Examples

### Test Valid Postcode:
```bash
curl "http://localhost:8000/api/locations/validate-postcode-comprehensive/SW1A1AA"
```

### Test Invalid Postcode:
```bash
curl "http://localhost:8000/api/locations/validate-postcode-comprehensive/INVALID"
```

### Test Address Lookup:
```bash
curl "http://localhost:8000/api/locations/postcode-addresses-comprehensive/SW1A1AA"
```

## Frontend Integration

### React/JavaScript Example:
```javascript
// Validate postcode and get structured addresses
const validatePostcode = async (postcode) => {
    try {
        const response = await fetch(`/api/locations/validate-postcode-comprehensive/${postcode}`);
        const data = await response.json();
        
        if (data.is_valid) {
            console.log('Postcode is valid:', data.addresses);
            
            // Access structured address components
            data.addresses.forEach(address => {
                console.log('Address Line 1:', address.address_line_1);
                console.log('Address Line 2:', address.address_line_2);
                console.log('City/Town:', address.city_town);
                console.log('County:', address.county);
                console.log('Postcode:', address.postcode);
                console.log('Country:', address.country);
                console.log('Coordinates:', address.coordinates);
            });
            
            return data.addresses;
        } else {
            console.log('Invalid postcode:', data.message);
            return [];
        }
    } catch (error) {
        console.error('Validation error:', error);
        return [];
    }
};

// Get addresses for postcode
const getAddresses = async (postcode) => {
    try {
        const response = await fetch(`/api/locations/postcode-addresses-comprehensive/${postcode}`);
        const data = await response.json();
        
        if (data.is_valid && data.addresses.length > 0) {
            console.log('Found addresses:', data.addresses);
            return data.addresses;
        } else {
            console.log('No addresses found');
            return [];
        }
    } catch (error) {
        console.error('Address lookup error:', error);
        return [];
    }
};
```

## Error Handling

All APIs return consistent error responses:

```json
{
    "is_valid": false,
    "message": "Error description",
    "source": "google_maps",
    "addresses": []
}
```

## Rate Limits

- **Google Maps APIs**: Depends on your billing plan
- **Free tier**: $200 credit per month (usually covers thousands of requests)
- **Production**: Consider upgrading for higher usage

## Troubleshooting

### Common Issues:

1. **"Google Maps API key not configured"**
   - Solution: Add `GOOGLE_MAPS_API_KEY` to your `.env` file

2. **"REQUEST_DENIED"**
   - Solution: Check Google Maps API setup in `GOOGLE_MAPS_API_SETUP.md`

3. **"No addresses found"**
   - Solution: Try a different postcode or check API key permissions

4. **"Quota exceeded"**
   - Solution: Check usage in Google Cloud Console or upgrade billing plan

## Best Practices

1. **Use structured address components** - Access individual fields for better UX
2. **Handle missing data gracefully** - Some fields may be empty
3. **Cache results** - Reduce API calls for repeated postcodes
4. **Implement fallback** - Always have manual entry option
5. **Monitor usage** - Track API usage in Google Cloud Console

## Support

For Google Maps API issues:
- **Google Maps Documentation**: https://developers.google.com/maps
- **Google Cloud Console**: https://console.cloud.google.com/
- **Billing Support**: https://cloud.google.com/billing/docs 