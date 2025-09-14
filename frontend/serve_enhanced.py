#!/usr/bin/env python3
"""
Enhanced HTTP server for the Fleet Management frontend
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import os

PORT = 3001

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/enhanced-index.html'
        return super().do_GET()

def start_server():
    """Start the enhanced HTTP server"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🌐 Enhanced Frontend server running at: http://localhost:{PORT}")
        print(f"📁 Serving enhanced UI from: {os.getcwd()}")
        print("🔄 Auto-opening browser in 2 seconds...")
        print("📡 Backend API should be running on http://127.0.0.1:8003")
        print("✨ Enhanced features: Route tracking, Alerts, Deviation detection")
        print("⌨️  Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open(f'http://localhost:{PORT}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Enhanced server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
