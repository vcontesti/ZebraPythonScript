import requests
import time
# Requesting input for IP address
def get_printer_ip():
    return input("Enter the printer's IP address: ")
# Define the printer's IP address
printer_ip = get_printer_ip()
# Define Username and password to use when requested
login_data = {
    "0": "admin",
    "1": "1234"
}

session = requests.Session()

# Define the URL endpoints for the settings you want to change
media_setup_url = f"http://{printer_ip}/setmed"
general_setup_url = f"http://{printer_ip}/setgen"
settings_setup_url = f"http://{printer_ip}/settings"
feed_request_url = f"http://{printer_ip}/control"
test_print_url = f"http://{printer_ip}/setlst"

# Login details
def login_details():
    response = session.post(settings_setup_url,data =login_data)
# Define the payload for media setup changes
media_setup_data = { "0": "1","1": "1", "2": "1", "3": "0", "4": "832", "5": "3048","submit":"Submit Changes" }
# Define the payload for general setup changes
general_setup_data = { "2": "0", "4": "26.0", "6": "4","5": "0", "7": "2", "8": "0", "submit":"Submit Changes" }
second_general_setup_data = {"6":"1", "submit":"Submit Changes" }
# Define the payload for setting changes
settings_setup_data = {"0":"Save Current Configuration"}
# Feed request data
feed_request_data = {"1":"submit"}
# Test print data
test_print_data = {"4":"submit"}
# Headers for the request, adjust according to what the printer's web interface requires
headers = { "Content-Type": "application/x-www-form-urlencoded" }
# Function to send the request to change media setup
def change_media_setup():
    response=requests.post(media_setup_url, data=media_setup_data, headers=headers)
    if response.status_code == 200:
        print("Media setup updated successfully.")
    else:
        print(f"Failed to update media setup. Status code: {response.status_code}")
# Function to send the request to change general setup
def change_general_setup():
    response = requests.post(general_setup_url, data=general_setup_data, headers=headers)
    if response.status_code == 200:
        print("General setup updated successfully.")
    else:
        print(f"Failed to update general setup. Status code: {response.status_code}")
# Function to send the request to change general to cutter for testing
def change_general_setup_tear_off():
    response = requests.post(general_setup_url, data=second_general_setup_data, headers=headers)
    if response.status_code == 200:
        print("General setup updated successfully.")
    else:
        print(f"Failed to update general setup. Status code: {response.status_code}")
# Function to send all settings to change
def change_settings_setup():
    response = requests.post(settings_setup_url, data=settings_setup_data, headers=headers)
    if response.status_code == 200:
        print("Settings setup updated successfully.")
    else:
        print(f"Failed to update settings setup. Status code: {response.status_code}")

# Function to request the feed twice
def feed_request():
    response = requests.post(feed_request_url, data=feed_request_data, headers=headers)
    print("Requested properly")

def test_print():
    response = requests.post(test_print_url, data=test_print_data, headers=headers)
    print("Requested properly")

login_details()
# Change media setup
change_media_setup()
# Change general setup
change_general_setup()
time.sleep(1)
feed_request()
time.sleep(2)
change_general_setup_tear_off()
time.sleep(2)
test_print()

# Change settings
change_settings_setup()