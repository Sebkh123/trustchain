# trustchain

A layered networking and DevOps project, built step by step to understand how
traffic, identity and access control fit together, from raw JWT signing up to
GitOps and cloud network design.

```
Client --HTTPS 443--> reverse-proxy (Nginx) --HTTP--> auth-service (FastAPI, :8000)
                              |                             ^
                              +--HTTP--> api-service (FastAPI, :8002)
                                              |  fetches JWKS
                                              +-------------+
```

| Service | Role |
|---|---|
| **auth-service** | Issues RS256-signed JWTs (5-minute lifetime), publishes the public key at `/.well-known/jwks.json`, supports key rotation |
| **api-service** | Fetches the JWKS itself and verifies tokens independently; `/protected` requires a Bearer token |
| **reverse-proxy** | Terminates TLS and routes by path: `/auth/` to auth-service, `/api/` to api-service |

## What each layer demonstrates

**1. Application: hand-rolled RS256 JWTs (Python/FastAPI)**
No JWT library. Header and payload are JSON-encoded, base64url-encoded and
signed with RSA (PKCS1v15, SHA-256) explicitly, so every step is visible. The
signature is verified *before* the payload is parsed. Tokens carry a `kid`
derived from the public key, which lets api-service pick the right key from the
JWKS, and `exp`/`nbf` are enforced.

**2. Containers: Docker Compose**
All three services run together. Only the reverse proxy publishes a port on the
host; the services are reachable only through it. api-service takes its auth URL
from an environment variable instead of a hardcoded address.

**3. Kubernetes: kind and Helm**
One Helm chart per service. The proxy's configuration comes from a ConfigMap
and its certificate from a Secret.

**4. Network policy: default-deny**
A default-deny ingress policy with explicit allow rules:
- auth-service accepts traffic from reverse-proxy and api-service
- api-service accepts traffic from reverse-proxy
- reverse-proxy accepts traffic on 443 from anywhere

Enforcement was tested: a connection from an arbitrary pod fails once
default-deny is applied.

**5. GitOps: Argo CD**
All three services are Argo CD Applications that sync from this repository with
auto-sync, prune and self-heal. Two behaviours were demonstrated:
- changing `replicaCount` in git created a new pod with no manual deploy
- scaling a deployment by hand to 5 replicas was reverted by Argo within seconds

**6. Cloud network design: Terraform (Azure)**
`terraform/` defines a VNet with two subnets (proxy and app). Each has a network
security group mirroring the Kubernetes policies: only 443 from the internet
into the proxy subnet, only the proxy subnet into the app subnet, and an
explicit deny-all. Azure allows all traffic inside a VNet by default, so the
deny rule is what makes the allow rules meaningful. Applied and verified with
`terraform plan`, `apply` and `az network nsg rule list`.

Defense in depth: NSGs filter between subnets, NetworkPolicies filter between
pods, and api-service verifies the JWT signature itself, so no single layer is
trusted alone.

## Running it

The same test script works against either environment, because it only talks to
`https://localhost:8443`. Run one environment at a time, since both use that port.

### Docker Compose

```
docker compose up --build
python test_flow.py
docker compose down
```

### Kubernetes (kind)

```
kind create cluster --name trustchain
kind load docker-image trustchain-auth-service trustchain-api-service --name trustchain

# Self-signed certificate for the proxy (git-ignored), then the TLS secret
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=localhost" \
  -keyout reverse-proxy/certs/key.pem -out reverse-proxy/certs/cert.pem
kubectl create secret tls reverse-proxy-tls \
  --cert=reverse-proxy/certs/cert.pem --key=reverse-proxy/certs/key.pem

# Argo CD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Network policies and the three Argo CD Applications
kubectl apply -f k8s/00-default-deny.yaml -f k8s/01-allow-rules.yaml
kubectl apply -f k8s/argocd-auth-service-app.yaml \
              -f