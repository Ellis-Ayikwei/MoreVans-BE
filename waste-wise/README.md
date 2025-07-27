# 🗑️ Waste Wise - Smart Waste Management System

A comprehensive IoT-based smart waste management system designed for urban environments, specifically tailored for Accra, Ghana. This system monitors waste bin fill levels in real-time, optimizes collection routes, and provides analytics for efficient waste management.

## 🌟 Features

### Core Functionality
- **Real-time Monitoring**: Track waste bin fill levels using IoT sensors
- **Smart Route Optimization**: AI-powered route planning for collection vehicles
- **Alert System**: Automated alerts for full bins, maintenance needs, and system issues
- **Analytics Dashboard**: Comprehensive analytics and reporting tools
- **Mobile App**: Citizen engagement through mobile application
- **Multi-role Support**: Admin, operator, driver, and citizen interfaces

### Technical Features
- **Real-time Updates**: WebSocket-based live data streaming
- **Offline Capability**: Progressive Web App with offline support
- **Predictive Analytics**: ML-based fill level predictions
- **Geographic Visualization**: Interactive maps with PostGIS integration
- **Multi-language Support**: Internationalization ready
- **Responsive Design**: Mobile-first approach

## 🏗️ System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   IoT Sensors   │────▶│   MQTT Broker   │────▶│  Django Backend │
│    (ESP32)      │     │   (Mosquitto)   │     │   (REST API)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                ┌─────────────────────────┴───────────────────────┐
                                │                                                 │
                        ┌───────▼────────┐                              ┌─────────▼────────┐
                        │  PostgreSQL    │                              │     Redis        │
                        │  with PostGIS  │                              │  (Cache/Queue)   │
                        └────────────────┘                              └──────────────────┘
                                                          │
                        ┌─────────────────────────────────┴─────────────────────────────┐
                        │                                                               │
                ┌───────▼────────┐              ┌──────────────┐              ┌─────────▼────────┐
                │ React Frontend │              │ React Native │              │     Celery       │
                │  (Dashboard)   │              │ (Mobile App) │              │ (Task Queue)     │
                └────────────────┘              └──────────────┘              └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL with PostGIS extension
- Redis

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/waste-wise.git
cd waste-wise
```

2. **Set up environment variables**
```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env

# Edit the .env files with your configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec backend python manage.py migrate
```

5. **Create a superuser**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Load sample data (optional)**
```bash
docker-compose exec backend python manage.py loaddata sample_data.json
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/swagger

## 💻 Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### IoT Firmware Development

1. Install Arduino IDE or PlatformIO
2. Install required libraries:
   - PubSubClient
   - ArduinoJson
   - DHT sensor library
   - ArduinoOTA

3. Configure WiFi and MQTT settings in the firmware
4. Upload to ESP32

## 📱 Mobile App

The React Native mobile app is located in the `mobile` directory.

```bash
cd mobile
npm install
npm run android  # For Android
npm run ios      # For iOS (macOS only)
```

## 🔧 Configuration

### Backend Configuration

Key settings in `backend/config/settings.py`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MQTT_BROKER_HOST`: MQTT broker address
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Allowed host domains

### Frontend Configuration

Key settings in `frontend/.env`:
- `VITE_API_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL
- `VITE_MAPBOX_ACCESS_TOKEN`: Mapbox API token

### IoT Configuration

Update in firmware:
- WiFi SSID and password
- MQTT broker address
- Sensor calibration values

## 📊 API Documentation

### Authentication
```http
POST /api/auth/token/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Bins Endpoints
- `GET /api/v1/bins/` - List all bins
- `GET /api/v1/bins/:id/` - Get bin details
- `POST /api/v1/bins/` - Create new bin
- `PUT /api/v1/bins/:id/` - Update bin
- `DELETE /api/v1/bins/:id/` - Delete bin

### Real-time WebSocket Events
- `sensor_update` - Sensor data updates
- `alert_notification` - New alerts
- `route_update` - Route status changes
- `bin_status_change` - Bin status updates

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=apps  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### E2E Tests
```bash
cd frontend
npm run test:e2e
```

## 📈 Performance Optimization

- **Database**: Indexes on frequently queried fields
- **Caching**: Redis caching for API responses
- **Frontend**: Code splitting and lazy loading
- **Images**: Automatic optimization and WebP conversion
- **API**: Pagination and query optimization

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Rate limiting on API endpoints
- Input validation and sanitization
- HTTPS enforcement in production
- Security headers (CORS, CSP, etc.)

## 🚢 Deployment

### Production Deployment

1. **Update environment variables for production**
2. **Build and push Docker images**
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml push
```

3. **Deploy to your cloud provider**
   - AWS ECS/EKS
   - Google Cloud Run/GKE
   - Azure Container Instances/AKS
   - DigitalOcean App Platform

### CI/CD Pipeline

GitHub Actions workflow included for:
- Automated testing
- Docker image building
- Deployment to staging/production

## 📊 Monitoring

- **Application Monitoring**: Sentry integration
- **Performance Monitoring**: Prometheus metrics
- **Logs**: Centralized logging with ELK stack
- **Uptime Monitoring**: Health check endpoints

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Project Lead**: [Your Name]
- **Backend Developer**: [Name]
- **Frontend Developer**: [Name]
- **IoT Engineer**: [Name]
- **UI/UX Designer**: [Name]

## 🙏 Acknowledgments

- Accra Metropolitan Assembly for project support
- University of Ghana for research collaboration
- Open source community for amazing tools and libraries

## 📞 Contact

- **Email**: contact@wastewise.com
- **Website**: https://wastewise.com
- **Twitter**: @wastewise
- **LinkedIn**: [Waste Wise](https://linkedin.com/company/wastewise)

---

**Made with ❤️ for a cleaner, smarter Accra**