import time
from keys import load_private_key
from jwt_tools import issue_token, verify_token, TokenError

private_key = load_private_key("private_key.pem")
public_key = private_key.public_key()

print("--- 1. fresh token, verified immediately ---")
token = issue_token(private_key, {"sub": "seb"})
print(verify_token(public_key, token))

print()
print("--- 2. token with a 2-second TTL, verified 1 second later (should pass) ---")
token = issue_token(private_key, {"sub": "seb"}, ttl_seconds=2)
time.sleep(1)
print(verify_token(public_key, token))

print()
print("--- 3. token with a 1-second TTL, verified 2 seconds later (should fail) ---")
token = issue_token(private_key, {"sub": "seb"}, ttl_seconds=1)
time.sleep(2)
try:
    print(verify_token(public_key, token))
except TokenError as e:
    print("Correctly rejected:", e)