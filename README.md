# Emily Web Delta

A web-based platform for monitoring configurable URLs, detecting content changes, computing meaningful deltas, and providing a rich UI for browsing diffs and receiving alerts.

**Core architectural decision: Firecrawl Monitoring API as the primary backend**, with a self-hosted fallback for users who cannot or will not use Firecrawl.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)
- [Infrastructure as Code](#infrastructure-as-code)
- [CI/CD](#cicd)
- [Contributing](#contributing)

## Quick Start

The fastest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-org/emily-web-delta.git
cd emily-web-delta

# Set required environment variables
export FIRECRAWL_API_KEY=your-firecrawl-api-key

# Start all services
docker compose up --build

# The API is available at http://localhost:8000
# The frontend is available at http://localhost:80
# The MinIO console is available at http://localhost:9001
# The PostgreSQL port is available at localhost:5432
# The Redis port is available at localhost:6379
```

Services will start in this order:
- `db` — PostgreSQL 16 (health-checked)
- `redis` — Redis 7 (cache + Celery broker)
- `api` — FastAPI backend on port 8000
- `worker` — Celery worker for self-hosted fallback polling
- `beat` — Celery Beat scheduler
- `frontend` — Nginx serving React build on port 80
- `minio` — MinIO object storage on ports 9000/9001

## Development Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Node.js 20+ (for frontend development)

### Backend

```bash
cd backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run linter
ruff check app/ tests/

# Run tests
pytest tests/ -v
```

### Frontend

```bash
cd frontend

# Install dependencies
npm ci

# Start development server
npm run dev

# Build for production
npm run build
```

### Full Development Environment

```bash
# Start all services (including worker, beat, db, redis, minio)
docker compose up

# Run in detached mode
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Rebuild all images
docker compose up --build
```

## Architecture Overview

Emily Web Delta uses a multi-service architecture:

```
                    +---------------------+
                    |   Cloudflare (DNS)  |
                    |   WAF + CDN         |
                    +----------+----------+
                               |
                    +----------v----------+
                    |  Cloud Run Service  |
                    |  (api + frontend)   |
                    |  Auto-scale 0-N     |
                    +----------+----------+
                               |
          +--------------------+--------------------+
          |                     |                   |
          v                     v                   v
    +-----------+       +-------------+    +---------------+
    |  Cloud    |       |  Cloud      |    |  Cloud Storage|
    |  SQL for  |       |  Memorystore|    |  (snapshot    |
    |  PostgreSQL|      |  Redis      |    |   raw HTML)   |
    +-----------+       +-------------+    +---------------+
```

### Services

| Service | Description | Port |
|---------|-------------|------|
| `api` | FastAPI backend, HTTP requests, auto-scales 0-N | 8000 |
| `worker` | Celery worker for self-hosted fallback polling | — |
| `beat` | Celery Beat scheduler for polling jobs | — |
| `frontend` | Nginx serving static React build | 80 |
| `db` | PostgreSQL 16 (primary data store) | 5432 |
| `redis` | Redis 7 (cache, rate limiting, Celery broker) | 6379 |
| `minio` | MinIO (local S3-compatible object storage) | 9000/9001 |

### Data Flow

**Primary Path (Firecrawl):**
1. User creates monitor via Web UI
2. FastAPI Server calls Firecrawl API (POST /v2/monitor)
3. Firecrawl handles scheduling, scraping, AI-powered change judging, diffs
4. Webhooks delivered to our backend -> stored in PostgreSQL
5. Web UI polls API -> displays diffs, notifications, analytics

**Fallback Path (Self-Hosted):**
1. User creates monitor via Web UI
2. FastAPI Server stores config in PostgreSQL
3. Celery Beat polls URLs on schedule
4. Celery Workers: fetch URL -> extract content -> compute diff -> store snapshot
5. Notification Service sends alerts
6. Web UI polls API -> displays diffs, notifications, analytics

### Key Design Decisions

- **Firecrawl as primary**: AI-powered change judging, structured extraction, production-ready scraping
- **Self-hosted fallback**: CloakBrowser stealth rendering, readability-lxml extraction, difflib-based diffing
- **Multi-stage Docker builds**: Small production images (~150MB backend, ~25MB frontend)
- **Non-root users**: Containers run as `emily` user for security
- **Async-first**: SQLAlchemy async + asyncpg for database, Celery for background tasks

## Deployment

### Google Cloud Platform (Production)

Emily Web Delta is designed for deployment on Google Cloud Platform using Cloud Run.

#### Prerequisites

- Google Cloud account
- `gcloud` CLI installed and authenticated
- Terraform installed (for infrastructure provisioning)

#### Infrastructure Provisioning

```bash
cd infra/gcp

# Initialize Terraform
terraform init

# Create a variables file
cat > terraform.tfvars <<EOF
project_id    = "your-gcp-project-id"
region        = "us-central1"
db_password   = "your-secure-password-here"
firecrawl_api_key = "your-firecrawl-api-key"
secret_key    = "your-app-secret-key"
EOF

# Review the plan
terraform plan -var-file=terraform.tfvars

# Apply infrastructure
terraform apply -var-file=terraform.tfvars
```

This provisions:
- Cloud SQL for PostgreSQL 16 (High Availability, Enterprise tier)
- Cloud Memorystore for Redis 7
- Cloud Storage bucket with lifecycle rules (90d -> COLDLINE, 365d -> delete)
- VPC network with private subnetwork
- VPC peering for Service Networking
- Secret Manager secrets
- Cloud Run services for API and Frontend
- Firewall rules

#### Deploying to Cloud Run

```bash
# Build and push images
docker build -t us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-api:latest -f backend/Dockerfile .
docker build -t us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-frontend:latest -f frontend/Dockerfile .

gcloud auth configure-docker us-docker.pkg.dev --quiet
docker push us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-api:latest
docker push us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-frontend:latest

# Deploy API
gcloud run deploy emily-api \
  --image us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-api:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --set-secrets FIRECRAWL_API_KEY=firecrawl-api-key:latest \
  --set-secrets SECRET_KEY=secret-key:latest \
  --vpc-connector emily-vpc-connector \
  --quiet

# Deploy Frontend
gcloud run deploy emily-frontend \
  --image us-docker.pkg.dev/PROJECT_ID/emily-repo/emily-frontend:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --platform managed \
  --memory 128Mi \
  --cpu 0.5 \
  --min-instances 1 \
  --quiet
```

### Cloud Build

Alternatively, use Google Cloud Build for automated CI/CD:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## API Documentation

API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs` (development)
- **ReDoc**: `http://localhost:8000/redoc` (development)

The API follows RESTful conventions with OpenAPI 3.0 specification. Key endpoints include:

- `GET /api/v1/health` — Health check
- `POST /api/v1/monitors` — Create a new URL monitor
- `GET /api/v1/monitors` — List all monitors
- `GET /api/v1/monitors/{id}` — Get monitor details
- `PUT /api/v1/monitors/{id}` — Update monitor
- `DELETE /api/v1/monitors/{id}` — Delete monitor
- `GET /api/v1/monitors/{id}/snapshots` — Get snapshot history
- `POST /api/v1/webhooks/firecrawl` — Firecrawl webhook endpoint

## Environment Variables

### Backend (api, worker, beat)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql+asyncpg://emily:emily@db:5432/emily` |
| `REDIS_URL` | Redis connection string | Yes | `redis://redis:6379/0` |
| `FIRECRAWL_API_KEY` | Firecrawl API key for scraping | Yes | — |
| `SECRET_KEY` | JWT and session signing key | Yes | `dev-secret-key-change-in-prod` |
| `CLOAKBROWSER_PATH` | Path to CloakBrowser Chromium binary | No | `/home/emily/.cloakbrowser/chrome` |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint | No | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | No | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | No | `minioadmin` |

### Frontend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API base URL | Yes | `http://localhost:8000/api/v1` |

### Docker Compose

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FIRECRAWL_API_KEY` | Firecrawl API key | Yes | — |

## Infrastructure as Code

Terraform configurations for GCP infrastructure are located in `infra/gcp/`:

```
infra/gcp/
  main.tf       # All GCP resources (SQL, Redis, Storage, VPC, Cloud Run, Secrets)
  variables.tf  # Input variables with validation
  outputs.tf    # Output values (URLs, IPs, bucket names)
  terraform.tfvars  # Environment-specific values (gitignored)
```

### Terraform Workflow

```bash
# Initialize
terraform init -backend-config="bucket=emily-terraform-state"

# Plan
terraform plan -var-file=terraform.tfvars

# Apply
terraform apply -var-file=terraform.tfvars

# Destroy (cleanup)
terraform destroy -var-file=terraform.tfvars
```

### Outputs

After applying, Terraform outputs:
- `cloud_run_api_url` — API service URL
- `cloud_run_frontend_url` — Frontend service URL
- `cloud_sql_connection_name` — Cloud SQL connection name
- `redis_address` — Redis private IP
- `storage_bucket_name` — Cloud Storage bucket name
- `vpc_name` — VPC network name

## CI/CD

### GitHub Actions

CI/CD pipeline defined in `.github/workflows/ci-cd.yml`:

1. **test** — Runs on every PR and push to main. Lints with ruff, runs pytest with coverage.
2. **build** — Builds and pushes Docker images to Google Artifact Registry (us-docker.pkg.dev).
3. **deploy** — Deploys to Cloud Run with secrets from Secret Manager and VPC connector.

Required GitHub secrets:
- `GCP_PROJECT_ID` — GCP project ID
- `GCP_SA_KEY` — Service account JSON key

### Cloud Build

Cloud Build pipeline defined in `cloudbuild.yaml`:

1. Install dependencies and run tests
2. Build backend and frontend Docker images
3. Push images to Google Artifact Registry
4. Deploy both services to Cloud Run

Submit with: `gcloud builds submit --config=cloudbuild.yaml`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Run linter (`ruff check app/ tests/`)
6. Commit changes (`git commit -am 'Add my feature'`)
7. Push to branch (`git push origin feature/my-feature`)
8. Open a Pull Request

### Code Style

- Python: ruff linter (configured in `backend/ruff.toml`)
- Frontend: ESLint + Prettier (configured in `frontend/`)

## License

This project is licensed under the MIT License.
