PYTHON := python3
CONFIG := replication.yml
SRC_DIR := src
CLI_SCRIPT := $(SRC_DIR)/cdc_cli.py

.PHONY: create_all create_profile drop_all drop_profile validate_config

## Create replication slots and publications for all profiles
create_all:
	$(PYTHON) $(CLI_SCRIPT) --config $(CONFIG) create_all

## Create replication slots and publications for a specific profile
create_profile:
	@if [ -z "$$PROFILE" ]; then echo "PROFILE variable is required"; exit 1; fi
	$(PYTHON) $(CLI_SCRIPT) --config $(CONFIG) create_profile $$PROFILE

## Drop all replication slots and publications
drop_all:
	$(PYTHON) $(CLI_SCRIPT) --config $(CONFIG) drop_all

## Drop replication slot and publication for a specific profile
drop_profile:
	@if [ -z "$$PROFILE" ]; then echo "PROFILE variable is required"; exit 1; fi
	$(PYTHON) $(CLI_SCRIPT) --config $(CONFIG) drop_profile $$PROFILE

## Validate replication.yml using the parser class
validate_config:
	$(PYTHON) $(CLI_SCRIPT) --config $(CONFIG) validate_config