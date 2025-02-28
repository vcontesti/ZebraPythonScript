from flask import Flask, request, jsonify, render_template_string
import requests
import time
import os

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
        }
        button:hover {
            background-color: #45a049;
        }
        #result {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
            border: 1px solid #d6e9c6;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
            border: 1px solid #ebccd1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zebra Printer Configuration</h1>
        <div class="form-group">
            <label for="printer_ip">Printer IP Address:</label>
            <input type="text" id="printer_ip" placeholder="Enter printer IP address">
        </div>
        <button onclick="configurePrinter()">Configure Printer</button>
        <div id="result"></div>
    </div>

    <script>
        async function configurePrinter() {
            const printerIp = document.getElementById('printer_ip').value;
            const resultDiv = document.getElementById('result');
            
            if (!printerIp) {
                resultDiv.className = 'error';
                resultDiv.textContent = 'Please enter a printer IP address';
                return;
            }

            resultDiv.textContent = 'Configuring printer...';
            resultDiv.className = '';

            try {
                const response = await fetch('/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ printer_ip: printerIp })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                resultDiv.textContent = data.message || 'Configuration completed';
                resultDiv.className = data.status === 'success' ? 'success' : 'error';
            } catch (error) {
                console.error('Error:', error);
                resultDiv.textContent = 'Error: Could not connect to the printer. Please check the IP address and try again.';
                resultDiv.className = 'error';
            }
        }
    </script>
</body>
</html>
"""

def configure_printer(printer_ip):
    session = requests.Session()

    try:
        # Define the URLs
        media_setup_url = f"http://{printer_ip}/setmed"
        general_setup_url = f"http://{printer_ip}/setgen"
        settings_setup_url = f"http://{printer_ip}/settings"
        feed_request_url = f"http://{printer_ip}/control"
        test_print_url = f"http://{printer_ip}/setlst"

        # Login data
        login_data = {"0": "admin", "1": "1234"}
        login_response = session.post(settings_setup_url, data=login_data, timeout=10)
        login_response.raise_for_status()

        # Payloads
        media_setup_data = {"0": "1", "1": "1", "2": "1", "3": "0", "4": "832", "5": "3048", "submit": "Submit Changes"}
        general_setup_data = {"2": "0", "4": "26.0", "6": "4", "5": "0", "7": "2", "8": "0", "submit": "Submit Changes"}
        second_general_setup_data = {"6": "1", "submit": "Submit Changes"}
        settings_setup_data = {"0": "Save Current Configuration"}
        feed_request_data = {"1": "submit"}
        test_print_data = {"4": "submit"}

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Apply settings with timeout and error checking
        session.post(media_setup_url, data=media_setup_data, headers=headers, timeout=10).raise_for_status()
        session.post(general_setup_url, data=general_setup_data, headers=headers, timeout=10).raise_for_status()
        time.sleep(1)
        session.post(feed_request_url, data=feed_request_data, headers=headers, timeout=10).raise_for_status()
        time.sleep(2)
        session.post(general_setup_url, data=second_general_setup_data, headers=headers, timeout=10).raise_for_status()
        time.sleep(2)
        session.post(test_print_url, data=test_print_data, headers=headers, timeout=10).raise_for_status()
        session.post(settings_setup_url, data=settings_setup_data, headers=headers, timeout=10).raise_for_status()

        return {"status": "success", "message": "Printer configured successfully"}

    except requests.Timeout:
        return {"status": "error", "message": "Connection timed out. Please check if the printer is accessible."}
    except requests.ConnectionError:
        return {"status": "error", "message": "Could not connect to the printer. Please check the IP address and network connection."}
    except requests.RequestException as e:
        return {"status": "error", "message": f"Failed to configure printer: {str(e)}"}

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/configure', methods=['POST'])
def configure():
    try:
        data = request.get_json()
        if not data or 'printer_ip' not in data:
            return jsonify({"status": "error", "message": "Printer IP is required"}), 400
            
        printer_ip = data["printer_ip"]
        result = configure_printer(printer_ip)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)