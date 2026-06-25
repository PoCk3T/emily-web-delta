# Emily Web Delta — GCP DevOps Deployment & Maintenance Guidelines

This document outlines the deployment, optimization, and maintenance workflows for the **Emily Web Delta** application on Google Cloud Platform (GCP). It is designed to guide a DevOps engineer through initial setup, troubleshooting, and continuous operations, capturing key architectural decisions and critical "lessons learned" from past deployments.

---

## 1. Initial GCP Account & Context Verification

Before creating resources, verify the active identity and ensure the target project is correctly activated in the CLI context.

```bash
# Verify active authenticated accounts
gcloud auth list

# Set the active account to your corporate deployment identity
gcloud config set account lucas@codimite.com

# Verify and configure the target project
gcloud config set project emily-levin-web-delta-scanner
gcloud config list
```

---

## 2. Infrastructure Setup & Network Security

### A. Core Services Activation
Activate the Compute Engine API:
```bash
gcloud services enable compute.googleapis.com
```

### B. Network Firewall Configuration
Do not expose the application's infrastructure ports (FastAPI on `8000`, PostgreSQL on `5432`, Redis on `6379`, or MinIO on `9000`/`9001`) to the public internet. Keep these strictly bound to Docker's internal default bridge network. 

Only ports `80` (HTTP web access) and `22` (SSH administrative access) should be allowed through ingress rules:

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

# Allow ingress SSH traffic (acts as a baseline fallback)
gcloud compute firewall-rules create allow-ssh \
  --project=emily-levin-web-delta-scanner \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0
```

---

## 3. VM Provisioning & Administrative Access

### A. VM Metadata Key Preparation
Google Cloud VM metadata expects keys formatted as `username:ssh-key`. ed25519 is preferred over RSA for security and speed.

```bash
# Generate the key pair locally
ssh-keygen -t ed25519 -f ~/.ssh/emily-vm-key -C "emily" -N ""

# Format public key metadata
echo "emily:$(cat ~/.ssh/emily-vm-key.pub)" > ~/.ssh/gcp_ssh_keys
```

### B. VM Instance Provisioning
Create an `e2-micro` virtual machine. Use a standard `debian-12` image family, attaching a 30GB boot disk.

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
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

## 4. Key Architectural Lessons Learned (Pitfalls Avoided)

Deploying and maintaining high-density workloads on shared-resource instances (like `e2-micro` with 1GB RAM) requires strict optimization. Review these guidelines to prevent repeating common deployment errors:

### Lesson 1: Resource Constrained Environments & Swap Allocation
*   **The Issue:** An `e2-micro` VM provides only 1GB of physical memory. Spawning parallel Docker image builds, multi-worker FastAPI instances, and Celery worker threads quickly starves the system, triggering kernel Out-Of-Memory (OOM) lockups and making the Docker daemon unresponsive.
*   **The Fix:** Configure a **2GB swap file** immediately on the Debian minimal host. This adds a critical memory buffer, keeping the OS and Docker daemon highly stable.

### Lesson 2: Vite Build-Time vs. Runtime Environment Variables
*   **The Issue:** Vite compiles environments statically at *build-time* inside the Docker builder stage. Standard Docker Compose runtime `environment` variables injected into the container have zero effect after compilation. If no build argument is supplied during compilation, the React client defaults to `http://localhost:8000/api/v1`. This forces client browsers to send API queries to their local machines, causing CORS loopback blocking (`net::ERR_FAILED`).
*   **The Fix:** 
    1. Default the client-side AXIOS base URL fallback to `/api/v1` (relative path) rather than `localhost`.
    2. Define build-time arguments (`ARG VITE_API_BASE_URL=/api/v1`) in the frontend Dockerfile.
    3. Configure `docker-compose.yml` to pass build arguments explicitly:
       ```yaml
       frontend:
         build:
           context: ./frontend
           dockerfile: Dockerfile
           args:
             - VITE_API_BASE_URL=/api/v1
       ```

### Lesson 3: Volume Mount Ownership & Celery Beat Permissions
*   **The Issue:** The celery beat process runs inside the backend container under a non-root user account (`emily`). If the backend source directory is bind-mounted (`./backend:/app`) to a host folder owned by the VM host deployment user, celery beat fails to write its schedule tracking file (`celerybeat-schedule`) to `/app/`, raising `_gdbm.error: [Errno 13] Permission denied` and crashing in a loop.
*   **The Fix:** Explicitly redirect the celery beat schedule tracking file to `/tmp` (fully writeable by any container user) via the command flag:
    ```yaml
    command: celery -A app.celery_app beat --schedule=/tmp/celerybeat-schedule --loglevel=info
    ```

### Lesson 4: Thread & Worker Footprint Optimization
*   **The Issue:** High default thread counts overwhelm thin virtual CPU allocation. Spawning 4 Uvicorn workers and 4 Celery worker processes creates high thread-context switching, starving other services like Redis or Postgres.
*   **The Fix:** Scale down the container process footprint to maintain low overhead:
    - Set `--workers 1` for the FastAPI Uvicorn execution command.
    - Set `--concurrency=1` for the Celery worker process daemon.

### Lesson 5: Proxy / CorpSSH Outbound Restrictions
*   **The Issue:** In corporate networks utilizing security certificates, ProxyCommands, or strict egress controls, standard outbound SSH on port `22` can hang or get blocked with authentication failures.
*   **The Fix:** Tunnel all SSH-based commands and file transfers over HTTPS port `443` through Google Cloud's Identity-Aware Proxy (IAP). This bypasses port `22` restrictions:
    ```bash
    gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap
    ```

### Lesson 6: Non-Interactive Executions & TTY Allocation Hangs
*   **The Issue:** Running helper containers (like `docker compose run`) from remote non-interactive shell scripts defaults to allocating a pseudo-TTY. Without interactive input, the process hangs indefinitely waiting for standard input.
*   **The Fix:** Always pass the TTY-disabling flag `-T` (or `--no-TTY`) when running helper scripts remotely:
    ```bash
    docker compose run -T --rm api python seed_user.py
    ```

### Lesson 7: Stale/Dead Containers & Storage Driver Volume Locks
*   **The Issue:** Aborted or interrupted deployments can leave containers in a `Dead` state. Subsequent runs will conflict on container names (`Conflict. The container name "/app-api-1" is already in use...`). Normal force-removal (`docker rm -f`) may hang or fail with `removal is already in progress` due to kernel filesystem locks in the overlay2 storage driver.
*   **The Fix:** Restart the host VM's Docker service to break filesystem and lock contention, then cleanly remove the stale containers:
    ```bash
    sudo systemctl restart docker
    docker rm -f app-db-1 app-api-run-a03e2cda5c79
    ```

---

## 5. Host Setup & Docker Installation

SSH into your VM using the IAP tunnel to perform these initial provisioning steps:

```bash
# Connect securely via IAP
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap
```

### A. Host Swap Allocation
Run the following commands on the remote VM to configure the 2GB swap space:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### B. Docker Engine & Docker Compose Installation
Install Docker using Debian's secure `/etc/apt/keyrings` keyring format:

```bash
# Update indexes and install utility packages
sudo apt-get update && sudo apt-get install -y curl ca-certificates rsync

# Configure Docker's official keyring and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Grant active user permissions to execute Docker commands
sudo usermod -aG docker $USER
```

*Note: Log out and log back in or execute `newgrp docker` to apply the group membership updates.*

---

## 6. Codebase Deployment & Production Environment Setup

### A. Synchronizing Files
To copy your local repository (including `backend`, `frontend`, and orchestration configs) cleanly and rapidly while excluding massive dependency folders (like `.git`, `node_modules`, virtual envs, or caches), package your codebase into a temporary compressed tarball locally, upload it over IAP, and extract it on the host:

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

# 2. Create the remote directory
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap --command="mkdir -p ~/app"

# 3. Securely upload the bundle over IAP
gcloud compute scp app.tar.gz emily-scanner-vm:~/app.tar.gz --zone=us-west1-a --tunnel-through-iap

# 4. Extract and clean up the bundle on the host VM
gcloud compute ssh emily-scanner-vm --zone=us-west1-a --tunnel-through-iap --command="tar -xzf ~/app.tar.gz -C ~/app/ && rm ~/app.tar.gz"

# 5. Remove the local temporary tarball
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

Generate a secure production `SECRET_KEY` using:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## 7. Database Initialization, Seeding, and Stamps

**Do not run `alembic upgrade head` directly on an empty Postgres database.** The migration files rely on database schemas and structures created dynamically by SQLAlchemy models.

Execute initial schemas creation and user/monitored URLs seeding via the dedicated Python runner inside your container first, and then stamp the migration version:

```bash
# 1. Bring up the PostgreSQL and Redis containers first
cd ~/app
docker compose up -d db redis

# 2. Verify PostgreSQL has initialized and is healthy
docker inspect --format='{{json .State.Health}}' app-db-1

# 3. Create all tables and seed the database with seed_user.py
docker compose run --rm api python seed_user.py

# 4. Stamp the database schema to synchronize with Alembic migrations
docker compose run --rm api alembic stamp head
```

---

## 8. Run, Build, and Health Monitoring

### A. Start All Services
```bash
cd ~/app
docker compose up -d --build
```

### B. Health Verification
Verify that all 7 containers are fully running and that no processes are looping or restarting:

```bash
# Inspect container states
docker compose ps

# Check the API logs for stable initialization
docker logs app-api-1

# Check the Celery Beat scheduler logs
docker logs app-beat-1

# Check Nginx access and proxy logs
docker logs app-frontend-1
```

Verify application accessibility by hitting the health endpoints from your host terminal:
```bash
# Verify base page serves the React static bundle
curl -I http://<VM_PUBLIC_IP>

# Verify Nginx reverse-proxies the FastAPI server internally over Docker's bridge network
curl http://<VM_PUBLIC_IP>/api/v1/health
```
