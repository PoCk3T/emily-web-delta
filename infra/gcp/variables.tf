# Emily Web Delta — GCP Terraform Variables

variable "project_id" {
  description = "GCP project ID for Emily Web Delta resources"
  type        = string

  validation {
    condition     = length(var.project_id) > 0 && can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be a valid GCP project ID (lowercase, 6-30 chars)."
  }
}

variable "region" {
  description = "GCP region for resource deployment"
  type        = string
  default     = "us-central1"

  validation {
    condition     = contains(["us-central1", "us-east1", "us-west1", "europe-west1", "europe-west4", "asia-east1"], var.region)
    error_message = "region must be one of: us-central1, us-east1, us-west1, europe-west1, europe-west4, asia-east1"
  }
}

variable "db_password" {
  description = "Password for the PostgreSQL emily database user"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "db_password must be at least 16 characters long."
  }
}

variable "firecrawl_api_key" {
  description = "Firecrawl API key for web scraping and monitoring"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Application secret key for JWT and session signing"
  type        = string
  sensitive   = true
}

variable "api_image" {
  description = "Container image for the API service (e.g., us-docker.pkg.dev/project/repo/emily-api:tag)"
  type        = string
  default     = "us-docker.pkg.dev/emily-web-delta/emily-repo/emily-api:latest"
}

variable "frontend_image" {
  description = "Container image for the frontend service (e.g., us-docker.pkg.dev/project/repo/emily-frontend:tag)"
  type        = string
  default     = "us-docker.pkg.dev/emily-web-delta/emily-repo/emily-frontend:latest"
}
