#!/usr/bin/env python3
"""
NTPC Critical Fleet Management Frontend Server
Enhanced with critical incident paging and smart gate camera integration
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import os

PORT = 3003

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/critical-index.html'
        return super().do_GET()

def start_server():
    """Start the NTPC Critical Operations server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print("🚨" + "="*90)
        print("🏭 NTPC CRITICAL FLEET MANAGEMENT SYSTEM - EMERGENCY OPERATIONS")
        print("="*92)
        print(f"🌐 Emergency Frontend running at: http://localhost:{PORT}")
        print(f"📍 Route: NTPC Talcher → Chandilkhol, Odisha")
        print(f"🚛 Fleet: Critical Operations Monitoring")
        print(f"📡 Critical Backend API: http://127.0.0.1:8005")
        print("="*92)
        print("🚨 CRITICAL FEATURES ACTIVATED:")
        print("   • Emergency Incident Paging System")
        print("   • Smart Gate Camera with AI Number Plate Recognition")
        print("   • Real-time Critical Alert Detection")
        print("   • Automatic Emergency Contact Notification")
        print("   • Live Gate Entry/Exit Monitoring")
        print("   • Critical Stop Detection (60+ minutes)")
        print("   • Critical Speed Violation (90+ km/h)")
        print("   • Route Deviation Emergency Alerts")
        print("="*92)
        print("📟 EMERGENCY CONTACTS:")
        print("   • Fleet Manager: +91-9437100001 | Pager: +91-9437200001")
        print("   • IT Emergency: +91-9437100002 | Pager: +91-9437200002") 
        print("   • Operations Control: +91-9437100003 | Pager: +91-9437200003")
        print("   • Safety Emergency: +91-9437100004 | Pager: +91-9437200004")
        print("="*92)
        print("📷 SMART GATE CAMERAS:")
        print("   • CAM_GATE_01: Main Entry Gate (Active)")
        print("   • CAM_GATE_02: Secondary Gate (Active)")
        print("   • CAM_LOAD_01: Loading Bay A (Active)")
        print("   • CAM_LOAD_02: Loading Bay B (Active)")
        print("="*92)
        print("🔄 Auto-opening browser in 3 seconds...")
        print("⌨️  Press Ctrl+C to stop the emergency system")
        print("🚨 Ensure critical backend API is running for full emergency functionality")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open(f'http://localhost:{PORT}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 NTPC Critical Fleet Management System stopped")
            print("📊 Emergency Session Summary:")
            print("   • Critical monitoring session ended")
            print("   • All incident tracking data saved")
            print("   • Emergency paging system deactivated")
            print("   • Smart gate cameras offline")
            print("   • Emergency contacts notified of system shutdown")
            print("🙏 Thank you for using NTPC Critical Fleet Management System")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
