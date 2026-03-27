import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4IiwiZXhwIjoxNzczMTk1MjE0fQ.NWYCfZN4_OJdWGoGlbW9ymnJtiaiC-qEkcNuvMEz_X8",
    "Content-Type": "application/json"
}

data = {
    "question": "什么是五四运动？以markdown格式输出",
    "use_context": True
}

response = requests.post("http://localhost:8000/api/v1/ask", headers=headers, json=data)

print("状态码:", response.status_code)
print("响应头:", response.headers)

try:
    print("JSON 响应:", response.json())
except Exception as e:
    print("JSON 解析错误:", e)