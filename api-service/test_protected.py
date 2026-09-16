import httpx

# Get a token from auth-service
issue = httpx.post("http://127.0.0.1:8000/token", json={"subject": "seb"})
token = issue.json()["token"]
print("Got token from auth-service")

# Use it against api-service's protected endpoint
response = httpx.get(
    "http://127.0.0.1:8002/protected",
    headers={"Authorization": f"Bearer {token}"},
)
print("Status:", response.status_code)
print("Response:", response.json())

# Now try with no token at all
response = httpx.get("http://127.0.0.1:8002/protected")
print()
print("No auth header - status:", response.status_code)
print("Response:", response.json())

# Now try with a garbage token
response = httpx.get(
    "http://127.0.0.1:8002/protected",
    headers={"Authorization": "Bearer garbage.not.valid"},
)
print()
print("Garbage token - status:", response.status_code)
print("Response:", response.json())