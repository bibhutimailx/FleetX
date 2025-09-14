# Fleet Management System

A comprehensive real-time fleet management web application that connects to the WHILSEYE GPS tracking platform to display live vehicle navigation, geofence monitoring, and send push notifications to stakeholders.

## 🚀 Features

- **Real-time Vehicle Tracking**: Live GPS tracking with 30-second updates
- **Interactive Map**: Leaflet-based map with OpenStreetMap tiles
- **Geofence Monitoring**: Plant gate geofence with entry/exit detection
- **Push Notifications**: Firebase Cloud Messaging and Slack webhooks
- **Activity Logging**: Comprehensive activity tracking and history
- **Dashboard Analytics**: Fleet overview with statistics and metrics
- **WebSocket Support**: Real-time updates without page refresh
- **Responsive Design**: Modern UI built with React and Tailwind CSS

## 🏗️ Architecture

### Backend (FastAPI)
- **API Service**: RESTful API with FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Background Tasks**: Async vehicle polling and event processing
- **WebSocket**: Real-time data streaming
- **Notifications**: FCM and Slack integration
- **Geofencing**: Automated zone entry/exit detection

### Frontend (React)
- **Map Component**: Interactive vehicle tracking with Leaflet
- **Dashboard**: Real-time analytics and fleet overview
- **Activity Log**: Event history and filtering
- **WebSocket Client**: Live data updates
- **Responsive Design**: Tailwind CSS for modern UI

### Infrastructure
- **Docker**: Containerized deployment
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **Nginx**: Reverse proxy and static file serving

## 📁 Project Structure

```
Fleet-management/
├── backend/                    # FastAPI backend application
│   └── app/
│       ├── api/               # API route handlers
│       ├── core/              # Core configuration and database
│       ├── models/            # SQLAlchemy database models
│       ├── services/          # Business logic services
│       └── utils/             # Utility functions
├── frontend/                  # React frontend application
│   ├── public/               # Static files
│   └── src/
│       ├── components/       # React components
│       ├── services/         # API and WebSocket services
│       ├── types/           # TypeScript type definitions
│       └── utils/           # Utility functions
├── docker/                   # Docker configuration files
├── docker-compose.yml        # Production deployment
├── docker-compose.dev.yml    # Development environment
├── requirements.txt          # Python dependencies
└── env.example              # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Fleet-management
```

### 2. Environment Configuration

Copy the environment template and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# WHILSEYE API Configuration
WHILSEYE_API_URL=https://api.whilseye.com/v1
WHILSEYE_USERNAME=your_username
WHILSEYE_PASSWORD=your_password
WHILSEYE_API_KEY=your_api_key

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=fleet_management

# Geofence Configuration (Plant Gate)
GEOFENCE_LAT=40.7128
GEOFENCE_LNG=-74.0060
GEOFENCE_RADIUS=100

# Firebase Cloud Messaging
FCM_SERVICE_ACCOUNT_KEY=./path/to/serviceAccountKey.json
FCM_PROJECT_ID=your_firebase_project_id

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Application Settings
POLLING_INTERVAL=30
JWT_SECRET_KEY=your_super_secure_jwt_key
```

### 3. Docker Deployment (Recommended)

#### Production Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Development Deployment

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View backend logs
docker-compose logs -f backend

# View frontend logs  
docker-compose logs -f frontend
```

### 4. Local Development

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Run database migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📊 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/v1/vehicles/` - Get all vehicles
- `GET /api/v1/vehicles/locations` - Get vehicle locations
- `GET /api/v1/vehicles/{vehicle_id}/location` - Get specific vehicle location
- `GET /api/v1/events/geofence` - Get geofence events
- `GET /api/v1/events/activity` - Get activity log
- `GET /api/v1/events/summary` - Get events summary
- `WS /ws/vehicle-updates` - WebSocket for real-time updates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WHILSEYE_API_URL` | WHILSEYE API base URL | `https://api.whilseye.com/v1` |
| `WHILSEYE_USERNAME` | WHILSEYE username | - |
| `WHILSEYE_PASSWORD` | WHILSEYE password | - |
| `WHILSEYE_API_KEY` | WHILSEYE API key | - |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `GEOFENCE_LAT` | Geofence center latitude | `40.7128` |
| `GEOFENCE_LNG` | Geofence center longitude | `-74.0060` |
| `GEOFENCE_RADIUS` | Geofence radius in meters | `100` |
| `POLLING_INTERVAL` | Vehicle polling interval (seconds) | `30` |
| `FCM_SERVICE_ACCOUNT_KEY` | Firebase service account key path | - |
| `FCM_PROJECT_ID` | Firebase project ID | - |
| `SLACK_WEBHOOK_URL` | Slack webhook URL | - |
| `DEBUG` | Enable debug mode | `false` |

### Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Cloud Messaging
3. Generate a service account key
4. Download the JSON key file
5. Set `FCM_SERVICE_ACCOUNT_KEY` to the file path
6. Set `FCM_PROJECT_ID` to your project ID

### Slack Integration

1. Create a Slack app at https://api.slack.com/apps
2. Enable incoming webhooks
3. Create a webhook URL for your channel
4. Set `SLACK_WEBHOOK_URL` to the webhook URL

## 🚧 Development

### Code Structure

#### Backend Services

- **WhilseyeService**: WHILSEYE API integration
- **GeofenceService**: Geofence calculations and events
- **NotificationService**: FCM and Slack notifications
- **TrackingService**: Vehicle polling and processing

#### Frontend Components

- **Map**: Interactive vehicle map with Leaflet
- **VehicleList**: Vehicle listing and selection
- **ActivityLog**: Event history and filtering
- **Dashboard**: Analytics and metrics

### Adding New Features

1. **Backend**: Add new services in `backend/app/services/`
2. **API**: Create new routes in `backend/app/api/`
3. **Frontend**: Add components in `frontend/src/components/`
4. **Database**: Create models in `backend/app/models/`

### Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

## 🔒 Security

### Best Practices

- Use strong passwords for database and JWT secrets
- Store sensitive data in environment variables
- Use HTTPS in production
- Regularly update dependencies
- Implement proper authentication for production use
- Secure Firebase and Slack webhook URLs

### Production Security

- Set up SSL/TLS certificates
- Configure firewall rules
- Use Docker secrets for sensitive data
- Implement rate limiting
- Set up monitoring and alerting

## 📈 Monitoring

### Health Checks

- Backend: `GET /health`
- Frontend: Built-in Docker health checks
- Database: PostgreSQL connection monitoring

### Logging

- Application logs: `./logs/` directory
- Docker logs: `docker-compose logs [service]`
- Database logs: PostgreSQL container logs

### Metrics

- Vehicle tracking status
- API response times
- WebSocket connection counts
- Geofence event rates
- Notification delivery status

## 🚀 Deployment

### Cloud Deployment

#### AWS/GCP/Azure

1. Set up a VM instance
2. Install Docker and Docker Compose
3. Clone the repository
4. Configure environment variables
5. Run `docker-compose up -d`

#### Kubernetes

```bash
# Generate Kubernetes manifests
docker-compose config > k8s-manifests.yaml

# Apply to cluster
kubectl apply -f k8s-manifests.yaml
```

### Scaling Considerations

- Use load balancers for multiple backend instances
- Configure Redis for session sharing
- Use PostgreSQL read replicas for read-heavy workloads
- Implement CDN for frontend assets

## 🛠️ Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Database connection issues
# - Missing environment variables
# - Port conflicts
```

#### Frontend Build Failures
```bash
# Check Node.js version
node --version

# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify connection string
docker-compose exec backend python -c "from app.core.database import engine; print(engine.url)"
```

#### WebSocket Connection Problems
```bash
# Check WebSocket endpoint
# Ensure proxy configuration is correct
# Verify CORS settings
```

### Performance Optimization

- Adjust `POLLING_INTERVAL` based on requirements
- Configure database connection pooling
- Implement caching for frequently accessed data
- Optimize map rendering for large vehicle counts

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Check Docker logs for error details

## 🔄 Updates

### Version 1.0.0
- Initial release with core features
- Real-time vehicle tracking
- Geofence monitoring
- Push notifications
- Web dashboard

### Roadmap
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Route optimization
- [ ] Driver behavior monitoring
- [ ] Maintenance scheduling
- [ ] API rate limiting
- [ ] User authentication/authorization

# FleetX
