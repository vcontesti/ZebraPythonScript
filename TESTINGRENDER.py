from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

# Function to configure the printer
def configure_printer(printer_ip):
    session = requests.Session()

    # Define the URLs
    media_setup_url = f"http://{printer_ip}/setmed"
    general_setup_url = f"http://{printer_ip}/setgen"
    settings_setup_url = f"http://{printer_ip}/settings"
    feed_request_url = f"http://{printer_ip}/control"
    test_print_url = f"http://{printer_ip}/setlst"

    try:
        # Login data
        login_data = {"0": "admin", "1": "1234"}
        login_response = session.post(settings_setup_url, data=login_data)
        login_response.raise_for_status()

        # Payloads
        media_setup_data = {"0": "1", "1": "1", "2": "1", "3": "0", "4": "832", "5": "3048", "submit": "Submit Changes"}
        general_setup_data = {"2": "0", "4": "26.0", "6": "4", "5": "0", "7": "2", "8": "0", "submit": "Submit Changes"}
        second_general_setup_data = {"6": "1", "submit": "Submit Changes"}
        settings_setup_data = {"0": "Save Current Configuration"}
        feed_request_data = {"1": "submit"}
        test_print_data = {"4": "submit"}

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Apply settings
        session.post(media_setup_url, data=media_setup_data, headers=headers).raise_for_status()
        session.post(general_setup_url, data=general_setup_data, headers=headers).raise_for_status()
        time.sleep(1)
        session.post(feed_request_url, data=feed_request_data, headers=headers).raise_for_status()
        time.sleep(2)
        session.post(general_setup_url, data=second_general_setup_data, headers=headers).raise_for_status()
        time.sleep(2)
        session.post(test_print_url, data=test_print_data, headers=headers).raise_for_status()
        session.post(settings_setup_url, data=settings_setup_data, headers=headers).raise_for_status()

        return {"status": "success", "message": "Printer configured successfully"}
    except requests.RequestException as e:
        return {"status": "error", "message": f"Failed to configure printer: {str(e)}"}, 500

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Zebra Printer Configuration API"})

# API Route to configure printer
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