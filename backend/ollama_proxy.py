# -*- coding: utf-8 -*-
"""
Ollama 请求监控代理
拦截后端 → Ollama 的请求，在独立终端显示完整参数
"""

import socket
import select
import threading
import json
import sys
from datetime import datetime

TARGET_HOST = "localhost"
TARGET_PORT = 11434
PROXY_PORT = 11435


def log_request(data: bytes):
    """打印请求到控制台"""
    try:
        decoded = data.decode('utf-8', errors='ignore')
        if b'\r\n\r\n' in data:
            header_end = data.index(b'\r\n\r\n')
            headers = decoded[:header_end]
            body = data[header_end + 4:]

            if body:
                print("\n" + "=" * 80, flush=True)
                print(f"[OLLAMA REQUEST] {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}", flush=True)
                print("=" * 80, flush=True)
                print(headers, flush=True)
                print("-" * 80, flush=True)
                print("Body:", flush=True)
                try:
                    parsed = json.loads(body.decode('utf-8'))
                    print(json.dumps(parsed, ensure_ascii=False, indent=2), flush=True)
                except Exception:
                    print(body.decode('utf-8', errors='ignore'), flush=True)
                print("=" * 80 + "\n", flush=True)
    except Exception as e:
        print(f"[Log Error] {e}", flush=True)


def forward(src: socket.socket, dst: socket.socket, direction: str):
    """转发数据"""
    try:
        data = src.recv(4096)
        if data:
            if direction == "request":
                log_request(data)
            dst.sendall(data)
            return True
        return False
    except Exception:
        return False


def handle_client(client: socket.socket, addr):
    """处理单个连接 - 双向转发"""
    target = None
    try:
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((TARGET_HOST, TARGET_PORT))

        client.setblocking(False)
        target.setblocking(False)

        while True:
            r, _, _ = select.select([client, target], [], [], 1.0)

            if client in r:
                data = client.recv(4096)
                if not data:
                    break
                log_request(data)
                target.sendall(data)

            if target in r:
                data = target.recv(4096)
                if not data:
                    break
                client.sendall(data)

    except Exception as e:
        print(f"[Error] {e}", flush=True)
    finally:
        if target:
            target.close()
        client.close()


def start_proxy():
    """启动代理服务器"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PROXY_PORT))
    server.listen(5)

    print("=" * 80, flush=True)
    print("[Ollama Request Monitor]", flush=True)
    print("=" * 80, flush=True)
    print(f"Proxy:  http://localhost:{PROXY_PORT}", flush=True)
    print(f"Target: http://localhost:{TARGET_PORT}", flush=True)
    print("=" * 80, flush=True)
    print("Waiting for requests...\n", flush=True)

    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client, addr),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n[Shutdown] Proxy stopped.", flush=True)
    finally:
        server.close()


if __name__ == "__main__":
    start_proxy()
