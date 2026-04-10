#!/usr/bin/env bash
# connect-doks.sh
# Automates connecting the SRE agent Droplet to a DOKS cluster over private VPC.
#
# Usage (run from your LOCAL machine, not the Droplet):
#   chmod +x scripts/connect-doks.sh
#   ./scripts/connect-doks.sh

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
CLUSTER_NAME=""
DROPLET_IP=""
DROPLET_USER="root"
AGENT_DIR="/opt/sre-agent"
KUBECONFIG_DEST="$AGENT_DIR/.kube/config"
RBAC_FILE="$(dirname "$0")/rbac.yaml"
ENV_FILE=".env"

# ── Helpers ───────────────────────────────────────────────────────────────────
info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*"; }
error() { echo "[ERROR] $*" >&2; exit 1; }

require() {
  for cmd in "$@"; do
    command -v "$cmd" &>/dev/null || error "'$cmd' is required but not installed."
  done
}

# ── Preflight ─────────────────────────────────────────────────────────────────
require doctl kubectl ssh scp

# Prompt for missing values
if [[ -z "$CLUSTER_NAME" ]]; then
  echo ""
  doctl kubernetes cluster list
  echo ""
  read -rp "Enter DOKS cluster name: " CLUSTER_NAME
fi

if [[ -z "$DROPLET_IP" ]]; then
  read -rp "Enter Droplet private IP: " DROPLET_IP
fi

# ── Step 1: Fetch kubeconfig from DOKS ───────────────────────────────────────
info "Fetching kubeconfig for cluster '$CLUSTER_NAME'..."
TMP_KUBECONFIG=$(mktemp)
doctl kubernetes cluster kubeconfig show "$CLUSTER_NAME" > "$TMP_KUBECONFIG"

# ── Step 2: Swap public API server IP for private IP ─────────────────────────
info "Detecting public API server address..."
PUBLIC_SERVER=$(grep "server:" "$TMP_KUBECONFIG" | awk '{print $2}')
info "Public: $PUBLIC_SERVER"

read -rp "Enter private API server IP (e.g. 10.x.x.x): " PRIVATE_IP
PRIVATE_SERVER="https://${PRIVATE_IP}:443"

info "Rewriting kubeconfig to use private endpoint: $PRIVATE_SERVER"
sed -i.bak "s|$PUBLIC_SERVER|$PRIVATE_SERVER|g" "$TMP_KUBECONFIG"
rm -f "${TMP_KUBECONFIG}.bak"

# ── Step 3: Apply RBAC on the cluster ────────────────────────────────────────
info "Applying RBAC (ServiceAccount + ClusterRole) to cluster..."
KUBECONFIG="$TMP_KUBECONFIG" kubectl apply -f "$RBAC_FILE"

# ── Step 4: Generate long-lived token ────────────────────────────────────────
info "Generating ServiceAccount token (1 year)..."
SA_TOKEN=$(KUBECONFIG="$TMP_KUBECONFIG" kubectl create token sre-agent \
  -n kube-system --duration=8760h)

# ── Step 5: Build final kubeconfig using the SA token ────────────────────────
info "Building final kubeconfig with SA token..."
FINAL_KUBECONFIG=$(mktemp)
CLUSTER_CA=$(grep "certificate-authority-data:" "$TMP_KUBECONFIG" | awk '{print $2}')
CLUSTER_NAME_SAFE=$(echo "$CLUSTER_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')

cat > "$FINAL_KUBECONFIG" <<EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: $CLUSTER_CA
    server: $PRIVATE_SERVER
  name: $CLUSTER_NAME_SAFE
contexts:
- context:
    cluster: $CLUSTER_NAME_SAFE
    user: sre-agent
  name: sre-agent@$CLUSTER_NAME_SAFE
current-context: sre-agent@$CLUSTER_NAME_SAFE
users:
- name: sre-agent
  user:
    token: $SA_TOKEN
EOF

# ── Step 6: Copy kubeconfig to Droplet ───────────────────────────────────────
info "Copying kubeconfig to Droplet $DROPLET_IP..."
ssh "$DROPLET_USER@$DROPLET_IP" "mkdir -p $(dirname $KUBECONFIG_DEST)"
scp "$FINAL_KUBECONFIG" "$DROPLET_USER@$DROPLET_IP:$KUBECONFIG_DEST"
ssh "$DROPLET_USER@$DROPLET_IP" "chmod 600 $KUBECONFIG_DEST"

# ── Step 7: Update .env on Droplet ───────────────────────────────────────────
info "Updating KUBECONFIG in $AGENT_DIR/$ENV_FILE on Droplet..."
ssh "$DROPLET_USER@$DROPLET_IP" \
  "sed -i 's|^KUBECONFIG=.*|KUBECONFIG=$KUBECONFIG_DEST|' $AGENT_DIR/$ENV_FILE || \
   echo 'KUBECONFIG=$KUBECONFIG_DEST' >> $AGENT_DIR/$ENV_FILE"

# ── Step 8: Verify ───────────────────────────────────────────────────────────
info "Verifying connectivity from Droplet..."
ssh "$DROPLET_USER@$DROPLET_IP" "KUBECONFIG=$KUBECONFIG_DEST kubectl get nodes"

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -f "$TMP_KUBECONFIG" "$FINAL_KUBECONFIG"

info "Done. SRE agent on $DROPLET_IP is connected to DOKS cluster '$CLUSTER_NAME'."
info "Restart the agent: ssh $DROPLET_USER@$DROPLET_IP 'systemctl restart sre-agent'"
