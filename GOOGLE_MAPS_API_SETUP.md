# Google Maps API Setup Guide

## Issue: REQUEST_DENIED Error

The `REQUEST_DENIED` error occurs when:
1. **API Key is missing** - No Google Maps API key is configured
2. **API Key is invalid** - The key doesn't exist or is malformed
3. **API Key lacks permissions** - The key doesn't have the required APIs enabled
4. **Billing not enabled** - Google Cloud billing is not set up
5. **API quotas exceeded** - You've hit the usage limits

## Step-by-Step Solution

### 1. Create Environment File

Create a `.env` file in your project root (same level as `manage.py`):

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here

# API Keys
GOOGLE_MAPS_API_KEY=your-actual-google-maps-api-key-here
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key-here

# Database Settings
DB_NAME=morevans
DB_USER=postgres
DB_PASSWORD=@Toshib123
DB_HOST=localhost
DB_PORT=5432

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Other Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Get Google Maps API Key

#### Option A: Create New Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** or select existing one
3. **Enable billing** (required for Google Maps APIs)
4. **Enable required APIs**:
   - Google Maps JavaScript API
   - Places API
   - Geocoding API
   - Directions API
5. **Create API Key**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the generated key

#### Option B: Use Existing Project

If you already have a Google Cloud project:
1. Go to https://console.cloud.google.com/
2. Select your project
3. Go to "APIs & Services" > "Credentials"
4. Create a new API key or use existing one

### 3. Configure API Key Restrictions (Recommended)

For security, restrict your API key:

1. **Application restrictions**:
   - HTTP referrers (web sites): Add your domain
   - IP addresses: Add your server IP
   - Android apps: Add your app package name
   - iOS apps: Add your app bundle ID

2. **API restrictions**:
   - Select "Restrict key"
   - Choose only the APIs you need:
     - Google Maps JavaScript API
     - Places API
     - Geocoding API

### 4. Test Your API Key

Create a simple test script to verify your API key works:

```python
# test_google_maps_api.py
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

if not api_key:
    print("❌ GOOGLE_MAPS_API_KEY not found in environment variables")
    exit(1)

print(f"🔑 API Key found: {api_key[:10]}...")

# Test with a simple geocoding request
test_address = "London, UK"
url = f"https://maps.googleapis.com/maps/api/geocode/json?address={test_address}&key={api_key}"

try:
    response = requests.get(url)
    data = response.json()
    
    if data.get('status') == 'OK':
        print("✅ Google Maps API is working correctly!")
        print(f"📍 Found location: {data['results'][0]['formatted_address']}")
    else:
        print(f"❌ API Error: {data.get('status')}")
        print(f"Error message: {data.get('error_message', 'No error message')}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
```

### 5. Common Issues and Solutions

#### Issue: "API key not valid"
- **Solution**: Check that the API key is correctly copied to your `.env` file
- **Solution**: Ensure the key exists in Google Cloud Console

#### Issue: "This API project is not authorized"
- **Solution**: Enable the required APIs in Google Cloud Console
- **Solution**: Ensure billing is enabled for your project

#### Issue: "Quota exceeded"
- **Solution**: Check your usage in Google Cloud Console
- **Solution**: Consider upgrading your billing plan
- **Solution**: Implement caching to reduce API calls

#### Issue: "Request denied"
- **Solution**: Check API key restrictions
- **Solution**: Ensure your domain/IP is in the allowed list
- **Solution**: Verify the API is enabled

### 6. Alternative Solutions

#### Option A: Use Free Tier
Google Maps APIs have a generous free tier:
- $200 credit per month
- Usually covers thousands of requests
- Perfect for development and small applications

#### Option B: Use Alternative Services
If Google Maps is too expensive:

1. **OpenStreetMap + Nominatim** (Free):
   ```python
   # Example using OpenStreetMap
   import requests
   
   def geocode_address(address):
       url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
       response = requests.get(url)
       return response.json()
   ```

2. **Here Maps** (Free tier available)
3. **Mapbox** (Free tier available)

### 7. Environment Variables in Production

For production deployment:

1. **Set environment variables** on your server:
   ```bash
   export GOOGLE_MAPS_API_KEY="your-production-api-key"
   ```

2. **Or use your hosting platform's environment variable settings**:
   - Heroku: `heroku config:set GOOGLE_MAPS_API_KEY=your-key`
   - DigitalOcean: Use App Platform environment variables
   - AWS: Use Parameter Store or Secrets Manager

### 8. Testing the Fix

After setting up your API key:

1. **Restart your Django server**
2. **Test the address autocomplete endpoint**:
   ```
   GET /api/location/google-address-autocomplete/?input=london
   ```
3. **Check the response** - should return predictions instead of REQUEST_DENIED

### 9. Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables** for all sensitive data
3. **Restrict API keys** to specific domains/IPs
4. **Monitor usage** in Google Cloud Console
5. **Set up billing alerts** to avoid unexpected charges

### 10. Troubleshooting Checklist

- [ ] `.env` file exists in project root
- [ ] `GOOGLE_MAPS_API_KEY` is set in `.env`
- [ ] API key is valid and not expired
- [ ] Required APIs are enabled in Google Cloud Console
- [ ] Billing is enabled for the Google Cloud project
- [ ] API key restrictions allow your domain/IP
- [ ] Django server has been restarted after adding `.env`
- [ ] No typos in the API key

## Quick Fix Commands

```bash
# 1. Create .env file
echo "GOOGLE_MAPS_API_KEY=your-actual-api-key-here" > .env

# 2. Restart Django server
python manage.py runserver

# 3. Test the API
curl "http://localhost:8000/api/location/google-address-autocomplete/?input=london"
```

## Support

If you're still getting `REQUEST_DENIED` after following these steps:

1. Check the Google Cloud Console for specific error messages
2. Verify your API key in the Google Cloud Console
3. Test the API key directly with a simple curl request
4. Check your billing status in Google Cloud Console 