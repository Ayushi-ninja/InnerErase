import requests
import time

try:
    print("Sending /analyze request...")
    resp = requests.post("http://127.0.0.1:5000/analyze", json={"message": "I feel anxious and a little mad"})
    print("Analyze Response:", resp.status_code, resp.text)
    
    print("Fetching /insights...")
    resp2 = requests.get("http://127.0.0.1:5000/insights")
    print("Insights Response:", resp2.status_code, resp2.text)
except Exception as e:
    print("Error:", e)
