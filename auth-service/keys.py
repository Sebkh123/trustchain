from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import hashlib
import base64

def generate_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def save_private_key(private_key: rsa.RSAPrivateKey, path: str) -> None:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(path, "wb") as f:
        f.write(pem)


def save_public_key(public_key: rsa.RSAPublicKey, path: str) -> None:
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(path, "wb") as f:
        f.write(pem)


def key_id(public_key: rsa.RSAPublicKey) -> str:
    """A short, deterministic identifier for a key, derived from its public bytes."""
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return hashlib.sha256(public_bytes).hexdigest()[:12]    


def _b64url_uint(value: int) -> str:
    """Base64url-encode an integer as raw big-endian bytes, no padding."""
    byte_length = (value.bit_length() + 7) // 8
    raw = value.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def public_key_to_jwk(public_key: rsa.RSAPublicKey, kid: str) -> dict:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": _b64url_uint(numbers.n),
        "e": _b64url_uint(numbers.e),
    }

def load_private_key(path: str) -> rsa.RSAPrivateKey:
    with open(path, "rb") as f:
        pem_data = f.read()
    return serialization.load_pem_private_key(pem_data, password=None)


if __name__ == "__main__":
    private_key = generate_key()
    public_key = private_key.public_key()

    numbers = public_key.public_numbers()
    print("Modulus (n):", numbers.n)
    print("Exponent (e):", numbers.e)

    save_private_key(private_key, "private_key.pem")
    save_public_key(public_key, "public_key.pem")
    print("Keys written to private_key.pem and public_key.pem")