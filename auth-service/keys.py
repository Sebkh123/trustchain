from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


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