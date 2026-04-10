# Connecting SRE Agent to DOKS (Same Subnet)

## Automated (recommended)

Run the setup script from your **local machine** (requires `doctl`, `kubectl`, `ssh`, `scp`):

```bash
chmod +x scripts/connect-doks.sh
./scripts/connect-doks.sh
```

The script will prompt for your cluster name and Droplet private IP, then handle all steps below automatically.

---

## Manual Steps

Since the Droplet and the DOKS cluster share the same VPC/subnet, the agent connects directly to the K8s API server over the private network — no VPN or tunneling required.

## 1. Get the API Server Private IP

```bash
kubectl cluster-info
# Or check the control plane private IP in the DigitalOcean console
```

## 2. Copy kubeconfig to the Droplet

```bash
scp ~/.kube/config root@<droplet-private-ip>:/opt/sre-agent/.kube/config
```

Then edit the copied config on the Droplet — replace the public API server address with the private IP:

```yaml
# Change this:
server: https://123.456.78.90:6443   # public IP

# To this:
server: https://10.x.x.x:6443       # private/VPC IP
```

## 3. Set KUBECONFIG in .env

```bash
KUBECONFIG=/opt/sre-agent/.kube/config
```

The agent reads this in `config.py` — if set, it calls `load_kube_config(config_file=...)`, otherwise falls back to in-cluster config.

## 4. Verify Connectivity from the Droplet

```bash
export KUBECONFIG=/opt/sre-agent/.kube/config
kubectl get nodes
```

If this works, the agent will connect successfully.

---

## Firewall Rule

If the DOKS API server has restricted access, whitelist the Droplet's private IP via the DigitalOcean console or CLI:

```bash
doctl kubernetes cluster update <cluster-id> \
  --restricted-access-ip-whitelist <droplet-private-ip>
```

Or if using `ufw` on a self-managed control plane:

```bash
ufw allow from <droplet-private-ip> to any port 6443
```

---

## RBAC — Least Privilege for the Agent

Do not use the admin kubeconfig in production. Create a dedicated ServiceAccount scoped to only what the agent needs.

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sre-agent
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: sre-agent
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods/eviction"]
    verbs: ["create"]
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["patch"]   # required for cordon (drain_node)
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "patch"]   # required for rollout restart
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: sre-agent
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: sre-agent
subjects:
  - kind: ServiceAccount
    name: sre-agent
    namespace: kube-system
```

Apply it and generate a long-lived token for the Droplet:

```bash
kubectl apply -f rbac.yaml

kubectl create token sre-agent -n kube-system --duration=8760h
```

Use that token in the kubeconfig on the Droplet instead of the admin credentials.

---

## Summary

| Step | What |
|---|---|
| Same subnet | Use private IP in kubeconfig `server:` field |
| Firewall | Whitelist Droplet private IP on port 6443 |
| Auth | Create dedicated ServiceAccount with scoped RBAC |
| Config | Set `KUBECONFIG=/opt/sre-agent/.kube/config` in `.env` |
