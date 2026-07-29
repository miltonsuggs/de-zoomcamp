variable "credentials" {
    description = "My credentials"
    default = "./keys/my-creds.json"
}

variable "project" {
    description = "Project"
    default = "terraform-demo-503418"
}

variable "location" {
    description = "Project Location"
    default = "US"
}

variable "region" {
    description = "Project region"
    default = "us-central1"
}

variable "bq_dataset_name" {
    description = "My BigQuery Dataset Name"
    default = "demo_dataset"
}

variable "gcs_bucket_name" {
    description = "My storage bucket name"
    default = "terraform-demo-503418-terra-bucket"
}

variable "gcs_storage_class" {
    description = "Bucket strage class"
    default = "STANDARD"
}