import requests
import json

url = "http://localhost:8000/api/v1/ask"
payload = {
    "question": "秦始皇统一六国的时间",
    "use_context": True
}

response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
print("Response:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))