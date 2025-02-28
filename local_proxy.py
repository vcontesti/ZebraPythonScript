from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json
import socket

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get printer IP from query parameters
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        printer_ip = query.get('printer_ip', [''])[0]
        
        if not printer_ip:
            self.send_error(400, "Printer IP not specified")
            return
            
        try:
            # Try to connect to printer port 9100
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            port_result = sock.connect_ex((printer_ip, 9100)) == 0
            sock.close()
            
            # Try HTTP connection
            try:
                response = urllib.request.urlopen(f'http://{printer_ip}', timeout=5)
                http_result = response.getcode() == 200
            except:
                http_result = False
                
            # Send results back
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                'port_9100': port_result,
                'http': http_result,
                'details': [
                    f'Port 9100: {"Open" if port_result else "Closed"}',
                    f'HTTP: {"Connected" if http_result else "Failed"}'
                ]
            }
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_error(500, str(e))

    def do_POST(self):
        # Get printer IP and data from request
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode()
        
        try:
            # Forward request to printer
            printer_ip = self.headers.get('X-Printer-IP')
            if not printer_ip:
                self.send_error(400, "Printer IP not specified")
                return
                
            request = urllib.request.Request(
                f'http://{printer_ip}{self.path}',
                data=post_data.encode(),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            response = urllib.request.urlopen(request)
            
            # Send response back
            self.send_response(response.getcode())
            self.send_header('Content-Type', response.headers.get('Content-Type', 'text/plain'))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.read())
            
        except Exception as e:
            self.send_error(500, str(e))
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Printer-IP')
        self.end_headers()

if __name__ == '__main__':
    try:
        server = HTTPServer(('localhost', 5001), ProxyHandler)
        print("\nProxy server is running on http://localhost:5001")
        print("Use this URL in your render.com application")
        print("Press Ctrl+C to stop the server\n")
        server.serve_forever()
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nPress Enter to exit...")
        input()
