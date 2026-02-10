import requests
import json

try:
    response = requests.get("http://localhost:1234/v1/models")
    if response.status_code == 200:
        models = response.json()['data']
        print("Available models:")
        for m in models:
            print(f"- {m['id']}")
    else:
        print(f"Error: {response.status_code} {response.text}")
except Exception as e:
    print(f"Connection failed: {e}")
