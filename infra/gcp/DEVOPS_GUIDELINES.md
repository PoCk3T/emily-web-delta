# Emily Web Delta & Brazen Core — GCP DevOps Deployment & Maintenance Guidelines

This document outlines the deployment, optimization, and maintenance workflows for the **Emily Web Delta** application and the shared **Brazen Core** microservices on Google Cloud Platform (GCP). It is designed to guide engineering and DevOps through initial setup, greenfield IAM provisioning, VM management, and troubleshooting, capturing critical lessons learned from past deployments to prevent configuration drift.

---

## Table of Contents

1. [GCP Project & Initial Context Verification](#1-gcp-project--initial-context-verification)
2. [Infrastructure Setup & Network Security](#2-infrastructure-setup--network-security)
3. [Greenfield IAM Provisioning & Service Accounts Matrix](#3-greenfield-iam-provisioning--service-accounts-matrix)
   - [A. Required Service Accounts & Project-Level Roles](#a-required-service-accounts--project-level-roles)
   - [B. Resource-Level Bindings & SA-to-SA Trusts](#b-resource-level-bindings--sa-to-sa-trusts)
   - [C. Unified Setup & Remediation Commands (Fix-All Script)](#c-unified-setup--remediation-commands-fix-all-script)
4. [Single-VM Host Provisioning & Optimizations (Emily Scanner VM)](#4-single-vm-host-provisioning--optimizations-emily-scanner-vm)
5. [VM Host Codebase Deployment & Production Setup](#5-vm-host-codebase-deployment--production-setup)
6. [Key Architectural Lessons Learned (Operational Gotchas)](#6-key-architectural-lessons-learned-operational-gotchas)

---

## 1. GCP Project & Initial Context Verification

Before creating resources, verify the active identity and ensure the target project is correctly activated in the CLI context.

```bash
# Verify active authenticated accounts
gcloud auth list

# Set the active account to your corporate deployment identity
gcloud config set account lucas@codimite.com

# Verify and configure the target project (e.g. emily-levin-web-delta-scanner or ai-agentic-marketing-core)
gcloud config set project ai-agentic-marketing-core
gcloud config list
```

---

## 2. Infrastructure Setup & Network Security

### A. Core APIs Activation
Enable all necessary Google Cloud APIs before running any deployment script or Terraform plan:
```bash
gcloud services enable \
    run.googleapis.com \
    compute.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    servicenetworking.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    cloudtasks.googleapis.com \
    vpcaccess.googleapis.com \
    --project=ai-agentic-marketing-core
```

### B. Network Firewall Configuration (VM Host Only)
Do not expose the application's infrastructure ports (FastAPI on `8000`, PostgreSQL on `5432`, Redis on `6379`, or MinIO on `9000`/`9001`) to the public internet. Keep these strictly bound to Docker's internal default bridge network. 

Only ports `80` (HTTP web access) and `22` (SSH administrative access) should be allowed through ingress rules:

```bash
# Allow ingress web traffic to tagged VM instances
gcloud compute firewall-rules create allow-http \
  --project=ai-agentic-marketing-core \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

# Allow ingress SSH traffic
gcloud compute firewall-rules create allow-ssh \
  --project=ai-agentic-marketing-core \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0
```

---

## 3. Greenfield IAM Provisioning & Service Accounts Matrix

This is the **critical reference checklist** to prevent recurring "missing binding" errors. When standing up a greenfield GCP project, these identities must be manually provisioned or verified first, and all roles applied.

### A. Required Service Accounts & Project-Level Roles

| Service / Workload | Service Account (SA) Email Name | Required Project-Level Roles | Purpose & Triggered Code Path |
|---|---|---|---|
| `api-gateway` | `api-gateway@` | `roles/cloudsql.client`<br>`roles/cloudsql.instanceUser`<br>`roles/datastore.user`<br>`roles/secretmanager.admin` | Connects to DB via asyncpg. Manages onboarding state in Firestore. Creates/modifies/deletes tenant secrets in Secret Manager. |
| `analytics-api` | `analytics-api@` | `roles/bigquery.dataViewer`<br>`roles/bigquery.jobUser` | Submits BigQuery jobs to query performance marts (`fct_ad_performance`). |
| `brand-analyzer` | `brand-analyzer@` | `roles/aiplatform.user`<br>`roles/cloudsql.client`<br>`roles/cloudsql.instanceUser`<br>`roles/datastore.user`<br>`roles/secretmanager.secretAccessor` | Calls Gemini/Vertex AI. Writes analysis to Postgres (`brand_brain`) and updates status in Firestore. |
| `tenant-provisioner` | `tenant-provisioner@` | `roles/cloudsql.client`<br>`roles/cloudsql.instanceUser`<br>`roles/bigquery.admin`<br>`roles/cloudtasks.enqueuer`<br>`roles/datastore.user`<br>`roles/firebaseauth.admin`<br>`roles/iam.serviceAccountTokenCreator`<br>`roles/secretmanager.admin` | Creates schemas in Postgres. Provisions BigQuery datasets. Enqueues tasks. Configures custom claims in Firebase. Generates internal OIDC tokens. |
| `assigntenant` *(blocking function)* | `blocking-fn@` | `roles/datastore.user`<br>`roles/run.invoker` | Reads user-to-tenant mappings in Firestore. Invokes internal provisioning triggers securely. |
| `webhook-receiver` | `webhook-receiver@` | `roles/secretmanager.secretAccessor` | Reads webhook provider signing signatures (Shopify, Meta) to verify payloads. |
| `execution-orchestrator` | `execution-orchestrator@` | `roles/cloudsql.client`<br>`roles/cloudsql.instanceUser`<br>`roles/redis.editor`<br>`roles/datastore.user`<br>`roles/secretmanager.secretAccessor`<br>`roles/iam.serviceAccountTokenCreator` | Connects to Postgres Token Vault. Coordinates distributed locks and rate limits in Redis. |
| **Shared App Services** *(Used by creative-api, agent-proxy, anomaly-alerter, google-ads-mcp)* | `brazen-services@` | `roles/aiplatform.user`<br>`roles/bigquery.dataEditor`<br>`roles/bigquery.user`<br>`roles/cloudtasks.enqueuer`<br>`roles/storage.objectUser`<br>`roles/iam.serviceAccountTokenCreator`<br>`roles/datastore.user`<br>`roles/redis.editor` | Shared runtime identity. Vertex AI generation, ad-platform live reads, GCS media uploads, and temporary Redis lock storage. |
| **Tasks Runner** *(Internal queue runner)* | `tasks-runner@` | *(No project-wide roles)* | OIDC identity embedded within Cloud Tasks. Only needs resource-level invoker permissions on target services. |

---

### B. Resource-Level Bindings & SA-to-SA Trusts

To maintain security boundaries, these resource-level access permissions are mandatory:

1. **Cloud Run Service Invoker Rights (`roles/run.invoker`):**
   - Private backends (`brand-analyzer`, `tenant-provisioner`, `creative-api`, `anomaly-alerter`, `agent-proxy`, `execution-orchestrator`, `google-ads-mcp`) must be deployed with `--no-allow-unauthenticated` and explicitly grant `roles/run.invoker` to:
     - `api-gateway@...` (enables proxying from the gateway router).
     - `tasks-runner@...` (enables Cloud Tasks queues to trigger async callbacks).
     - `blocking-fn@...` (for triggering `tenant-provisioner` during Firebase blocking callbacks).
2. **Cloud Tasks Enqueue Rights (`roles/cloudtasks.enqueuer`):**
   - `brand-analysis-queue` must grant enqueue rights explicitly to `brand-analyzer@...`.
3. **Identity Delegation / Service Account Actor (`roles/iam.serviceAccountUser`):**
   - To dispatch asynchronous tasks carrying the `tasks-runner` identity, both the `brand-analyzer@...` and `tenant-provisioner@...` service accounts **must** be granted `roles/iam.serviceAccountUser` on the target `tasks-runner` service account.
4. **Cloud Storage Blob Signer (`roles/iam.serviceAccountTokenCreator`):**
   - SAs generating GCS dynamic pre-signed media URLs (`brazen-services@` and `api-gateway@`) must be granted Token Creator on **themselves** to permit dynamic cryptographic asset signing in serverless runtimes.

---

### C. Unified Setup & Remediation Commands (Fix-All Script)

Run this copy-pasteable script to stand up a pristine IAM baseline, create any missing service accounts, and apply all project-level role bindings automatically to avoid configuration drift:

```bash
# Set your project ID
export PROJECT_ID="ai-agentic-marketing-core"

# 1. Ensure dedicated Service Accounts exist
gcloud iam service-accounts create api-gateway --display-name="API Gateway Router" --project=$PROJECT_ID || true
gcloud iam service-accounts create analytics-api --display-name="Analytics API" --project=$PROJECT_ID || true
gcloud iam service-accounts create brand-analyzer --display-name="Brand Analyzer Service" --project=$PROJECT_ID || true
gcloud iam service-accounts create tenant-provisioner --display-name="Tenant Provisioner Saga" --project=$PROJECT_ID || true
gcloud iam service-accounts create blocking-fn --display-name="Firebase blocking-fn" --project=$PROJECT_ID || true
gcloud iam service-accounts create webhook-receiver --display-name="Webhook Receiver" --project=$PROJECT_ID || true
gcloud iam service-accounts create execution-orchestrator --display-name="Execution Orchestrator" --project=$PROJECT_ID || true
gcloud iam service-accounts create brazen-services --display-name="Brazen Shared App Services" --project=$PROJECT_ID || true
gcloud iam service-accounts create tasks-runner --display-name="Cloud Tasks Queue Runner" --project=$PROJECT_ID || true

# 2. Apply Project-Level Role Bindings
declare -A BINDINGS=(
  ["api-gateway"]="roles/cloudsql.client roles/cloudsql.instanceUser roles/datastore.user roles/secretmanager.admin"
  ["analytics-api"]="roles/bigquery.dataViewer roles/bigquery.jobUser"
  ["brand-analyzer"]="roles/aiplatform.user roles/cloudsql.client roles/cloudsql.instanceUser roles/datastore.user roles/secretmanager.secretAccessor"
  ["tenant-provisioner"]="roles/cloudsql.client roles/cloudsql.instanceUser roles/bigquery.admin roles/cloudtasks.enqueuer roles/datastore.user roles/firebaseauth.admin roles/iam.serviceAccountTokenCreator roles/secretmanager.admin"
  ["blocking-fn"]="roles/datastore.user roles/run.invoker"
  ["webhook-receiver"]="roles/secretmanager.secretAccessor"
  ["execution-orchestrator"]="roles/cloudsql.client roles/cloudsql.instanceUser roles/redis.editor roles/datastore.user roles/secretmanager.secretAccessor roles/iam.serviceAccountTokenCreator"
  ["brazen-services"]="roles/aiplatform.user roles/bigquery.dataEditor roles/bigquery.user roles/cloudtasks.enqueuer roles/storage.objectUser roles/iam.serviceAccountTokenCreator roles/datastore.user roles/redis.editor"
)

for SA in "${!BINDINGS[@]}"; do
  for ROLE in ${BINDINGS[$SA]}; do
    echo "Binding $ROLE to $SA..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:$SA@$PROJECT_ID.iam.gserviceaccount.com" \
      --role="$ROLE" --quiet
  done
done

# 3. Grant Service Account User to Tasks Runner
gcloud iam service-accounts add-iam-policy-binding tasks-runner@$PROJECT_ID.iam.gserviceaccount.com \
  --member="serviceAccount:brand-analyzer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" --project=$PROJECT_ID --quiet

gcloud iam service-accounts add-iam-policy-binding tasks-runner@$PROJECT_ID.iam.gserviceaccount.com \
  --member="serviceAccount:tenant-provisioner@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" --project=$PROJECT_ID --quiet
```

---

## 4. Single-VM Host Provisioning & Optimizations (Emily Scanner VM)

When deploying to a single VM host (such as `emily-scanner-vm` on `debian-12` minimal), follow these provisioning configurations to guarantee stability.

### A. VM Metadata Key Preparation
Google Cloud VM metadata expects keys formatted as `username:ssh-key`.
```bash
# Generate the key pair locally
ssh-keygen -t ed25519 -f ~/.ssh/emily-vm-key -C "emily" -N ""

# Format public key metadata
echo "emily:$(cat ~/.ssh/emily-vm-key.pub)" > ~/.ssh/gcp_ssh_keys
```

### B. VM Instance Provisioning
Create an `e2-micro` virtual machine with a standard 30GB boot disk and http/ssh tags:
```bash
gcloud compute instances create emily-scanner-vm \
  --project=ai-agentic-marketing-core \
  --zone=us-west1-a \
  --machine-type=e2-micro \
  --network-interface=network-tier=STANDARD,subnet=default \
  --metadata-from-file=ssh-keys=$HOME/.ssh/gcp_ssh_keys \
  --tags=http-server \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard
```

Retrieve the instance's public IP address:
```bash
gcloud compute instances describe emily-scanner-vm \
  --zone=us-west1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### C. Host Swap Allocation & Docker Installation
Connect securely via IAP:
```bash
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap
```

Run these on the remote VM host to configure a **2GB swap file** (absolutely essential on 1GB RAM instances) and install Docker cleanly:
```bash
# 1. Allocate Swap File
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. Configure Docker Official Repositories
sudo apt-get update && sudo apt-get install -y curl ca-certificates rsync
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Install Docker Engine and Compose
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```
*Note: Run `newgrp docker` or log out and back in to apply group privileges.*

---

## 5. VM Host Codebase Deployment & Production Setup

### A. Synchronizing Files
To copy your local repository cleanly and rapidly while excluding massive dependency folders (`node_modules`, `.venv`, `.git`), package your codebase into a temporary tarball locally, upload it over IAP, and extract it on the host:

```bash
# 1. Package the clean codebase locally
tar -czf app.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.venv*' \
  --exclude='.ruff_cache' \
  --exclude='__pycache__' \
  --exclude='frontend/dist' \
  --exclude='.env' \
  backend frontend docker-compose.yml .dockerignore .gitignore

# 2. Create remote dir & securely upload
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap --command="mkdir -p ~/app"
gcloud compute scp app.tar.gz emily-scanner-vm:~/app.tar.gz --zone=us-west1-a --tunnel-through-iap

# 3. Extract and clean up
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap --command="tar -xzf ~/app.tar.gz -C ~/app/ && rm ~/app.tar.gz"
rm app.tar.gz
```

### B. Production Environment Configuration
SSH back into your VM and write default production configurations to `~/app/.env`:
```bash
DATABASE_URL=postgresql+asyncpg://emily:emily@db:5432/emily
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<32_CHARACTER_CRYPTOGRAPHIC_RANDOM_HEX_KEY>
FIRECRAWL_API_KEY=<YOUR_API_KEY>
VITE_API_BASE_URL=/api/v1
```

### C. Database Initialization, Seeding, and Stamps
**Do not run `alembic upgrade head` directly on an empty database.** Create the schemas first via the dedicated python runner, seed the default user, and then stamp Alembic:
```bash
cd ~/app
docker compose up -d db redis
docker compose run --rm api python seed_user.py
docker compose run --rm api alembic stamp head
```

### D. Start and Monitor All Services
```bash
# Start all containers in the background
docker compose up -d --build

# Verify container stability and check logs
docker compose ps
docker logs app-api-1
docker logs app-beat-1

# Verify internal reverse-proxy accessibility
curl http://localhost/api/v1/health
```

---

## 6. Key Architectural Lessons Learned (Operational Gotchas)

### Lesson 1: Resource Constrained VM Host lockups
*   **The Issue:** An `e2-micro` VM provides only 1GB of physical memory. Parallel builds or multiple processes trigger Out-Of-Memory (OOM) locks, freezing the Docker daemon and SSH server.
*   **The Fix:** Always configure a **2GB swap file** on the host. This buffers physical RAM starvation and ensures high-density workload stability.

### Lesson 2: Vite Build-Time vs. Runtime Environment Variables
*   **The Issue:** Vite compiles environment variables statically at *build-time* during the Docker builder stage. Standard Docker Compose runtime variables have zero effect once the static bundle is built.
*   **The Fix:** Inject build-time arguments (`ARG VITE_API_BASE_URL=/api/v1`) explicitly in the client Dockerfile and define them inside the `docker-compose.yml` build block.

### Lesson 3: Volume Mount Ownership & Celery Beat Permissions
*   **The Issue:** Bind-mounting the backend directory (`./backend:/app`) to a host folder owned by the root deployment user causes Celery Beat to fail with `Permission denied` when trying to write its tracking file (`celerybeat-schedule`).
*   **The Fix:** Explicitly redirect the celerybeat schedule file to `/tmp` via the startup command:
    ```yaml
    command: celery -A app.celery_app beat --schedule=/tmp/celerybeat-schedule --loglevel=info
    ```

### Lesson 4: Thread & Worker Footprint Optimization
*   **The Issue:** High worker and thread counts overwhelm thin virtual CPU allocation.
*   **The Fix:** Scale down the container footprints explicitly:
    - Set `--workers 1` for FastAPI's Uvicorn execution command.
    - Set `--concurrency=1` for Celery worker daemons.

### Lesson 5: Proxy / CorpSSH Outbound Restrictions
*   **The Issue:** Corporate networks utilizing certificates or custom ProxyCommands often block outbound SSH on port `22`.
*   **The Fix:** Tunnel all SSH traffic over HTTPS port `443` through Identity-Aware Proxy (IAP):
    ```bash
    gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap
    ```

### Lesson 6: Non-Interactive Executions & TTY Allocation Hangs
*   **The Issue:** Running commands remotely via non-interactive shell scripts defaults to allocating a pseudo-TTY, which hangs indefinitely waiting for input.
*   **The Fix:** Always pass the TTY-disabling flag `-T` (or `--no-TTY`):
    ```bash
    docker compose run -T --rm api python seed_user.py
    ```

### Lesson 7: Stale/Dead Containers & Storage Driver Volume Locks
*   **The Issue:** Aborted deployments can leave containers in a `Dead` state, failing with name conflicts on subsequent starts. Force-removal (`docker rm -f`) fails due to kernel locks in the overlay2 storage driver.
*   **The Fix:** Restart the host VM's Docker service to break filesystem lock contention, then cleanly remove:
    ```bash
    sudo systemctl restart docker
    docker rm -f app-db-1 app-api-1
    ```

### Lesson 8: Cloud Run Microservices & Storage Bucket Environment Variables
*   **The Issue:** Microservices writing files to Google Cloud Storage (such as `creative-api` uploading generated assets) often rely on environmental configuration flags like `BRAND_ASSETS_BUCKET`. If a deployment revision is rolled out without explicitly setting this variable, fallback hardcodings in shared packages (e.g., `os.environ.get("BRAND_ASSETS_BUCKET", "brazen-assets")`) can cause silent failures. The storage client attempts to write to a non-existent bucket (`brazen-assets` instead of `brazen-media-assets-ai-agentic-marketing-core`), causing upstream requests to hang and eventually timing out at the API Gateway level (raising `httpx.ReadTimeout` and returning 500 errors to the client).
*   **The Fix:** Ensure all service deployment configs (Cloud Build files, Terraform definitions, or manual `gcloud run deploy` command setups) explicitly define essential environmental flags like `BRAND_ASSETS_BUCKET`. Avoid using hardcoded local fallback values for external cloud infrastructure names (like buckets or remote databases) in production-bound packages. Instead, force the application to fail fast with a clear initialization error during startup.

### Lesson 9: Missing or Under-Configured `FRONTEND_URL` on `api-gateway` (400 CORS Errors)
*   **The Issue:** If `FRONTEND_URL` is missing or does not explicitly contain all active frontend custom domains (like `https://marketing.upslope.tech`, `https://brazen.marketing.upslope.tech`, etc.), standard CORS preflight `OPTIONS` requests fail with `400 Bad Request` or "Disallowed CORS origin". The gateway falls back to `["http://localhost:3000"]` when `FRONTEND_URL` is omitted, blocking all custom-domain browsers.
*   **The Fix:** Always deploy and update `api-gateway` with `FRONTEND_URL` explicitly configured to include all white-label frontend origins. Since the list contains commas, **always** use custom caret delimiters (`^@^`) in your `gcloud` command to prevent `gcloud` from misinterpreting commas as environment variable separators:
  ```bash
  gcloud run services update api-gateway \
    --region=us-central1 \
    --project=ai-agentic-marketing-core \
    --update-env-vars="^@^FRONTEND_URL=https://marketing.upslope.tech,https://brazen.marketing.upslope.tech,https://goldengate.marketing.upslope.tech,https://redpocket.marketing.upslope.tech,https://app.goldengateads.com,https://app.brazen.ai,https://frontend-723572939533.us-central1.run.app,http://localhost:3000"
  ```
  Ensure all automated deployment scripts preserve and include `FRONTEND_URL`.
