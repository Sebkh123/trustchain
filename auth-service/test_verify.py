from keys import load_private_key
from jwt_tools import issue_token, verify_token

private_key = load_private_key("private_key.pem")
public_key = private_key.public_key()

payload = {"sub": "seb", "iss": "trustchain-auth"}
token = issue_token(private_key, payload)

print("--- verifying genuine token ---")
claims = verify_token(public_key, token)
print("Verified! Claims:", claims)

print()
print("--- corrupting one character and re-verifying ---")
header_b64, payload_b64, signature_b64 = token.split(".")
tampered_payload = payload_b64[:-1] + ("A" if payload_b64[-1] != "A" else "B")
tampered_token = f"{header_b64}.{tampered_payload}.{signature_b64}"

claims = verify_token(public_key, tampered_token)
print("Verified! Claims:", claims)