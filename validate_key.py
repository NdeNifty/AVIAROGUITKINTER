import requests
import uuid
import json

def get_mac_address():
    """Get the MAC address of the computer."""
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0, 11, 2)])

def validate_key(key):
    """Send the key and MAC address to the server for validation."""
    mac_address = get_mac_address()
    url = "http://yourserver.com/path/to/validate_key.php"
    data = {
        "key": key,
        "mac_address": mac_address
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()

if __name__ == "__main__":
    key = input("Enter your product key: ")
    result = validate_key(key)
    print(result)
