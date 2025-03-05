# Global Variables
PYTHON := python3
VENV := venv
CONFIG := custom-cli/replication.yml
SRC_DIR := custom-cli/src
CLI_SCRIPT := $(SRC_DIR)/cdc_cli.py
TERRAFORM_DIR := terraform
DOCKER_DIR := docker

DB_HOST := localhost
DB_PORT := 5434
DB_NAME := postgres
DB_USER := postgres
DB_PASSWORD := postgres

# Export password for non-interactive use
export PGPASSWORD := $(DB_PASSWORD)

.PHONY: help setup docker-up docker-down docker-reset venv install validate_config create_all create_profile drop_all drop_profile terraform-init terraform-apply terraform-destroy show_publications show_publication_tables show_replication_slots clean

## Show available make commands
help:
	@echo "Available commands:"
	@echo ""
	@echo "  setup               - Setup the project (Docker, Python dependencies, Terraform init)"
	@echo "  docker-up           - Start PostgreSQL database in Docker"
	@echo "  docker-down         - Stop the database container"
	@echo "  docker-reset        - Reset the database container"
	@echo "  venv                - Create a Python virtual environment"
	@echo "  install             - Install Python dependencies"
	@echo "  validate_config     - Validate replication.yml file"
	@echo "  create_all          - Create all replication slots and publications"
	@echo "  create_profile      - Create a specific replication profile (PROFILE required)"
	@echo "  drop_all            - Drop all replication slots and publications"
	@echo "  drop_profile        - Drop a specific replication profile (PROFILE required)"
	@echo "  terraform-init      - Initialize Terraform"
	@echo "  terraform-apply     - Apply Terraform configuration"
	@echo "  terraform-destroy   - Destroy Terraform-managed CDC objects"
	@echo "  show_publications     - List all PostgreSQL publications"
	@echo "  show_publication_tables - List tables in a specific publication (PUB_NAME required)"
	@echo "  show_replication_slots - List all replication slots"
	@echo "  clean               - Remove Terraform state and reset the environment"

# -------------------------
# 🚀 Setup Commands
# -------------------------

## Setup the project (Docker, Python dependencies, Terraform init)
setup: ensure-env docker-up venv install terraform-init

## Ensure .env file exists in SRC_DIR by copying from .env.example if missing
ensure-env:
	@if [ ! -f "$(SRC_DIR)/.env" ]; then cp $(SRC_DIR)/.env.example $(SRC_DIR)/.env; echo "$(SRC_DIR)/.env file created from .env.example"; else echo "$(SRC_DIR)/.env file already exists"; fi

## Create a Python virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then $(PYTHON) -m venv $(VENV); fi
	@echo "Virtual environment created. Activate it using: source $(VENV)/bin/activate"

## Install Python dependencies
install:
	$(VENV)/bin/pip install -r requirements.txt
	@echo "Python dependencies installed."

# -------------------------
# 🐳 Docker Database Management
# -------------------------

## Start the PostgreSQL database in Docker
docker-up:
	cd $(DOCKER_DIR) && docker-compose up -d
	@echo "PostgreSQL database started in Docker."

## Stop the database container
docker-down:
	cd $(DOCKER_DIR) && docker-compose down
	@echo "PostgreSQL database stopped."

## Reset the database container
docker-reset: docker-down docker-up
	@echo "PostgreSQL database reset."

# -------------------------
# ⚡ Python CLI Commands
# -------------------------

## Validate the replication.yml configuration
validate_config:
	$(VENV)/bin/python $(CLI_SCRIPT) --config $(CONFIG) validate_config
	@echo "✅ YAML validation successful."

## Create replication slots and publications for all profiles
create_all:
	$(VENV)/bin/python $(CLI_SCRIPT) --config $(CONFIG) create_all

## Create replication slots and publications for a specific profile
create_profile:
	@if [ -z "$$PROFILE" ]; then echo "PROFILE variable is required"; exit 1; fi
	$(VENV)/bin/python $(CLI_SCRIPT) --config $(CONFIG) create_profile $$PROFILE

## Drop all replication slots and publications
drop_all:
	$(VENV)/bin/python $(CLI_SCRIPT) --config $(CONFIG) drop_all

## Drop replication slot and publication for a specific profile
drop_profile:
	@if [ -z "$$PROFILE" ]; then echo "PROFILE variable is required"; exit 1; fi
	$(VENV)/bin/python $(CLI_SCRIPT) --config $(CONFIG) drop_profile $$PROFILE

# -------------------------
# 🌍 Terraform Commands
# -------------------------

## Initialize Terraform
terraform-init:
	cd $(TERRAFORM_DIR) && terraform init

## Apply Terraform configuration
terraform-apply:
	cd $(TERRAFORM_DIR) && terraform apply -auto-approve

## Destroy Terraform-managed CDC objects
terraform-destroy:
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve

# -------------------------
# Postgres Commands
# -------------------------
## Show all publications
show_publications:
	psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -c "SELECT * FROM pg_publication;"

## Show tables in a specific publication (requires PUB_NAME variable)
show_publication_tables:
	@if [ -z "$$PUB_NAME" ]; then echo "PUB_NAME variable is required"; exit 1; fi
	psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -c "SELECT * FROM pg_publication_tables WHERE pubname = '$$PUB_NAME';"

## Show all replication slots
show_replication_slots:
	psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -c "SELECT slot_name, plugin, slot_type, database, active, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

# -------------------------
# 🧹 Cleanup
# -------------------------

## Remove Terraform state and reset the environment
clean:
	rm -rf $(VENV) $(TERRAFORM_DIR)/.terraform $(TERRAFORM_DIR)/terraform.tfstate*
	@echo "Cleaned up Terraform state and Python virtual environment."
