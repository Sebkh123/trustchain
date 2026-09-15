from jwks_client import fetch_jwks, jwk_to_public_key
import httpx
import json

jwks = fetch_jwks("http://127.0.0.1:8000/.well-known/jwks.json")
jwk = jwks["keys"][0]
public_key = jwk_to_public_key(jwk)
print("Reconstructed public key, size:", public_key.key_size)

# Get a real token from the auth service
issue = httpx.post(
    "http://127.0.0.1:8000/token",
    json={"subject": "seb"},
)
token = issue.json()["token"]
print("Got token:", token[:50], "...")

# Verify it ourselves, using ONLY the reconstructed key — no import from auth-service's code
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

header_b64, payload_b64, signature_b64 = token.split(".")
signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

import base64
def b64url_decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

signature = b64url_decode(signature_b64)

try:
    public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    print("VERIFIED using the key fetched over HTTP, independently of auth-service's code")
except InvalidSignature:
    print("FAILED")