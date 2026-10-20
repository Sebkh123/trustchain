import json
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Issue a token through the proxy
issue_req = urllib.request.Request(
    "https://localhost:8443/auth/token",
    data=json.dumps({"subject": "seb"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
token = json.loads(urllib.request.urlopen(issue_req, context=ctx).read())["token"]
print("Got token (truncated for display):", token[:50], "...")

# Immediately verify it through the proxy's /api/protected
verify_req = urllib.request.Request(
    "https://localhost:8443/api/protected",
    headers={"Authorization": f"Bearer {token}"},
)
response = urllib.request.urlopen(verify_req, context=ctx)
print("Protected response:", response.read().decode())