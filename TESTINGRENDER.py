from flask import Flask, request, jsonify, render_template_string
import requests
import time
import os
import ipaddress
import socket
import re
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urljoin

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Zebra Printer Configuration</title>
    <style>
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: Arial, sans-serif;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
        }
        .form-group input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        #testResult, #configResult {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            display: none;
        }
        .success {
            background-color: #dff0d8;
            border: 1px solid #d6e9c6;
            color: #3c763d;
        }
        .error {
            background-color: #f2dede;
            border: 1px solid #ebccd1;
            color: #a94442;
        }
        .step {
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
        }
        .step.success {
            background-color: #dff0d8;
        }
        .step.error {
            background-color: #f2dede;
        }
        .advanced-settings {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zebra Printer Configuration</h1>
        <div class="form-group">
            <label for="printer_ip">Printer IP Address:</label>
            <input type="text" id="printer_ip" name="printer_ip" placeholder="Enter printer IP address">
        </div>
        <div class="form-group">
            <a href="#" onclick="toggleAdvanced()">Advanced Settings</a>
        </div>
        <div id="advancedSettings" class="advanced-settings">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" value="admin">
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" value="1234">
            </div>
        </div>
        <button onclick="testConnection()">Test Connection</button>
        <button onclick="configurePrinter()">Configure Printer</button>
        <div id="testResult"></div>
        <div id="configResult"></div>
    </div>
    
    <script>
        function toggleAdvanced() {
            const advancedSettings = document.getElementById('advancedSettings');
            advancedSettings.style.display = advancedSettings.style.display === 'none' ? 'block' : 'none';
        }

        function testConnection() {
            const printerIp = document.getElementById('printer_ip').value;
            const resultDiv = document.getElementById('testResult');
            
            if (!printerIp) {
                resultDiv.className = 'error';
                resultDiv.innerHTML = 'Please enter a printer IP address';
                return;
            }
            
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = 'Testing connection...';
            resultDiv.className = '';
            
            const formData = new FormData();
            formData.append('printer_ip', printerIp);
            
            fetch('/test_connection', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `Error: ${data.error}`;
                } else {
                    let html = '<h3>Connection Test Results:</h3>';
                    
                    // Show ping result only if available
                    if ('ping' in data) {
                        html += `<p>Ping Test: ${data.ping ? '✅' : '❌'}</p>`;
                    }
                    
                    // Always show port and HTTP results
                    html += `<p>Printer Port (9100): ${data.port_9100 ? '✅' : '❌'}</p>`;
                    html += `<p>HTTP Connection: ${data.http ? '✅' : '❌'}</p>`;
                    
                    html += '<h4>Details:</h4><ul>';
                    data.details.forEach(detail => {
                        html += `<li>${detail}</li>`;
                    });
                    html += '</ul>';
                    
                    resultDiv.className = data.port_9100 ? 'success' : 'error';
                    resultDiv.innerHTML = html;
                }
            })
            .catch(error => {
                resultDiv.className = 'error';
                resultDiv.innerHTML = `Error: ${error.message}`;
            });
        }
        
        function configurePrinter() {
            const printerIp = document.getElementById('printer_ip').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const resultDiv = document.getElementById('configResult');
            
            if (!printerIp) {
                resultDiv.className = 'error';
                resultDiv.innerHTML = 'Please enter a printer IP address';
                return;
            }
            
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = 'Configuring printer...';
            resultDiv.className = '';
            
            const formData = new FormData();
            formData.append('printer_ip', printerIp);
            formData.append('username', username);
            formData.append('password', password);
            
            fetch('/configure', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `<h3>Configuration Failed</h3><p>Error: ${data.error}</p>`;
                    
                    if (data.steps && data.steps.length > 0) {
                        resultDiv.innerHTML += '<h4>Steps Completed:</h4>';
                        data.steps.forEach(step => {
                            resultDiv.innerHTML += `<div class="step ${step.status}">${step.step}: ${step.status}</div>`;
                        });
                    }
                } else {
                    resultDiv.className = 'success';
                    resultDiv.innerHTML = '<h3>Printer Configuration Successful!</h3>';
                    resultDiv.innerHTML += '<h4>Completed Steps:</h4>';
                    data.steps.forEach(step => {
                        resultDiv.innerHTML += `<div class="step success">${step.step}: ${step.status}</div>`;
                    });
                }
            })
            .catch(error => {
                resultDiv.className = 'error';
                resultDiv.innerHTML = `Error: ${error.message}`;
            });
        }
    </script>
</body>
</html>
"""

@dataclass
class PrinterConfig:
    """Configuration settings for the Zebra printer."""
    media_setup: Dict[str, str] = None
    general_setup: Dict[str, str] = None
    settings_setup: Dict[str, str] = None
    feed_request: Dict[str, str] = None
    test_print: Dict[str, str] = None

    def __post_init__(self):
        # Default configuration values
        self.media_setup = {
            "0": "1", "1": "1", "2": "1", "3": "0",
            "4": "832", "5": "3048", "submit": "Submit Changes"
        }
        self.general_setup = {
            "2": "0", "4": "26.0", "6": "4", "5": "0",
            "7": "2", "8": "0", "submit": "Submit Changes"
        }
        self.settings_setup = {"0": "Save Current Configuration"}
        self.feed_request = {"1": "submit"}
        self.test_print = {"4": "submit"}

class ZebraPrinter:
    """Class to manage Zebra printer operations."""
    
    def __init__(self, ip_address: str, username: str = "admin", password: str = "1234"):
        """Initialize printer with connection details."""
        self.validate_ip_address(ip_address)
        self.base_url = f"http://{ip_address}"
        self.session = requests.Session()
        self.config = PrinterConfig()
        self._credentials = {"0": username, "1": password}
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            raise ValueError("Invalid IP address format")
        return True

    def _make_request(self, endpoint: str, data: Dict, method: str = 'POST') -> Optional[requests.Response]:
        """Make HTTP request with error handling."""
        try:
            url = urljoin(self.base_url, endpoint)
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            app.logger.error(f"Request failed: {str(e)}")
            return None

    def configure_printer(self) -> Dict[str, any]:
        """Configure the printer with all settings."""
        results = {
            'success': False,
            'steps': [],
            'error': None
        }

        try:
            # Step 1: Login
            if not self.login():
                results['error'] = "Failed to authenticate with printer"
                return results
            results['steps'].append({'step': 'Login', 'status': 'success'})

            # Step 2: Media Setup
            if not self.update_media_setup():
                results['error'] = "Failed to update media setup"
                return results
            results['steps'].append({'step': 'Media Setup', 'status': 'success'})
            time.sleep(2)

            # Step 3: General Setup
            if not self.update_general_setup():
                results['error'] = "Failed to update general setup"
                return results
            results['steps'].append({'step': 'General Setup', 'status': 'success'})
            time.sleep(2)

            # Step 4: Feed Request
            if not self.request_feed():
                results['error'] = "Failed to execute feed request"
                return results
            results['steps'].append({'step': 'Feed Request', 'status': 'success'})
            time.sleep(2)

            # Step 5: Cutter Mode Setup
            if not self.update_general_setup(True):
                results['error'] = "Failed to update cutter mode"
                return results
            results['steps'].append({'step': 'Cutter Mode Setup', 'status': 'success'})
            time.sleep(2)

            # Step 6: Test Print
            if not self.print_test():
                results['error'] = "Failed to execute test print"
                return results
            results['steps'].append({'step': 'Test Print', 'status': 'success'})
            time.sleep(2)

            # Step 7: Save Settings
            if not self.save_settings():
                results['error'] = "Failed to save settings"
                return results
            results['steps'].append({'step': 'Save Settings', 'status': 'success'})

            results['success'] = True
            return results

        except Exception as e:
            results['error'] = str(e)
            return results

    def login(self) -> bool:
        """Authenticate with the printer."""
        response = self._make_request('/settings', self._credentials)
        return bool(response)

    def update_media_setup(self) -> bool:
        """Update media configuration."""
        response = self._make_request('/setmed', self.config.media_setup)
        return bool(response)

    def update_general_setup(self, cutter_mode: bool = False) -> bool:
        """Update general configuration."""
        data = self.config.general_setup.copy()
        if cutter_mode:
            data["6"] = "1"
        response = self._make_request('/setgen', data)
        return bool(response)

    def save_settings(self) -> bool:
        """Save current configuration."""
        response = self._make_request('/settings', self.config.settings_setup)
        return bool(response)

    def request_feed(self) -> bool:
        """Request paper feed."""
        response = self._make_request('/control', self.config.feed_request)
        return bool(response)

    def print_test(self) -> bool:
        """Perform test print."""
        response = self._make_request('/setlst', self.config.test_print)
        return bool(response)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    return jsonify({"status": "success", "message": "Zebra Printer Configuration API"})

@app.route('/configure', methods=['POST'])
def configure_printer():
    """Configure the Zebra printer with all settings."""
    printer_ip = request.form.get('printer_ip', '').strip()
    username = request.form.get('username', 'admin').strip()
    password = request.form.get('password', '1234').strip()

    try:
        # Initialize and configure printer
        printer = ZebraPrinter(printer_ip, username, password)
        results = printer.configure_printer()
        
        if results['success']:
            return jsonify({
                'success': True,
                'steps': results['steps']
            })
        else:
            return jsonify({
                'error': results['error'],
                'steps': results['steps']
            }), 400

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Configuration error: {str(e)}")
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

@app.route('/test_connection', methods=['POST'])
def test_connection():
    printer_ip = request.form.get('printer_ip', '').strip()
    
    try:
        # First validate IP format
        ipaddress.ip_address(printer_ip)
        
        # For render website, we'll use a simpler connection test that doesn't rely on local network commands
        if os.environ.get('RENDER') or not os.name == 'nt':  # Check if we're on render or not on Windows
            results = {
                'ip': printer_ip,
                'ping': False,
                'port_9100': False,
                'http': False,
                'details': []
            }
            
            # Use socket for basic connection test
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((printer_ip, 9100))
                sock.close()
                
                results['port_9100'] = result == 0
                results['details'].append(f'Port 9100: {"open" if result == 0 else "closed"}')
            except Exception as e:
                results['details'].append(f'Port 9100 test error: {str(e)}')

            # Try HTTP connection
            try:
                response = requests.get(f'http://{printer_ip}', timeout=5)
                results['http'] = response.status_code == 200
                results['details'].append(f'HTTP connection: Status {response.status_code}')
            except Exception as e:
                results['details'].append(f'HTTP connection failed: {str(e)}')
                
            return jsonify(results)
        else:
            # On localhost/Windows, use our full test suite
            results = test_printer_connection(printer_ip)
            return jsonify(results)
            
    except ValueError:
        return jsonify({'error': 'Invalid IP address format'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def test_printer_port(ip, port, timeout=10):
    """Test a specific printer port using Test-NetConnection"""
    try:
        # Use Test-NetConnection which we know works
        cmd = f'powershell -Command "Test-NetConnection -ComputerName {ip} -Port {port} | Select-Object -ExpandProperty TcpTestSucceeded"'
        result = os.popen(cmd).read().strip().lower()
        
        success = result == "true"
        print(f"Test-NetConnection to {ip}:{port} {'succeeded' if success else 'failed'}")
        return success, f"Port {port} is {'open' if success else 'closed'}"
        
    except Exception as e:
        print(f"Error testing connection to {ip}:{port}: {e}")
        return False, f"Port {port} test error: {str(e)}"

def test_printer_connection(printer_ip):
    """Test printer connectivity"""
    results = {
        'ip': printer_ip,
        'ping': False,
        'port_9100': False,
        'http': False,
        'details': []
    }
    
    # Test ping
    try:
        print(f"\nPinging {printer_ip}...")
        ping_output = os.popen(f'ping -n 2 -w 1000 {printer_ip}').read()
        results['ping'] = "bytes=" in ping_output
        results['details'].append(f'Ping test: {"Successful" if results["ping"] else "Failed"}')
        results['details'].append(f'Ping details:\n{ping_output}')
    except Exception as e:
        print(f"Error during ping: {e}")
        results['details'].append(f'Ping error: {str(e)}')

    # Always test port 9100 regardless of ping
    print(f"\nTesting printer port 9100...")
    success, message = test_printer_port(printer_ip, 9100)
    results['port_9100'] = success
    results['details'].append(f'Printer port (9100): {message}')

    # Test HTTP connection
    try:
        print(f"\nTesting HTTP connection to {printer_ip}...")
        response = requests.get(f'http://{printer_ip}', timeout=5)
        results['http'] = response.status_code == 200
        results['details'].append(f'HTTP connection: Status {response.status_code}')
    except requests.Timeout:
        print("HTTP connection timed out")
        results['details'].append('HTTP connection timed out')
    except requests.ConnectionError as e:
        print(f"HTTP connection error: {e}")
        results['details'].append(f'HTTP connection refused: {str(e)}')
    except requests.RequestException as e:
        print(f"HTTP request error: {e}")
        results['details'].append(f'HTTP connection failed: {str(e)}')

    return results

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)