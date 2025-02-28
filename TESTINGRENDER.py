from flask import Flask, request, jsonify, render_template_string
import requests
import time
import os
import ipaddress
import socket

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Zebra Printer Configuration</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        input[type="text"] {
            width: 100%;
            padding: 8px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        #testResult {
            margin-top: 15px;
            padding: 10px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Zebra Printer Configuration</h1>
        <div class="form-group">
            <label for="printer_ip">Printer IP Address:</label>
            <input type="text" id="printer_ip" name="printer_ip" placeholder="Enter printer IP address">
        </div>
        <button onclick="testConnection()">Test Connection</button>
        <button onclick="configurePrinter()">Configure Printer</button>
        <div id="testResult"></div>
    </div>
    
    <script>
        function testConnection() {
            const printerIp = document.getElementById('printer_ip').value;
            const resultDiv = document.getElementById('testResult');
            
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
                    html += `<p>Ping Test: ${data.ping ? '✅' : '❌'}</p>`;
                    html += `<p>Printer Port (9100): ${data.port_9100 ? '✅' : '❌'}</p>`;
                    html += `<p>HTTP Connection: ${data.http ? '✅' : '❌'}</p>`;
                    html += '<h4>Details:</h4><ul>';
                    data.details.forEach(detail => {
                        html += `<li>${detail}</li>`;
                    });
                    html += '</ul>';
                    
                    resultDiv.className = data.ping || data.port_9100 ? 'success' : 'error';
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
            const resultDiv = document.getElementById('testResult');
            
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = 'Configuring printer...';
            resultDiv.className = '';
            
            const formData = new FormData();
            formData.append('printer_ip', printerIp);
            
            fetch('/configure', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultDiv.className = 'error';
                    resultDiv.innerHTML = `Error: ${data.error}`;
                } else {
                    resultDiv.className = 'success';
                    resultDiv.innerHTML = 'Printer configured successfully!';
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

def configure_printer(printer_ip):
    """Configure the printer with increased timeout and detailed error handling"""
    try:
        # First verify we can reach the printer
        connection_test = test_printer_connection(printer_ip)
        if not connection_test['ping']:
            return {"status": "error", "message": "Cannot ping printer"}
            
        # Increase timeout for printer communication
        timeout = 10
        url = f'http://{printer_ip}/config.html'
        
        # Detailed logging of connection attempt
        print(f"Attempting to connect to {url} with timeout {timeout}s")
        
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            return {"status": "error", "message": f"Printer returned status code: {response.status_code}"}
            
        # Configuration commands with increased timeout
        config_url = f'http://{printer_ip}/config.html'
        config_data = {
            'config': 'your_config_here'  # Add your specific configuration
        }
        
        config_response = requests.post(config_url, data=config_data, timeout=timeout)
        if config_response.status_code != 200:
            return {"status": "error", "message": f"Configuration failed with status code: {config_response.status_code}"}
            
        return {"status": "success", "message": "Printer configured successfully"}
        
    except requests.Timeout:
        return {"status": "error", "message": "Connection timed out. Printer is reachable but not responding to configuration requests"}
    except requests.ConnectionError as e:
        return {"status": "error", "message": f"Connection error: {str(e)}. Printer is pingable but web interface may be disabled"}
    except requests.RequestException as e:
        return {"status": "error", "message": f"Failed to configure printer: {str(e)}"}

def test_printer_connection(printer_ip):
    """Test printer connectivity and return detailed status"""
    results = {
        'ip': printer_ip,
        'ping': False,
        'port_9100': False,
        'http': False,
        'details': []
    }
    
    # Test basic ping with increased count
    try:
        # Use 3 pings to be more certain
        response = os.system(f"ping -n 3 -w 1000 {printer_ip}")
        results['ping'] = response == 0
        results['details'].append('Ping successful' if response == 0 else 'Ping failed')
    except Exception as e:
        results['details'].append(f'Ping error: {str(e)}')

    # Test port 9100 (raw printing port) with increased timeout
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # Increased timeout to 5 seconds
        result = sock.connect_ex((printer_ip, 9100))
        sock.close()
        results['port_9100'] = result == 0
        results['details'].append(f'Port 9100: {"open" if result == 0 else "closed"} (error code: {result})')
    except socket.timeout:
        results['details'].append('Port 9100 test timed out after 5 seconds')
        results['port_9100'] = False
    except Exception as e:
        results['details'].append(f'Port 9100 test error: {str(e)}')

    # Test HTTP connection with increased timeout
    try:
        response = requests.get(f'http://{printer_ip}', timeout=5)  # Increased timeout to 5 seconds
        results['http'] = response.status_code == 200
        results['details'].append(f'HTTP connection successful (status {response.status_code})')
    except requests.Timeout:
        results['details'].append('HTTP connection timed out after 5 seconds')
    except requests.ConnectionError:
        results['details'].append('HTTP connection refused - web interface may be disabled')
    except requests.RequestException as e:
        results['details'].append(f'HTTP connection failed: {str(e)}')

    return results

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/configure', methods=['POST'])
def configure():
    printer_ip = request.form.get('printer_ip', '').strip()
    
    # Validate IP address
    try:
        # Check if it's a valid IP address format
        ip_obj = ipaddress.ip_address(printer_ip)
        
        # Ensure it's IPv4
        if not isinstance(ip_obj, ipaddress.IPv4Address):
            return jsonify({'error': 'Please enter a valid IPv4 address'}), 400
            
        # Basic connectivity check with timeout
        socket.create_connection((printer_ip, 9100), timeout=2)
        
        # If all checks pass, proceed with printer configuration
        result = configure_printer(printer_ip)
        return jsonify(result)
        
    except ValueError:
        return jsonify({'error': 'Invalid IP address format'}), 400
    except socket.timeout:
        return jsonify({'error': 'Could not connect to printer (timeout)'}), 400
    except socket.error:
        return jsonify({'error': 'Could not connect to printer. Please check if the printer is online'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/test_connection', methods=['POST'])
def test_connection():
    printer_ip = request.form.get('printer_ip', '').strip()
    
    try:
        # Validate IP format first
        ipaddress.ip_address(printer_ip)
        
        # Run connection tests
        results = test_printer_connection(printer_ip)
        return jsonify(results)
        
    except ValueError:
        return jsonify({'error': 'Invalid IP address format'}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)