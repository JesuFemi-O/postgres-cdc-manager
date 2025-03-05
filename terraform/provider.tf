terraform {
  required_providers {
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.25.0"  # Use the latest stable version
    }
  }
}

provider "postgresql" {
  host            = var.db_host
  port            = 5434
  database        = var.db_name
  username        = var.db_username
  password        = var.db_password
  sslmode         = "disable"
}
