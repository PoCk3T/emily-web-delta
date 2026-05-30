# Emily Web Delta — GCP Infrastructure (Terraform)
# All GCP resources for production deployment on Google Cloud Platform.

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "emily-terraform-state"
    prefix = "gcp"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Enable APIs ───
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudbuild.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# ─── Cloud SQL for PostgreSQL ───
resource "google_sql_database_instance" "emily" {
  name             = "emily-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier                        = "db-custom-2-7680"
    edition                     = "ENTERPRISE"
    availability_type           = "HIGH_AVAILABILITY"
    disk_size                   = 20
    disk_autoresize             = true
    disk_autoresize_limit       = 100
    user_labels = {
      "app" = "emily"
    }

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention      = "7D"
    }

    # Database Insights
    insights_config {
      query_insights_enabled = true
    }

    # Connection settings
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.emily.id
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "emily" {
  name     = "emily"
  instance = google_sql_database_instance.emily.name
}

resource "google_sql_user" "emily" {
  name     = "emily"
  instance = google_sql_database_instance.emily.name
  password = var.db_password
}

# ─── Cloud Memorystore (Redis) ───
resource "google_redis_instance" "emily" {
  name                    = "emily-redis"
  memory_size_gb          = 1
  tier                    = "BASIC"
  redis_version           = "REDIS_7_0"
  region                  = var.region
  connect_mode            = "PRIVATE_SERVICE_ACCESS"

  authorized_network = google_compute_network.emily.id

  redis_configs = {
    "maxmemory-policy" = "allkeys-lru"
    "maxmemory-samples" = "5"
  }

  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.emily,
  ]
}

# ─── Cloud Storage (S3-compatible snapshots) ───
resource "google_storage_bucket" "snapshots" {
  name                          = "${var.project_id}-emily-snapshots"
  location                      = "US"
  uniform_bucket_level_access   = true
  force_destroy                 = false

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.apis]
}

# ─── VPC & Subnetwork ───
resource "google_compute_network" "emily" {
  name                    = "emily-vpc"
  auto_create_subnetworks = false

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "emily" {
  name          = "emily-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.emily.name

  private_ip_google_access = true
}

# ─── VPC Peering Range for Service Networking ───
resource "google_compute_global_address" "emily" {
  name         = "emily-addr"
  address_type = "INTERNAL"
  purpose      = "VPC_PEERING"
  ip_cidr_range = "10.19.0.0/16"
  network      = google_compute_network.emily.name
}

# ─── Service Networking Connection (VPC Peering) ───
resource "google_service_networking_connection" "emily" {
  network                 = google_compute_network.emily.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.emily.name]
}

# ─── Firewall Rules ───
resource "google_compute_firewall" "emily" {
  name    = "emily-allow-health"
  network = google_compute_network.emily.name

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["emily"]
}

# ─── VPC Connector for Cloud Run ───
resource "google_compute_region_network_endpoint_group" "emily_vpc_connector" {
  name                  = "emily-vpc-connector"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  default_port          = 8000
}

# ─── Secret Manager ───
resource "google_secret_manager_secret" "firecrawl_api_key" {
  secret_id = "firecrawl-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "firecrawl_api_key" {
  secret_id = google_secret_manager_secret.firecrawl_api_key.id
  secret_data = var.firecrawl_api_key
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret_id = google_secret_manager_secret.secret_key.id
  secret_data = var.secret_key
}

# ─── Cloud Run Service (API) ───
resource "google_cloud_run_v2_service" "api" {
  name     = "emily-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    max_instance_duration = "5m"
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    vpc_access {
      network_interfaces {
        network    = google_compute_network.emily.id
        subnetwork = google_compute_subnetwork.emily.id
        access_config {
          network_tag = "emily"
        }
      }
    }

    containers {
      image = var.api_image

      ports {
        container_port = 8000
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql://${google_sql_user.emily.name}:${var.db_password}@/${google_sql_database.emily.name}"
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.emily.primary_address[0].address}:${google_redis_instance.emily.port}/0"
      }

      env {
        name  = "FIRECRAWL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.firecrawl_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        cpu_request    = "1"
        memory_limit = "512Mi"
        concurrency    = 80
      }
    }
  }

  depends_on = [
    google_service_networking_connection.emily,
    google_compute_firewall.emily,
  ]
}

# ─── Cloud Run Job (DB Migrations) ───
resource "google_cloud_run_v2_job" "migrate" {
  name     = "emily-migrate"
  location = var.region

  template {
    template {
      max_retries = 1

      containers {
        image = var.api_image

        command = ["python", "/app/run_migrations.py"]

        env {
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.emily.name}:${var.db_password}@/${google_sql_database.emily.name}"
        }

        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.emily.primary_address[0].address}:${google_redis_instance.emily.port}/0"
        }

        env {
          name  = "FIRECRAWL_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.firecrawl_api_key.secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "SECRET_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.secret_key.secret_id
              version = "latest"
            }
          }
        }

        resources {
          cpu_request    = "0.5"
          memory_limit = "256Mi"
        }
      }
    }
  }

  depends_on = [
    google_service_networking_connection.emily,
    google_compute_firewall.emily,
  ]
}

# ─── Cloud Run Service (Frontend) ───
resource "google_cloud_run_v2_service" "frontend" {
  name     = "emily-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 80
      }

      resources {
        cpu_request    = "0.5"
        memory_limit = "128Mi"
        concurrency    = 80
      }
    }
  }
}
