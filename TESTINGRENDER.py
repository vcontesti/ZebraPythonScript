from flask import Flask, request, jsonify
import requests
import time

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

    # Login data
    login_data = {"0": "admin", "1": "1234"}
    session.post(settings_setup_url, data=login_data)

    # Payloads
    media_setup_data = {"0": "1", "1": "1", "2": "1", "3": "0", "4": "832", "5": "3048", "submit": "Submit Changes"}
    general_setup_data = {"2": "0", "4": "26.0", "6": "4", "5": "0", "7": "2", "8": "0", "submit": "Submit Changes"}
    second_general_setup_data = {"6": "1", "submit": "Submit Changes"}
    settings_setup_data = {"0": "Save Current Configuration"}
    feed_request_data = {"1": "submit"}
    test_print_data = {"4": "submit"}

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Apply settings
    session.post(media_setup_url, data=media_setup_data, headers=headers)
    session.post(general_setup_url, data=general_setup_data, headers=headers)
    time.sleep(1)
    session.post(feed_request_url, data=feed_request_data, headers=headers)
    time.sleep(2)
    session.post(general_setup_url, data=second_general_setup_data, headers=headers)
    time.sleep(2)
    session.post(test_print_url, data=test_print_data, headers=headers)
    session.post(settings_setup_url, data=settings_setup_data, headers=headers)

    return {"status": "Success", "message": "Printer configured successfully"}


# API Route to configure printer
@app.route('/configure', methods=['POST'])
def configure():
    data = request.get_json()
    printer_ip = data.get("printer_ip")
    if not printer_ip:
        return jsonify({"error": "Missing printer IP"}), 400

    result = configure_printer(printer_ip)
    return jsonify(result)


# Home Route
@app.route('/')
def home():
    return "Flask app is running!"


if __name__ == '__main__':
    import os

    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)