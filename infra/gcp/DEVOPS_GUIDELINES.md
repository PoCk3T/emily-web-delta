# Emily Web Delta & Brazen Core — GCP DevOps Deployment & Maintenance Guidelines

This document outlines the deployment, optimization, and maintenance workflows for the **Emily Web Delta** application and the shared **Brazen Core** microservices on Google Cloud Platform (GCP). It is designed to guide engineering and DevOps through initial setup, greenfield IAM provisioning, VM management, and troubleshooting, capturing critical lessons learned from past deployments to prevent configuration drift.

---

## Table of Contents

1. [GCP Project & Initial Context Verification](#1-gcp-project--initial-context-verification)
   - [A. Two Projects — Do Not Confuse Them](#a-two-projects--do-not-confuse-them)
2. [Infrastructure Setup & Network Security](#2-infrastructure-setup--network-security)
3. [Greenfield IAM Provisioning & Service Accounts Matrix](#3-greenfield-iam-provisioning--service-accounts-matrix)
   - [A. Required Service Accounts & Project-Level Roles](#a-required-service-accounts--project-level-roles)
   - [B. Resource-Level Bindings & SA-to-SA Trusts](#b-resource-level-bindings--sa-to-sa-trusts)
   - [C. Unified Setup & Remediation Commands (Fix-All Script)](#c-unified-setup--remediation-commands-fix-all-script)
4. [Single-VM Host Provisioning & Optimizations (Emily Scanner VM)](#4-single-vm-host-provisioning--optimizations-emily-scanner-vm)
5. [VM Host Codebase Deployment & Production Setup](#5-vm-host-codebase-deployment--production-setup)
6. [Key Architectural Lessons Learned (Operational Gotchas)](#6-key-architectural-lessons-learned-operational-gotchas)
7. [Runbook: Adding URLs to the Monitored Set](#7-runbook-adding-urls-to-the-monitored-set)

---

## 1. GCP Project & Initial Context Verification

### A. Two Projects — Do Not Confuse Them

This document covers **two separate GCP projects**. Running a command against the wrong one fails with a confusing `Required '<permission>' permission` error rather than a clear "wrong project" message, so confirm which half of the document you are in before copying anything.

| Project ID | What lives there | Covered by |
|---|---|---|
| `emily-levin-web-delta-scanner` | **Emily Web Delta scanner.** `emily-scanner-vm` (e2-micro, `us-west1-a`) and `emily-archive-vm` (e2-standard-2, `us-central1-a`). | §2, §4, §5, §7, Lessons 1–7 and 10–16 |
| `ai-agentic-marketing-core` | **Brazen Core microservices.** Cloud Run services, Firestore, BigQuery, Cloud Tasks, Secret Manager. | §3, Lessons 8–9 |

The scanner VM is **not** in `ai-agentic-marketing-core`. Every VM command in §4, §5 and §7 targets `emily-levin-web-delta-scanner`.

### B. Verify Identity and Set Context

```bash
# Verify active authenticated accounts
gcloud auth list

# Set the active account to your corporate deployment identity
gcloud config set account lucas@codimite.com

# Pick ONE of the two projects, per the table above.
# Scanner VM work (§2, §4, §5, §7):
gcloud config set project emily-levin-web-delta-scanner

# Brazen Core / Cloud Run work (§3):
# gcloud config set project ai-agentic-marketing-core

gcloud config list
```

> Every command below passes `--project=` explicitly rather than relying on the
> ambient `gcloud config` value. Keep it that way: an inherited project from an
> unrelated session is the single most common cause of failed runbook steps.

### C. Current Deployment Facts

| Item | Value |
|---|---|
| Scanner public URL | `http://35.212.148.174` |
| Health endpoint | `http://35.212.148.174/api/v1/health` → `{"status":"ok","service":"emily-web-delta"}` |
| Scanner VM / zone | `emily-scanner-vm` / `us-west1-a` |
| Archive VM / zone | `emily-archive-vm` / `us-central1-a` |
| App directory on host | `~/app` |

---

## 2. Infrastructure Setup & Network Security

### A. Core APIs Activation
Enable all necessary Google Cloud APIs before running any deployment script or Terraform plan. **This API set belongs to the Brazen Core project** (`ai-agentic-marketing-core`); the scanner VM only needs `compute.googleapis.com` and `iap.googleapis.com`:
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

> Project: `emily-levin-web-delta-scanner`.

Do not expose the application's infrastructure ports (FastAPI on `8000`, PostgreSQL on `5432`, Redis on `6379`, or MinIO on `9000`/`9001`) to the public internet.

**Defence in depth is mandatory here — the firewall is not sufficient on its own.** Enforce both layers:

1. **Host binding (primary).** Every infrastructure port in `docker-compose.yml` is published to `127.0.0.1` only, e.g. `"127.0.0.1:5432:5432"`. A bare `"5432:5432"` binds `0.0.0.0`, and Docker writes its own `DOCKER` iptables chain that bypasses ordinary host firewalls — leaving the GCP VPC firewall as the *only* control. Postgres, Redis and MinIO all run with default credentials, so a single mistaken ingress rule would expose them outright.
2. **VPC firewall (secondary).** Only ports `80` and `22` are permitted.

```bash
# Allow ingress web traffic to tagged VM instances
gcloud compute firewall-rules create allow-http \
  --project=emily-levin-web-delta-scanner \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

# Allow ingress SSH traffic
gcloud compute firewall-rules create allow-ssh \
  --project=emily-levin-web-delta-scanner \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0
```

Verify the infrastructure ports are actually unreachable from outside:

```bash
IP=$(gcloud compute instances describe emily-scanner-vm \
  --zone=us-west1-a --project=emily-levin-web-delta-scanner \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

for p in 8000 5432 6379 9000 9001; do
  nc -z -w4 "$IP" "$p" 2>/dev/null \
    && echo "port $p: OPEN — EXPOSED, fix immediately" \
    || echo "port $p: closed"
done

# Confirm the host itself is not publishing them on 0.0.0.0
gcloud compute ssh emily-scanner-vm --zone=us-west1-a \
  --project=emily-levin-web-delta-scanner --tunnel-through-iap \
  --command="docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '0\.0\.0\.0:(5432|6379|8000|9000|9001)' && echo 'LEAK: rebind to 127.0.0.1' || echo 'host bindings OK'"
```

---

## 3. Greenfield IAM Provisioning & Service Accounts Matrix

> **Scope: Brazen Core only — project `ai-agentic-marketing-core`.** None of this section applies to the Emily scanner VM, which runs Docker Compose on a single host and uses no service accounts.

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

> **Scope: project `emily-levin-web-delta-scanner`, zone `us-west1-a`.**

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
  --project=emily-levin-web-delta-scanner \
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
  --project=emily-levin-web-delta-scanner \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### C. Host Swap Allocation & Docker Installation
Connect securely via IAP:
```bash
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap
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
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap --command="mkdir -p ~/app"
gcloud compute scp app.tar.gz emily-scanner-vm:~/app.tar.gz --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap

# 3. Extract and clean up
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap --command="tar -xzf ~/app.tar.gz -C ~/app/ && rm ~/app.tar.gz"
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
    gcloud compute ssh emily-scanner-vm --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap
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

### Lesson 10: SQLAlchemy `is None` Silently Disables Filters (Severe — Silent Data Loss)
*   **The Issue:** `select(Url).where(or_(Url.next_check is None, Url.next_check <= now))` looks correct but is not. In Python, `Column is None` is an **identity comparison**, not an overloaded operator, so it evaluates to the constant `False` when the module is imported. SQLAlchemy then folds the `or_()` down to just `next_check <= now`. Every URL created through the API or the web UI starts with `next_check = NULL`, so **the scheduler never selected them and they were never polled — silently, with no error anywhere in the logs.** The seeded URLs worked only because the seeder happens to set `next_check` explicitly, which masked the defect for months. The identical bug in `trigger_notifications_for_url` disabled every tenant-wide (`url_id = NULL`) notification rule.
*   **The Fix:** Always use the SQL-generating methods `.is_(None)` / `.is_not(None)` inside query filters, never the Python `is` operator:
    ```python
    or_(Url.next_check.is_(None), Url.next_check <= now)   # correct
    or_(Url.next_check is None,   Url.next_check <= now)   # BUG: folds to False
    ```
*   **Guardrail:** `backend/tests/test_scheduler_query.py` asserts that a URL with `next_check = NULL` is selected by the due-query and that `.is_(None)` compiles to `IS NULL`. Grep for `is None` inside any `.where(`/`.filter(` before shipping query changes.

### Lesson 11: PDF Sources Need a Dedicated Extraction Path
*   **The Issue:** Many regulated sources (the entire PG&E tariff book, for example) publish canonical documents as PDFs. Feeding PDF bytes into the `readability`/`lxml` HTML pipeline raises `ValueError: All strings must be XML compatible: ... no NULL bytes or control characters`, and the URL is recorded as a permanent hard failure. Headless browsers do not help: `page.content()` cannot return PDF bytes because the browser either renders its internal viewer or triggers a download.
*   **The Fix:** `backend/app/core/pdf_parser.py` detects PDFs (by magic bytes → Content-Type → `.pdf` extension) and extracts text with `pypdf`. `SelfHostedBackend` skips CloakBrowser for PDF URLs, fetches with httpx, and parses in a worker thread (`asyncio.to_thread`) since PDF parsing is CPU-bound and would otherwise block the event loop. Extraction output is whitespace-normalized so the content hash stays stable across identical fetches — otherwise every poll would raise a false "content changed" alert.
*   **Note:** The hyperlink-stripping sanitizer is deliberately **not** applied to PDF text. It rewrites `[text](url)` patterns, which appear legitimately in tariff prose and would corrupt the content.

### Lesson 12: Empty Renders Are More Dangerous Than Failures
*   **The Issue:** JavaScript-only pages (e.g. `https://www.safetyactioncenter.pge.com/terms`, an Ember SPA) return HTTP 200 with an empty DOM shell when fetched without a browser. The pipeline happily stored that as a valid snapshot. Because the empty shell hashes identically on every poll, **the URL appears permanently healthy while being structurally incapable of ever detecting a change.** A hard failure is far preferable: it is visible.
*   **The Fix:** Two layers now exist.
    1. `SelfHostedBackend` rejects any extraction yielding fewer than `MIN_VISIBLE_CHARS` (50) visible, tag-stripped characters and returns an error result instead of a snapshot.
    2. The `js_required` flag on a URL (already in the schema but previously never read) is now honored: when set, the backend refuses to fall back to a non-JS fetch and reports the CloakBrowser failure instead of masking it behind a meaningless 200.
*   **Operational Guidance:** After adding URLs, always check the new rows for suspiciously small snapshots. A monitored page reporting a few hundred bytes is almost certainly a broken extraction, not a small page.
*   **Important caveat:** a small snapshot does **not** by itself mean JavaScript rendering failed. Setting `js_required = True` only helps when the browser fetch is the thing that is broken. If CloakBrowser already succeeded and the snapshot is still tiny, the fault is downstream in extraction — see Lesson 16. Confirm which one you are looking at before "fixing" it, or you will change a flag that has no effect.

### Lesson 13: Idempotent Seeders Must Be Additive, Not Normalizing
*   **The Issue:** The seeder previously recomputed `stagger = 7200 // len(DEFAULT_URLS)` on every run and rewrote `interval_seconds` and `next_check` for **all** seeded URLs. Adding a single URL therefore reshuffled the entire polling schedule and silently discarded any interval an operator had tuned through the UI. It also called `.scalars().all()` three times on a single already-consumed `Result`, so the "manual URLs" bookkeeping always reported zero.
*   **The Fix:** Seeding is now strictly additive. Only URLs absent from the database are inserted, and only the *new* entries are staggered across the window. Pre-existing rows are never rescheduled or retimed — they are only tagged `seeded`. Manually added URLs are counted and left untouched. The query result is materialized exactly once.
*   **Guardrail:** Verified by simulating the real upgrade path (33 existing URLs → add 18): `pre-existing URLs modified: 0`.

### Lesson 14: One Source of Truth for Seed Data
*   **The Issue:** The monitored URL list was duplicated in both `backend/seed_user.py` and the Alembic revision `0002_seed_admin_user_and_default_urls.py`. The two drifted — the migration was missing URLs that had already been added to the seeder. Because the deploy runbook uses `alembic stamp head` (never actually executing `0002`), edits to the migration had no production effect while still appearing authoritative to readers.
*   **The Fix:** `backend/seed_user.py` is the **single source of truth**. The Alembic copy is explicitly frozen and documented as a historical snapshot. `tests/test_seed_urls.py` asserts the migration list remains a strict subset of the live list, so it can never resurrect stale entries on a fresh database.

### Lesson 15: Defaults Must Point at Code Paths That Actually Run
*   **The Issue:** Both the API schema and the web form defaulted new URLs to `backend="firecrawl"`, but the Celery poller only ever selects `backend == "selfhosted"`, and no Firecrawl monitor is provisioned anywhere in the codebase. Every URL added through the UI was therefore created dead-on-arrival. Separately, the frontend called `PATCH /urls/{id}/toggle` and `POST /urls/{id}/check` while the backend only exposed `/enable`, `/disable`, and `/check-now`, so enable/disable and manual re-check were broken from the UI.
*   **The Fix:** `selfhosted` is now the default in both the API (`DEFAULT_BACKEND`) and the form; the Firecrawl option is labelled "(not polled)". The backend exposes `/toggle` and a `/check` alias so the UI contract matches. New URLs also receive `tenant_id` and an immediate `next_check`, making them verifiable on the very next scheduler tick.

### Lesson 16: A Successful Render Can Still Produce a Near-Empty Snapshot (Extractor Collapse)
*   **The Issue:** Nine Stripe pricing URLs were storing snapshots of only 345–451 bytes. Every surface-level indicator was green: CloakBrowser fetched the page successfully, the poll logged `Result status: same`, `check_results` showed **zero errors over 24 hours**, and the snapshots comfortably cleared the `MIN_VISIBLE_CHARS = 50` guard from Lesson 12. The pages were nonetheless being monitored almost blind.

    The cause was **not** JavaScript rendering — the render worked. It was `readability`. On `https://stripe.com/pricing`, a 976 KB rendered document, the two extractors differ by a factor of 43:

    | Extractor | Visible characters recovered |
    |---|---|
    | `readability` | **255** |
    | `trafilatura` | **11,079** |

    readability's scoring heuristics were written for article/blog markup. On component-rendered marketing pages it latches onto one small high-text-density `<div>` (here a single `Copy__body` paragraph) and discards the actual pricing tables. The extracted fragment is *real prose*, not an empty shell, so it passes every emptiness check — and because the fragment is stable, the hash is stable, and **the URL reports "no change" forever regardless of what happens to the prices being monitored.**

    This is strictly worse than Lesson 12's empty render: an empty render is at least detectably empty. A plausible-looking fragment is not.

*   **The Fix:** `extract_content()` in `backend/app/core/html_parser.py` is now a *strategy* rather than a single library call. It runs trafilatura first (with `favor_recall=True` and `include_tables=True`, since pricing tables are exactly what was being lost), accepts that result when it clears 1,000 visible characters, and otherwise cross-checks against readability and keeps whichever recovered more text. Neither engine is allowed to raise: both are wrapped, and if both return nothing the raw HTML is passed through so the Lesson 12 guard makes the final call. Note `trafilatura` was already a declared dependency in `requirements.txt` — it was simply never called.

*   **Second layer — make thin extractions visible.** A hard threshold cannot be raised safely, because some monitored pages are legitimately short. Instead `SelfHostedBackend` now logs a `Thin extraction` warning whenever it recovers fewer than `THIN_EXTRACTION_CHARS` (500) visible characters from an HTML document larger than 20 KB. That ratio — large input, tiny output — is the actual signal, and it is the thing nobody could see before.

*   **Guardrail:** `backend/tests/test_html_parser.py` builds a page shaped like the real failure (decorative shell + short teaser + large body) and asserts the strategy recovers the body copy rather than the teaser.

*   **Diagnostic — is it the render or the extractor?** These are different bugs with different fixes. Distinguish them before acting:
    ```bash
    # Did the browser fetch actually fail? (render problem → js_required=True)
    docker logs --tail 400 app-worker-1 2>&1 | grep -i "cloakbrowser failed"

    # Compare the two extractors on the live page (extractor problem → Lesson 16)
    docker exec app-api-1 python -c "
    import httpx, re
    from readability import readability
    import trafilatura
    h = httpx.get('https://stripe.com/pricing', follow_redirects=True, timeout=45,
                  headers={'User-Agent':'Mozilla/5.0'}).text
    vis = lambda s: len(re.sub(r'\s+',' ', re.sub(r'<[^>]+>',' ', s or '')).strip())
    print('raw html      :', len(h))
    print('readability   :', vis(readability.Document(h).summary()))
    print('trafilatura   :', vis(trafilatura.extract(h)))
    "
    ```
    A large gap between the two numbers means the extractor is collapsing the page, and `js_required` will do nothing.

*   **Audit query — find every URL with this problem:**
    ```sql
    SELECT s.sz, u.name, u.url
    FROM (SELECT DISTINCT ON (url_id) url_id, snapshot_size AS sz
          FROM url_snapshots ORDER BY url_id, created_at DESC) s
    JOIN urls u ON u.id = s.url_id
    WHERE s.sz < 500
    ORDER BY s.sz;
    ```

### Lesson 17: `requirements.txt` Is Not the Deployed Environment
*   **The Issue:** `pypdf>=5.1.0` had been added to `backend/requirements.txt` as part of the Lesson 11 PDF work, and the code imported it correctly, but the running containers were built from an image predating that commit. `pypdf` was therefore **absent from the deployed image for weeks** while appearing present in the repository. `pdf_parser` degrades with `pypdf is not installed; cannot extract PDF content`, so the gap surfaced only as three failing tests — and, because no PDF URL had been seeded yet, it had zero production symptoms. It would have silently broken the first PDF added.
*   **The Fix:** `docker compose build api worker beat` before seeding any URL that needs a dependency newer than the running image. The §7C runbook already says to rebuild; the failure here was rebuilding `api` alone while `worker` and `beat` — the containers that actually poll — kept the stale image.
*   **Verify the deployed environment directly, not the requirements file:**
    ```bash
    for c in app-api-1 app-worker-1 app-beat-1; do
      echo -n "$c: "
      docker exec "$c" python -c 'import pypdf, trafilatura; print("pypdf", pypdf.__version__, "| trafilatura ok")' \
        || echo "MISSING DEPENDENCY"
    done
    ```
*   **Related gotcha — rebuilds are slow and memory-hungry on `e2-micro`.** A full `docker compose build` of all three images takes roughly 20–40 minutes and drives load average above 10. It completes successfully, but SSH becomes unresponsive while it runs; do not interrupt it and assume failure. Confirm with `docker images` (check the `CreatedSince` column) once the host is responsive again.

### Lesson 18: Recreating `api` Breaks the Nginx Upstream Until `frontend` Restarts
*   **The Issue:** `docker compose up -d` recreated `app-api-1`, which received a new IP on the Docker bridge network. The `frontend` container had been running for two months and its nginx worker had cached the previous upstream address at startup. The public site immediately began returning **HTTP 502** on every `/api/v1` route, even though `api` itself was healthy and answering correctly on `127.0.0.1:8000` from the host.
*   **The Fix:** Restart `frontend` whenever `api` is recreated (not merely restarted):
    ```bash
    docker compose restart frontend
    ```
*   **Guardrail:** Never finish a deployment on the internal health check alone — `curl http://localhost:8000/api/v1/health` passing while the public URL is down is exactly the shape of this bug. Always confirm from **outside** the VM:
    ```bash
    curl -s -o /dev/null -w 'public health -> HTTP %{http_code}\n' \
      http://35.212.148.174/api/v1/health
    ```

---

## 7. Runbook: Adding URLs to the Monitored Set

`backend/seed_user.py` is the single source of truth. The seeder is **additive**: it only inserts URLs that do not already exist and never modifies or deletes existing ones, so it is safe to re-run against production.

### A. Edit the Seed List

Append entries to `DEFAULT_URLS` in `backend/seed_user.py`:

```python
{
    "name": "PG&E Electric Rate Schedule E-1 (Residential Services)",
    "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-1.pdf",
    "tags": ["pge", "tariffs", "electric", "residential", "pdf"],
},
```

Field rules:
| Field | Required | Notes |
|---|---|---|
| `name` | yes | Shown in the UI and in alerts. Must be unique. |
| `url` | yes | Must be unique and pass `app/core/url_validator.py`. |
| `tags` | yes | Free-form. Add `pdf` for PDF sources so they can be filtered. |
| `js_required` | no | Set `True` for client-rendered SPAs **and for origins that answer a plain fetch with 403/bot-challenge** (e.g. `marcus.com`). Forces CloakBrowser and disables the non-JS fallback, so a challenge page is never stored as if it were the real content. |
| `backend` | no | Defaults to `selfhosted`, the only backend the poller services. |
| `interval_seconds` | no | Defaults to `7200` (2 h). Must be within `[60, 86400]`. |

Do **not** add the `seeded` tag manually — the seeder applies it.

**Strip tracking query parameters** (`?utm_source=...` and similar) before adding a URL. They do not change the document served, but they become part of the stored URL, so the same page added later without the parameter would be treated as a second, distinct entry.

**Probe every candidate before adding it.** A URL that 403s or returns the wrong content type will otherwise be discovered only after it is live:

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
curl -sSL -o /dev/null -w '%{http_code} %{content_type} %{size_download} -> %{url_effective}\n' \
  -m 45 -A "$UA" "<CANDIDATE_URL>"
```

- `403` → the origin is bot-protected. Confirm CloakBrowser can reach it, then set `js_required: True`.
- `application/pdf` → add the `pdf` tag and make sure the deployed image actually has `pypdf` (Lesson 17).
- A differing `url_effective` → the URL redirects; this is fine, but record it in a comment so the stored URL is not mistaken for a mistake later.

### B. Validate Locally Before Deploying

```bash
cd backend
ruff check .
pytest tests/ -q
```

`tests/test_seed_urls.py` enforces no duplicate URLs/names, validator compliance, `pdf` tagging, and that previously monitored URLs were not accidentally dropped.

### C. Deploy to the VM

Sync the codebase as described in §5A, then:

```bash
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --project=emily-levin-web-delta-scanner --tunnel-through-iap

cd ~/app

# Capture a baseline first, so you can prove the seeder touched nothing.
docker exec app-db-1 psql -U emily -d emily -t -A -F'|' \
  -c "SELECT id,url,interval_seconds,next_check,last_checked,enabled,state FROM urls ORDER BY url;" \
  > /tmp/pre_seed.txt

# Rebuild ALL THREE images. Rebuilding only `api` leaves the poller running
# stale code and missing dependencies — see Lesson 17. Expect 20-40 min on
# the e2-micro; SSH will be sluggish and load average will exceed 10.
docker compose build api worker beat

docker compose run -T --rm api python seed_user.py
docker compose up -d api worker beat

# `api` was recreated, so nginx must re-resolve the upstream — see Lesson 18.
docker compose restart frontend
```

Confirm the pre-existing rows were not modified:

```bash
docker exec app-db-1 psql -U emily -d emily -t -A -F'|' \
  -c "SELECT id,url,interval_seconds,next_check,last_checked,enabled,state FROM urls ORDER BY url;" \
  > /tmp/post_seed.txt

awk -F'|' 'NR==FNR{a[$1]=$0;next} ($1 in a) && a[$1]!=$0 {print "CHANGED: "a[$1]"  ->  "$0}' \
  /tmp/pre_seed.txt /tmp/post_seed.txt
```

Any `CHANGED:` line means a pre-existing URL was altered. Note that the poller runs concurrently with the seeder, so a row whose **`next_check`/`last_checked`/`state` alone** moved was almost certainly updated by a normal poll, not by seeding — check `interval_seconds` and `enabled`, which the seeder must never touch.

The seeder prints an explicit summary — confirm `created (new)` matches the number of URLs you added and that nothing unexpected appears:

```
URL seeding complete:
  defaults defined     : 51
  created (new)        : 18
  already present      : 33
  newly tagged seeded  : 0
  previously seeded    : 33
  manual (untouched)   : 0
```

> Restarting `worker` and `beat` is **mandatory**. Celery loads task code at process start; without a restart the new URLs are polled by the old image and any extraction fixes are not applied.

### D. Verify the New URLs Are Actually Being Checked

New URLs are staggered across a 2-hour window, so allow time before judging. Then:

```bash
# Watch polling activity
docker logs -f app-worker-1 | grep -i "extract\|poll"

# Confirm the rows exist and are scheduled
curl -s "http://localhost/api/v1/urls?per_page=100" \
  | python3 -c "import json,sys; [print(u['last_checked'], u['next_check'], u['url']) for u in json.load(sys.stdin)['data']]"
```

Checklist:
- Every new URL has a non-null `next_check`.
- After its first poll, `last_checked` is populated.
- Snapshot sizes are plausible. **A URL reporting only a few hundred bytes is a broken extraction, not a small page** (see Lessons 12 and 16).
- No `Thin extraction` warnings for the new URLs:
  ```bash
  docker logs --tail 500 app-worker-1 2>&1 | grep -i "thin extraction"
  ```
- PDF URLs log `engine=httpx+pdf`.

Run the Lesson 16 audit query after any batch addition — zero errors in `check_results` does **not** imply the pages are being monitored meaningfully:

```bash
docker exec app-db-1 psql -U emily -d emily -P pager=off -c "
SELECT s.sz, u.name, u.url
FROM (SELECT DISTINCT ON (url_id) url_id, snapshot_size AS sz
      FROM url_snapshots ORDER BY url_id, created_at DESC) s
JOIN urls u ON u.id = s.url_id
WHERE s.sz < 500 ORDER BY s.sz;"
```

### E. Rollback

Seeding only inserts rows; there is nothing to roll back at the infrastructure level. To stop monitoring a URL added by mistake, disable it rather than deleting it (deleting cascades to its snapshots and diff history):

```bash
curl -X PATCH "http://localhost/api/v1/urls/<URL_ID>/toggle" \
  -H 'Content-Type: application/json' -d '{"enabled": false}'
```

Removing the entry from `DEFAULT_URLS` prevents future re-creation but does **not** delete the existing row.
