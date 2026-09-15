import subprocess
import json
import base64

issue = subprocess.run(
    ["curl.exe", "-s", "-X", "POST", "http://127.0.0.1:8000/token",
     "-H", "Content-Type: application/json",
     "-d", json.dumps({"subject": "seb"})],
    capture_output=True, text=True
)
token = json.loads(issue.stdout)["token"]
print("Issued token (truncated):", token[:50], "...")

verify = subprocess.run(
    ["curl.exe", "-s", "-X", "POST", "http://127.0.0.1:8000/verify",
     "-H", "Content-Type: application/json",
     "-d", json.dumps({"token": token})],
    capture_output=True, text=True
)
print("Verify response:", verify.stdout)

header_b64 = token.split(".")[0]
header = base64.urlsafe_b64decode(header_b64 + "==")
print("Decoded header:", header)