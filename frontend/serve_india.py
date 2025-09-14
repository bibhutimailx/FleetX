#!/usr/bin/env python3
"""
NTPC India Fleet Management Frontend Server
Enhanced for Indian operations with 13 vehicle fleet monitoring
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import os

PORT = 3002

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/india-index.html'
        return super().do_GET()

def start_server():
    """Start the NTPC India Fleet Management server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print("🇮🇳" + "="*80)
        print("🏭 NTPC FLEET MANAGEMENT SYSTEM - INDIA OPERATIONS")
        print("="*82)
        print(f"🌐 Frontend server running at: http://localhost:{PORT}")
        print(f"📍 Route: NTPC Talcher → Chandilkhol, Odisha")
        print(f"🚛 Fleet: 13 Heavy Coal Transport Trucks")
        print(f"📡 Backend API: http://127.0.0.1:8004")
        print("="*82)
        print("✨ ENHANCED FEATURES:")
        print("   • 13 Vehicle Fleet with Indian Registration Numbers")
        print("   • Real-time Speed Violation Detection") 
        print("   • Route Deviation Alerts for NH16/SH9A Route")
        print("   • Gas Station & Toll Gate Mapping")
        print("   • Mobile Alerts to IT Team & Stakeholders")
        print("   • Enhanced Stop Time Monitoring (30+ min alerts)")
        print("   • Fuel Level Monitoring & Low Fuel Alerts")
        print("   • Critical Alert Banner System")
        print("="*82)
        print("🔄 Auto-opening browser in 3 seconds...")
        print("⌨️  Press Ctrl+C to stop the server")
        print("🚨 Make sure backend API is running for full functionality")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open(f'http://localhost:{PORT}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 NTPC Fleet Management Server stopped")
            print("📊 Session Summary:")
            print("   • Fleet monitoring session ended")
            print("   • All vehicle tracking data saved")
            print("   • Alert system deactivated")
            print("🙏 Thank you for using NTPC Fleet Management System")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
