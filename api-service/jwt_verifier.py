import base64
import json
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class TokenError(Exception):
    """Raised when a token fails verification, with a human-readable reason."""


def _b64url_decode(data: str) -> bytes:
    padding_needed = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding_needed)


def verify_token(public_key: rsa.RSAPublicKey, token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise TokenError("malformed token: expected three dot-separated segments")

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    try:
        signature = _b64url_decode(signature_b64)
    except (ValueError, TypeError):
        raise TokenError("malformed token: signature is not valid base64url")

    try:
        public_key.verify(
            signature,
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except InvalidSignature:
        raise TokenError("signature verification failed: token was altered or forged")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, TypeError, json.JSONDecodeError):
        raise TokenError("malformed token: payload is not valid base64url JSON")

    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise TokenError("token has expired")
    if payload.get("nbf", 0) > now:
        raise TokenError("token is not yet valid")

    return payload