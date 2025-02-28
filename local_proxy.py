from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json
import socket
import urllib.parse

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
        try:
            # Get printer IP from header
            printer_ip = self.headers.get('X-Printer-IP')
            if not printer_ip:
                self.send_error(400, "Printer IP not specified")
                return

            # Read POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode()
            
            # Parse the form data
            form_data = urllib.parse.parse_qs(post_data)
            username = form_data.get('username', ['admin'])[0]
            password = form_data.get('password', ['1234'])[0]

            # Define configuration steps
            config_steps = [
                {
                    'name': 'Login',
                    'url': f'http://{printer_ip}/login',
                    'data': urllib.parse.urlencode({'0': username, '1': password}).encode()
                },
                {
                    'name': 'Media Setup',
                    'url': f'http://{printer_ip}/media_setup',
                    'data': urllib.parse.urlencode({'1': '0', '16': '0', '15': '0'}).encode()
                },
                {
                    'name': 'General Setup',
                    'url': f'http://{printer_ip}/general_setup',
                    'data': urllib.parse.urlencode({'1': '0', '12': '0'}).encode()
                },
                {
                    'name': 'Save Settings',
                    'url': f'http://{printer_ip}/save_settings',
                    'data': urllib.parse.urlencode({'1': '1'}).encode()
                }
            ]

            # Execute configuration steps
            steps_results = []
            session = urllib.request.build_opener()
            session.addheaders = [('Content-Type', 'application/x-www-form-urlencoded')]

            for step in config_steps:
                try:
                    print(f"Trying {step['name']}: {step['url']}")
                    request = urllib.request.Request(
                        step['url'],
                        data=step['data'],
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    )
                    response = session.open(request, timeout=10)
                    response_data = response.read().decode()
                    print(f"Response: {response_data}")

                    # Check for specific error messages in response
                    if "Incorrect" in response_data:
                        raise Exception("Invalid credentials")
                    
                    success = response.code == 200 and "Error" not in response_data
                    steps_results.append({
                        'step': step['name'],
                        'status': 'success' if success else 'error',
                        'response': response_data
                    })

                    if not success:
                        raise Exception(f"Step failed: {response_data}")

                except Exception as e:
                    print(f"Error in {step['name']}: {str(e)}")
                    steps_results.append({
                        'step': step['name'],
                        'status': 'error',
                        'error': str(e)
                    })
                    break

            # Send response back
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = {
                'success': all(step['status'] == 'success' for step in steps_results),
                'steps': steps_results
            }
            
            self.wfile.write(json.dumps(result).encode())
            
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
