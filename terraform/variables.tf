variable "publications" {
  description = "List of PostgreSQL publications"
  type = list(object({
    name  = string
    ops   = list(string)
    type  = string
    schema = optional(string)
    tables = optional(list(string))
  }))
}

variable "replication_slots" {
  description = "List of PostgreSQL replication slots"
  type = list(object({
    name           = string
    output_plugin = string
  }))
}

variable "db_host" {
  description = "PostgreSQL database host"
  type        = string
  default     = "localhost"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "postgres"
}

variable "db_username" {
  description = "PostgreSQL username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}
