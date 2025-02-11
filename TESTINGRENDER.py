from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

# Global session for requests
session = requests.Session()


def configure_printer(printer_ip):
    """Configures a printer using its IP address."""

    # Define Username and password for login
    login_data = {
        "0": "admin",
        "1": "1234"
    }

    # Define URL endpoints for the printer
    media_setup_url = f"http://{printer_ip}/setmed"
    general_setup_url = f"http://{printer_ip}/setgen"
    settings_setup_url = f"http://{printer_ip}/settings"
    feed_request_url = f"http://{printer_ip}/control"
    test_print_url = f"http://{printer_ip}/setlst"

    # Headers
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Payloads for different configurations
    media_setup_data = {"0": "1", "1": "1", "2": "1", "3": "0", "4": "832", "5": "3048", "submit": "Submit Changes"}
    general_setup_data = {"2": "0", "4": "26.0", "6": "4", "5": "0", "7": "2", "8": "0", "submit": "Submit Changes"}
    second_general_setup_data = {"6": "1", "submit": "Submit Changes"}
    settings_setup_data = {"0": "Save Current Configuration"}
    feed_request_data = {"1": "submit"}
    test_print_data = {"4": "submit"}

    try:
        # Login to printer
        login_response = session.post(settings_setup_url, data=login_data)
        if login_response.status_code != 200:
            return {"error": "Login failed", "status_code": login_response.status_code}

        # Update media setup
        response = session.post(media_setup_url, data=media_setup_data, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to update media setup", "status_code": response.status_code}

        # Update general setup
        response = session.post(general_setup_url, data=general_setup_data, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to update general setup", "status_code": response.status_code}

        time.sleep(1)

        # Request feed
        session.post(feed_request_url, data=feed_request_data, headers=headers)

        time.sleep(2)

        # Change general setup tear-off
        response = session.post(general_setup_url, data=second_general_setup_data, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to update tear-off settings", "status_code": response.status_code}

        time.sleep(2)

        # Request test print
        session.post(test_print_url, data=test_print_data, headers=headers)

        # Save settings
        response = session.post(settings_setup_url, data=settings_setup_data, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to save settings", "status_code": response.status_code}

        return {"status": "Success", "message": f"Configured printer {printer_ip}"}

    except Exception as e:
        return {"error": str(e)}


@app.route('/configure', methods=['POST'])
def configure():
    """API endpoint to configure a printer."""
    data = request.get_json()
    printer_ip = data.get("printer_ip")

    if not printer_ip:
        return jsonify({"error": "Missing printer IP"}), 400

    result = configure_printer(printer_ip)

    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Get PORT from environment, default to 5000
    app.run(host='0.0.0.0', port=port)