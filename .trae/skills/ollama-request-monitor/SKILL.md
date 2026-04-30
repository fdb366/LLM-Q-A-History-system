---
name: "ollama-request-monitor"
description: "Monitors and displays full Ollama API requests in a separate terminal window. Invoke when user needs to inspect complete HTTP parameters sent from backend to Ollama server, including headers, JSON body, and messages, without truncation."
---

# Ollama Request Monitor

## Purpose

Backend logging often truncates or omits parts of the JSON payload sent to Ollama. This skill opens a dedicated terminal window to capture and display the **complete, un-truncated HTTP request** in real-time.

## When to Invoke

- User asks to see what parameters the backend sends to Ollama
- User complains that backend logs are incomplete or unclear
- User needs to debug RAG context, prompt construction, or message history
- User wants to verify the exact JSON body sent to the LLM

## How It Works

This skill uses a **local HTTP proxy** (mitmproxy) to intercept traffic between the backend and Ollama:

```
Backend (Python) → Proxy (localhost:11435) → Ollama (localhost:11434)
```

The proxy logs every request body to a dedicated terminal window.

## Prerequisites

Install mitmproxy (cross-platform):

```bash
pip install mitmproxy
```

## Step 1: Create the Proxy Script

Save this as `ollama_proxy.py` in your project root:

```python
# ollama_proxy.py
import json
import sys
from mitmproxy import http
from datetime import datetime

class OllamaMonitor:
    def request(self, flow: http.HTTPFlow) -> None:
        if "api/chat" in flow.request.pretty_url or "api/generate" in flow.request.pretty_url:
            print("\n" + "="*80)
            print(f"[OLLAMA REQUEST] {datetime.now().isoformat()}")
            print("="*80)
            print(f"URL: {flow.request.pretty_url}")
            print(f"Method: {flow.request.method}")
            print(f"Headers:")
            for k, v in flow.request.headers.items():
                print(f"  {k}: {v}")
            print("-"*80)
            print("Body (raw):")
            try:
                body = flow.request.content.decode('utf-8')
                # Pretty print JSON
                parsed = json.loads(body)
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"[Raw bytes]: {flow.request.content}")
                print(f"[Parse error]: {e}")
            print("="*80 + "\n")
            sys.stdout.flush()

addons = [OllamaMonitor()]
```

## Step 2: Start the Proxy (Dedicated Terminal)

### Windows (PowerShell)

Open a **new** PowerShell window and run:

```powershell
# Navigate to project
Set-Location "D:\桌面\LLM_project"

# Start proxy (forwards to Ollama on 11434)
mitmdump -s ollama_proxy.py --mode reverse:http://localhost:11434 --listen-port 11435
```

### macOS / Linux (Terminal)

Open a **new** Terminal window and run:

```bash
cd /path/to/LLM_project
mitmdump -s ollama_proxy.py --mode reverse:http://localhost:11434 --listen-port 11435
```

## Step 3: Configure Backend to Use Proxy

Temporarily modify `backend/app/services/llm_service.py`:

```python
# Change base_url from:
self.base_url = base_url  # http://localhost:11434

# To:
self.base_url = "http://localhost:11435"  # Proxy port
```

Or set environment variable before starting backend:

```bash
# Windows PowerShell
$env:OLLAMA_HOST="http://localhost:11435"

# macOS/Linux
export OLLAMA_HOST=http://localhost:11435
```

## Step 4: Trigger a Request

Ask a question in the frontend. The proxy terminal will display the **complete, un-truncated** request.

## Alternative: Using Python Script (No External Dependencies)

If you cannot install mitmproxy, use this pure-Python proxy:

```python
# simple_ollama_proxy.py
import socket
import threading
import json

TARGET_HOST = "localhost"
TARGET_PORT = 11434
PROXY_PORT = 11435

def handle_client(client_socket):
    try:
        # Read request from backend
        request_data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            request_data += chunk
            if b"\r\n\r\n" in request_data:
                # Check Content-Length for body
                header_end = request_data.index(b"\r\n\r\n") + 4
                headers = request_data[:header_end].decode('utf-8', errors='ignore')
                content_length = 0
                for line in headers.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())
                        break
                if len(request_data) >= header_end + content_length:
                    break

        # Parse and print
        print("\n" + "="*80)
        print("[OLLAMA REQUEST CAPTURED]")
        print("="*80)
        headers = request_data[:request_data.index(b"\r\n\r\n")].decode('utf-8', errors='ignore')
        print(headers)
        print("-"*80)
        body = request_data[request_data.index(b"\r\n\r\n")+4:]
        try:
            parsed = json.loads(body.decode('utf-8'))
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except:
            print(body.decode('utf-8', errors='ignore'))
        print("="*80 + "\n")

        # Forward to Ollama
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((TARGET_HOST, TARGET_PORT))
        target.sendall(request_data)

        # Return response to backend
        while True:
            data = target.recv(4096)
            if not data:
                break
            client_socket.sendall(data)
        target.close()
    except Exception as e:
        print(f"[Proxy Error] {e}")
    finally:
        client_socket.close()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PROXY_PORT))
    server.listen(5)
    print(f"[*] Proxy listening on 0.0.0.0:{PROXY_PORT}")
    print(f"[*] Forwarding to {TARGET_HOST}:{TARGET_PORT}")
    print(f"[*] Ready to capture Ollama requests...")

    while True:
        client, addr = server.accept()
        print(f"[*] Connection from {addr}")
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    start_proxy()
```

Run in a new terminal:

```bash
python simple_ollama_proxy.py
```

## Output Example

```
================================================================================
[OLLAMA REQUEST CAPTURED]
================================================================================
POST /api/chat HTTP/1.1
Host: localhost:11435
Content-Type: application/json
Content-Length: 2847

--------------------------------------------------------------------------------
{
  "model": "deepseek-r1:7b",
  "messages": [
    {
      "role": "user",
      "content": "请根据以下历史资料回答问题。\n资料：\n归途中他又被匈奴抓住..."
    }
  ],
  "stream": true
}
================================================================================
```

## Cleanup

After debugging, revert the backend `base_url` to `http://localhost:11434`.
