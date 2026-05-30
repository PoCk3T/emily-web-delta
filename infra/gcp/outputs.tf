# Emily Web Delta — GCP Terraform Outputs

output "cloud_run_api_url" {
  description = "URL of the deployed Emily API Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "cloud_run_frontend_url" {
  description = "URL of the deployed Emily Frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name for direct connections"
  value       = google_sql_database_instance.emily.connection_name
}

output "cloud_sql_host" {
  description = "Private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.emily.private_ip_address
}

output "redis_address" {
  description = "Private IP address of the Cloud Memorystore Redis instance"
  value       = google_redis_instance.emily.host
}

output "redis_port" {
  description = "Port of the Cloud Memorystore Redis instance"
  value       = google_redis_instance.emily.port
}

output "storage_bucket_name" {
  description = "Name of the Cloud Storage bucket for snapshots"
  value       = google_storage_bucket.snapshots.name
}

output "vpc_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.emily.name
}

output "vpc_subnetwork_name" {
  description = "Name of the VPC subnetwork"
  value       = google_compute_subnetwork.emily.name
}

output "vpc_connector_name" {
  description = "Name of the VPC connector for Cloud Run"
  value       = google_compute_region_network_endpoint_group.emily_vpc_connector.name
}
