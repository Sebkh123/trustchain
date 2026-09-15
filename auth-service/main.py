from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from keys import load_private_key
from jwt_tools import issue_token, verify_token, TokenError
from keys import load_private_key, key_id, public_key_to_jwk

app = FastAPI(title="trustchain auth service")

private_key = load_private_key("private_key.pem")
public_key = private_key.public_key()
kid = key_id(public_key)


class TokenRequest(BaseModel):
    subject: str


class VerifyRequest(BaseModel):
    token: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/token")
def token(request: TokenRequest):
    jwt = issue_token(private_key, {"sub": request.subject})
    return {"token": jwt}


@app.post("/verify")
def verify(request: VerifyRequest):
    try:
        claims = verify_token(public_key, request.token)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"valid": True, "claims": claims}


@app.get("/.well-known/jwks.json")
def jwks():
    return {"keys": [public_key_to_jwk(public_key, kid)]}    