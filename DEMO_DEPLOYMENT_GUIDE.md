# FleetX Enhanced India Fleet Management - Demo Deployment Guide

## 🚀 Quick Local Demo (Recommended for Immediate Access)

### Option 1: One-Click Local Start ⭐ **RECOMMENDED**
```bash
# From FleetX root directory
./start_demo.sh
```
Then access: **http://localhost:3004**

### Option 2: Manual Local Start
```bash
# Terminal 1 - Start Backend
cd backend
source venv/bin/activate  # If using virtual environment
python3 enhanced_india_fleet_api.py

# Terminal 2 - Start Frontend (in new terminal)
cd frontend
python3 serve_enhanced_india.py
```
Then access: **http://localhost:3004**

---

## 🌐 Cloud Deployment Options (For Remote Demo Access)

### Option A: Railway.app (Free Tier) ⭐ **EASIEST CLOUD OPTION**

1. **Fork the repository to your GitHub**
2. **Go to [Railway.app](https://railway.app)**
3. **Sign up with GitHub and deploy:**
   ```
   - Connect GitHub repository
   - Add environment variables (if needed)
   - Deploy both backend and frontend
   ```
4. **Railway will provide public URLs like:**
   - Backend: `https://your-app-backend.railway.app`
   - Frontend: `https://your-app-frontend.railway.app`

### Option B: Render.com (Free Tier)

1. **Go to [Render.com](https://render.com)**
2. **Create Web Service from GitHub repo**
3. **Deploy Configuration:**
   ```yaml
   # Backend Service
   Build Command: pip install -r requirements.txt
   Start Command: python backend/enhanced_india_fleet_api.py
   
   # Frontend Service  
   Build Command: # None needed
   Start Command: python frontend/serve_enhanced_india.py
   ```

### Option C: Heroku (Free Tier Discontinued, Paid)

1. **Install Heroku CLI**
2. **Deploy Backend:**
   ```bash
   heroku create your-fleet-backend
   git subtree push --prefix backend heroku main
   ```
3. **Deploy Frontend:**
   ```bash
   heroku create your-fleet-frontend
   git subtree push --prefix frontend heroku main
   ```

### Option D: Vercel + Serverless (For Static Frontend)

1. **Go to [Vercel.com](https://vercel.com)**
2. **Deploy frontend directly**
3. **Backend can run on Railway/Render**

---

## 🐳 Docker Deployment (Production Ready)

### Option 1: Docker Compose (Local/Server)
```bash
# Build and start all services
docker-compose up -d

# Access at:
# Frontend: http://localhost/
# Backend: http://localhost:8000
```

### Option 2: Individual Docker Containers
```bash
# Build and run backend
docker build -f docker/Dockerfile.backend -t fleet-backend .
docker run -p 8006:8006 fleet-backend

# Build and run frontend  
docker build -f docker/Dockerfile.frontend -t fleet-frontend .
docker run -p 3004:3004 fleet-frontend
```

---

## 📱 Mobile/Remote Access Solutions

### Option 1: ngrok (Quick Remote Access)
```bash
# Install ngrok: https://ngrok.com/
# After starting local demo:
ngrok http 3004

# Share the ngrok URL: https://abc123.ngrok.io
```

### Option 2: localtunnel (Alternative to ngrok)
```bash
# Install: npm install -g localtunnel
# After starting local demo:
lt --port 3004

# Share the tunnel URL provided
```

### Option 3: Cloudflare Tunnel (Free)
```bash
# Install cloudflared
# After starting local demo:
cloudflared tunnel --url http://localhost:3004

# Share the Cloudflare URL provided
```

---

## ⚡ Fastest Demo Setup for Urgent Presentation

### For Immediate Local Demo:
```bash
# 1. Navigate to FleetX directory
cd /Users/bibhutisahoo/Downloads/GITHUB/FleetX

# 2. Start demo (auto-opens browser)
./start_demo.sh

# 3. Access immediately at: http://localhost:3004
```

### For Remote Demo (under 5 minutes):
```bash
# 1. Start local demo first
./start_demo.sh

# 2. In another terminal, create public tunnel
npx localtunnel --port 3004
# OR
brew install ngrok && ngrok http 3004

# 3. Share the public URL with your audience
```

---

## 🛠️ Environment Configuration

### Required Environment Variables (Optional)
```bash
# Create .env file (optional for demo)
cp env.example .env

# Edit .env with your API keys (not required for demo):
WHILSEYE_USERNAME=your_username
WHILSEYE_PASSWORD=your_password
SLACK_WEBHOOK_URL=your_slack_webhook
```

### System Requirements
- **Python 3.8+** (for backend)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
- **Internet Connection** (for map tiles and demo data)

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Kill processes on port 3004 or 8006
lsof -ti:3004 | xargs kill -9
lsof -ti:8006 | xargs kill -9
```

### Python Virtual Environment Issues
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
```

### Missing Dependencies
```bash
# Install Python dependencies
cd backend
pip install -r ../requirements.txt

# Or use system Python (if virtual env not working)
python3 -m pip install fastapi uvicorn pydantic
```

---

## 📊 Demo Features Available

### ✅ Immediate Access Features:
- **13 Indian Fleet Vehicles** (OD-03-NT-1001 to 1013)
- **Real-time Map Tracking** (Odisha, India route)
- **Interactive Dashboard** with 8 analytics panels
- **Live Activity Logs** with real-time updates
- **Speed Violation Alerts** (>90 km/h triggers)
- **Route Deviation Detection** (NH16/SH9A route)
- **PagerDuty-style Escalation System**
- **AI Smart Gate Camera Simulation**
- **Mobile-Responsive Design**

### 🚛 Fleet Details:
- **Route:** NTPC Talcher → Chandilkhol, Odisha
- **Vehicle Types:** Heavy Coal Transport Trucks  
- **Update Frequency:** Real-time (8-second intervals)
- **Monitoring:** 24/7 continuous tracking simulation

---

## 📞 Support & Contact

### For Demo Assistance:
- **Technical Issues:** Check troubleshooting section above
- **Feature Questions:** All features are pre-configured and running
- **Performance:** Demo optimized for presentation environments

### Demo URLs Summary:
- **Local Demo:** http://localhost:3004
- **API Documentation:** http://localhost:8006/docs
- **Health Check:** http://localhost:8006/health

---

## 🎯 Best Practices for Demo Presentation

1. **Pre-test:** Run `./start_demo.sh` before the actual demo
2. **Backup Plan:** Have ngrok/localtunnel ready for remote access
3. **Browser:** Use Chrome or Firefox for best compatibility
4. **Network:** Ensure stable internet for map tiles
5. **Screen:** Set browser to full-screen mode for presentation

---

*Last Updated: September 2025*
*FleetX Enhanced India Fleet Management System*
