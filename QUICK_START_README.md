# 🚛 FleetX Enhanced India Fleet Management - Quick Start Guide

## ⚡ IMMEDIATE SOLUTION for localhost:3004 Access

### 🎯 **Problem:** Cannot access http://localhost:3004/
### ✅ **Solution:** Follow these 3 simple steps:

---

## 🚀 Method 1: One-Click Start (RECOMMENDED)

```bash
# Step 1: Navigate to project directory
cd /Users/bibhutisahoo/Downloads/GITHUB/FleetX

# Step 2: Install dependencies (one-time setup)
./install_dependencies.sh

# Step 3: Start the demo
./start_demo.sh

# ✅ Access your UI at: http://localhost:3004
```

**That's it!** Your enhanced India fleet management system is now running.

---

## 🔧 Method 2: Manual Start (If automatic doesn't work)

### Terminal 1 - Backend API:
```bash
cd /Users/bibhutisahoo/Downloads/GITHUB/FleetX/backend
python3 enhanced_india_fleet_api.py
```
**✅ Backend will start on: http://localhost:8006**

### Terminal 2 - Frontend UI:
```bash
cd /Users/bibhutisahoo/Downloads/GITHUB/FleetX/frontend  
python3 serve_enhanced_india.py
```
**✅ Frontend will start on: http://localhost:3004**

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
python3 -m pip install fastapi uvicorn pydantic --user
```

### Issue: "Port 3004 already in use"
**Solution:**
```bash
# Kill any processes using the port
lsof -ti:3004 | xargs kill -9
lsof -ti:8006 | xargs kill -9
```

### Issue: "command not found: python"
**Solution:**
Use `python3` instead of `python` in all commands.

---

## 📊 What You'll See at localhost:3004

### 🇮🇳 Enhanced India Fleet Features:
- **13 Heavy Coal Transport Trucks** (OD-03-NT-1001 to 1013)
- **Real-time Route Tracking** (NTPC Talcher → Chandilkhol, Odisha)
- **Interactive Map** with live vehicle positions
- **Speed Violation Alerts** (triggers at >90 km/h)
- **Route Deviation Detection** (NH16/SH9A monitoring)
- **PagerDuty-style Emergency Escalation**
- **AI Smart Gate Camera System**
- **Live Activity Dashboard** with 8 analytics panels

### 🚨 Alert System:
- **Extended Stop Alerts** (>60 minutes)
- **Critical Speed Violations** (>90 km/h)
- **Route Deviation Warnings** (off-route >30 min)
- **Low Fuel Alerts** (<15%)

---

## 🌐 Alternative Access Methods

### For Remote Demo (Public URL):
```bash
# Start local demo first
./start_demo.sh

# Then in another terminal, create public tunnel:
npx localtunnel --port 3004
# OR install ngrok and run:
ngrok http 3004
```

### Cloud Deployment Options:
See `DEMO_DEPLOYMENT_GUIDE.md` for Railway, Render, Heroku, and Docker options.

---

## 📱 Mobile Access

The UI is fully responsive and works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Mobile devices (iOS Safari, Android Chrome)
- ✅ Tablets (iPad, Android tablets)

---

## 🔍 System URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Main UI** | http://localhost:3004 | Enhanced India Fleet Dashboard |
| **API Docs** | http://localhost:8006/docs | Interactive API Documentation |
| **Health Check** | http://localhost:8006/health | System Status |

---

## ⚙️ System Requirements

- **Python 3.8+** ✅ (You have Python 3.9.6)
- **Modern Web Browser** ✅
- **Internet Connection** ✅ (for map tiles)
- **Ports 3004 & 8006** available

---

## 📞 Demo Support

### Before Your Demo:
1. ✅ Run `./start_demo.sh` to test everything works
2. ✅ Access http://localhost:3004 to verify UI loads
3. ✅ Keep the terminal open during demo
4. ✅ Have backup: ngrok/localtunnel for remote access

### During Demo:
- **Show Features:** Real-time tracking, alerts, route monitoring
- **Demonstrate:** Speed violations, geofence alerts, emergency escalation
- **Highlight:** AI camera system, PagerDuty integration, Indian fleet data

---

## 🎯 Success Checklist

- [ ] Dependencies installed (`./install_dependencies.sh`)
- [ ] Backend running on port 8006
- [ ] Frontend running on port 3004
- [ ] UI accessible at http://localhost:3004
- [ ] Map loads with 13 Indian vehicles
- [ ] Real-time updates working (8-second intervals)
- [ ] Alert system functional

---

## 📝 Quick Commands Reference

```bash
# Install everything
./install_dependencies.sh

# Start demo
./start_demo.sh

# Check if running
curl http://localhost:3004
curl http://localhost:8006/health

# Stop demo
# Press Ctrl+C in the terminal running start_demo.sh

# Emergency port cleanup
lsof -ti:3004 | xargs kill -9
lsof -ti:8006 | xargs kill -9
```

---

**🎉 Your FleetX Enhanced India Fleet Management System is now ready for demo!**

*Access at: http://localhost:3004*
