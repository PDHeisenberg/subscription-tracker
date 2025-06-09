import requests
import time

# Give server time to start
time.sleep(2)

try:
    # Test if server is running
    response = requests.get('http://localhost:8080/', timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")
    print("First 500 chars of response:")
    print(response.text[:500])
except Exception as e:
    print(f"Error connecting to server: {e}")