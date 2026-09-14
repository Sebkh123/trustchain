from keys import load_private_key
from jwt_tools import issue_token

private_key = load_private_key("private_key.pem")

payload = {"sub": "seb", "iss": "trustchain-auth"}
token = issue_token(private_key, payload)

print(token)