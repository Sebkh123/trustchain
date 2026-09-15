import base64

import httpx
from cryptography.hazmat.primitives.asymmetric import rsa


def _b64url_decode_uint(value: str) -> int:
    padding_needed = "=" * (-len(value) % 4)
    raw_bytes = base64.urlsafe_b64decode(value + padding_needed)
    return int.from_bytes(raw_bytes, byteorder="big")


def fetch_jwks(jwks_url: str) -> dict:
    response = httpx.get(jwks_url)
    response.raise_for_status()
    return response.json()


def jwk_to_public_key(jwk: dict) -> rsa.RSAPublicKey:
    n = _b64url_decode_uint(jwk["n"])
    e = _b64url_decode_uint(jwk["e"])
    public_numbers = rsa.RSAPublicNumbers(e=e, n=n)
    return public_numbers.public_key()