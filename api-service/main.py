from fastapi import FastAPI, HTTPException, Header

from jwks_client import fetch_jwks, jwk_to_public_key
from jwt_verifier import verify_token, TokenError

app = FastAPI(title="trustchain api-service")

AUTH_SERVICE_JWKS_URL = "http://127.0.0.1:8000/.well-known/jwks.json"

# Fetch once at startup, cached for the process lifetime.
_jwks = fetch_jwks(AUTH_SERVICE_JWKS_URL)
_public_keys_by_kid = {
    jwk["kid"]: jwk_to_public_key(jwk) for jwk in _jwks["keys"]
}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/protected")
def protected(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ")

    # We need the token's kid to know which key to check it against.
    
    import base64, json
    try:
        header_b64 = token.split(".")[0]
        padding_needed = "=" * (-len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64 + padding_needed))
        kid = header.get("kid")
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail= "malformed token: could not read headers")

    public_key = _public_keys_by_kid.get(kid)
    if public_key is None:
        raise HTTPException(status_code=401, detail=f"unknown signing key: {kid}")

    try:
        claims = verify_token(public_key, token)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return {"message": f"Hello, {claims.get('sub')}. You accessed a protected resource.", "claims": claims}