# trustchain

A layered networking and DevOps project, built step by step to understand how
traffic, identity and access control fit together, from raw JWT signing up to
GitOps and cloud network design.

Three services sit behind each other:

```
Client --HTTPS 443--> reverse-proxy (Nginx) --HTTP--> auth-service (FastAPI, :8000)
                              |                             ^
                              +--HTTP--> api-service (FastAPI, :8002)
                                              |  fetches JWKS
                                              +-------------+
```

| Service | Role |
|---|---|
| **auth-service** | Issues RS256-signed JWTs, publishes the public key at `/.well-known/jwks.json`, supports key rotation |
| **api-service** | Fetches the JWKS itself and verifies tokens independently; `/protected` requires a Bearer token |
| **reverse-proxy** | Terminates TLS and routes by path: `/auth/` to auth-service, `/api/` to api-service |

## What each layer demonstrates

**1. Application: hand-rolled RS256 JWTs (Python/FastAPI)**
No JWT library. Header and payload are JSON-encoded, base64url-encoded and
signed with RSA (PKCS1v15, SHA-256) explicitly, so every step is visible. The
signature is verified *before* the payload is parsed. Tokens carry a `kid`
derived from the public key, and `exp`/`nbf` are enforced.

**2. Containers: Docker Compose**
All three services run together. api-service gets its auth URL from an
environment variable instead of a hardcoded address.

**3. Kubernetes: kind, Helm**
One Helm chart per service. The proxy's configuration comes from a ConfigMap
and its certificate from a Secret.

**4. Network policy: default-deny**
A default-deny ingress policy, with explicit allow rules:
- auth-service accepts traffic from reverse-proxy and api-service
- api-service accepts traffic from reverse-proxy
- reverse-proxy accepts traffic on 443 from anywhere

The enforcement was tested: a connection from an arbitrary pod fails after
default-deny is applied.

**5. GitOps: Argo CD**
All three services are Argo CD Applications that sync from this repository
with auto-sync, prune and self-heal enabled. Two behaviours were demonstrated:
- changing `replicaCount` in git creates a new pod with no manual deploy
- scaling a deployment by hand to 5 replicas is reverted by Argo within seconds

**6. Cloud network design: Terraform (Azure)**
`terraform/` defines a VNet with two subnets (proxy and app), each with a
network security group that mirrors the Kubernetes policies: only 443 from the
internet into the proxy subnet, only the proxy subnet into the app subnet, and
an explicit deny-all. Azure allows all traffic inside a VNet by default, so the
deny rule is what makes the allows meaningful. Applied and verified with
`terraform plan`, `apply` and `az network nsg rule list`.

Defense in depth: NSGs filter between subnets, NetworkPolicies filter between
pods, and api-service verifies the JWT signature itself, so no single layer is
trusted alone.

## Running it

**Docker Compose**
```
docker compose up --build
python test_compose_flow.py
```

**Kubernetes (kind)**
```
kind create cluster --name trustchain
kind load docker-image trustchain-auth-service trustchain-api-service --name trustchain
kubectl apply -f k8s/
```
The TLS secret is created manually (see known gaps). Argo CD is installed from
its stable manifest and the Applications are in `k8s/argocd-*.yaml`.

**Azure**
```
cd terraform
terraform init
terraform plan
terraform apply
terraform destroy
```
Needs an Azure subscription and a git-ignored `terraform.tfvars` containing
`subscription_id`. Resources used here have no cost.

## Bugs found along the way

- The payload was parsed before the signature was verified, so a tampered token crashed the service instead of being rejected.
- Malformed input to `/verify` caused a 500 instead of a clean error.
- A missing exception handler on header decoding in api-service had the same effect.

## Known gaps

- **Egress is unrestricted** in both Kubernetes (policies cover ingress only) and Azure (subnets have default outbound access).
- **Pod-to-pod traffic is plain HTTP.** TLS ends at the proxy. Mutual TLS between services (Linkerd) is planned.
- **`depends_on` only orders startup.** It does not wait for readiness, so api-service can start before auth-service is ready.
- **The private key is baked into the Docker image.** Production would use a secrets manager such as Azure Key Vault.
- **The TLS secret is created by hand** and is not in git, so it must be recreated if the cluster is rebuilt.
- **Terraform builds the network only.** No workloads run in the VNet, and state is kept locally rather than in a remote backend.

## Planned

- Linkerd for mTLS between pods
- Readiness probes and a retry on the JWKS fetch
- NetworkPolicies managed through Argo CD
