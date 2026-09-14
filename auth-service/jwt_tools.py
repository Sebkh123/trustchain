import base64
import json
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from cryptography.exceptions import InvalidSignature



def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def issue_token(private_key: rsa.RSAPrivateKey, payload: dict, ttl_seconds: int = 300) -> str:
    header = {"alg": "RS256", "typ": "JWT"}

    now = int(time.time())
    full_payload = {
        **payload,
        "iat": now,
        "nbf": now,
        "exp": now + ttl_seconds,
    }

    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64url_encode(json.dumps(full_payload, separators=(",", ":")).encode())

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    signature = private_key.sign(
        signing_input,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signature_b64 = b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"

def b64url_decode(data: str) -> bytes:
    padding_needed = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding_needed)


class TokenError(Exception):
    """Raised when a token fails verification, with a human-readable reason."""


def verify_token(public_key, token: str) -> dict:
    header_b64, payload_b64, signature_b64 = token.split(".")

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = b64url_decode(signature_b64)

    try:
        public_key.verify(
            signature,
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature:
        raise TokenError("signature verification failed: token was altered or forged")

    payload = json.loads(b64url_decode(payload_b64))
    now = int(time.time())

    if payload.get("exp", 0) < now:
        raise TokenError("token has expired")
    if payload.get("nbf", 0) > now:
        raise TokenError("token is not yet valid")

    return payload