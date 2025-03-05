import yaml
from typing import List, Dict, Any, Optional

class ReplicationConfigParser:
    """
    Parses and validates the YAML configuration for PostgreSQL replication management.
    """
    REQUIRED_CONNECTION_KEYS = {"name", "type", "credential_id"}
    REQUIRED_REPLICATION_KEYS = {"replication_profile_name", "connection_profile", "publication_name", "slot_name", "publication_ops", "publication_type"}
    VALID_PUBLICATION_TYPES = {"all", "schema", "filtered"}
    VALID_OPS = {"INSERT", "UPDATE", "DELETE"}
    
    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
        self.config = self._load_yaml()
        self._validate_config()
        self.connection_profiles = self.config.get("CONNECTION_PROFILES", [])
        self.replication_profiles = self.config.get("REPLICATION_PROFILES", [])
    
    def _load_yaml(self) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        try:
            with open(self.yaml_path, "r") as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found: {self.yaml_path}")
    
    def _validate_config(self):
        """Validates the required keys in the YAML file."""
        if not isinstance(self.config, dict):
            raise ValueError("Invalid YAML structure. Expected a dictionary at root level.")
        
        if "CONNECTION_PROFILES" not in self.config or not isinstance(self.config["CONNECTION_PROFILES"], list):
            raise ValueError("Missing or invalid CONNECTION_PROFILES section.")
        
        if "REPLICATION_PROFILES" not in self.config or not isinstance(self.config["REPLICATION_PROFILES"], list):
            raise ValueError("Missing or invalid REPLICATION_PROFILES section.")
        
        replication_profile_names = set()
        publication_names = set()
        slot_names = set()
        table_occurrences = {}
        connection_names = {conn["name"] for conn in self.config["CONNECTION_PROFILES"]}
        
        for profile in self.config["CONNECTION_PROFILES"]:
            self._validate_keys(profile, self.REQUIRED_CONNECTION_KEYS, "CONNECTION_PROFILES")
        
        for profile in self.config["REPLICATION_PROFILES"]:
            self._validate_keys(profile, self.REQUIRED_REPLICATION_KEYS, "REPLICATION_PROFILES")
            self._validate_replication_profile(profile)
            

            if profile["replication_profile_name"] in replication_profile_names:
                raise ValueError(f"Duplicate replication profile name found: {profile['replication_profile_name']}")
            replication_profile_names.add(profile["replication_profile_name"])

            if profile["publication_name"] in publication_names:
                raise ValueError(f"Duplicate publication name found: {profile['publication_name']}")
            publication_names.add(profile["publication_name"])
            
            if profile["slot_name"] in slot_names:
                raise ValueError(f"Duplicate replication slot found: {profile['slot_name']}")
            slot_names.add(profile["slot_name"])
            
            if profile["connection_profile"] not in connection_names:
                raise ValueError(f"Invalid connection_profile '{profile['connection_profile']}'. Must match a defined connection profile name.")
            
            if profile["publication_type"] == "filtered":
                for table in profile.get("publication_tables", []):
                    formatted_table = f"{profile['connection_profile']}.{table}"
                    if table in table_occurrences:
                        print(f"\033[91m⚠ WARNING: Table '{formatted_table}' appears in multiple replication profiles.\033[0m")
                        
                    table_occurrences[table] = True
            
    
    def _validate_keys(self, profile: Dict[str, Any], required_keys: set, section: str):
        """Ensures all required keys are present in a given section."""
        missing_keys = required_keys - profile.keys()
        if missing_keys:
            raise ValueError(f"Missing keys {missing_keys} in {section} section.")
    
    def _validate_replication_profile(self, profile: Dict[str, Any]):
        """Validates the replication profile fields."""
        if profile["publication_type"] not in self.VALID_PUBLICATION_TYPES:
            raise ValueError(
                f"Invalid publication_type '{profile['publication_type']}'. Must be one of {self.VALID_PUBLICATION_TYPES} in replication profile '{profile['replication_profile_name']}'."
                )
        
        invalid_ops = set(profile["publication_ops"]) - self.VALID_OPS
        if invalid_ops:
            raise ValueError(
                f"Invalid publication_ops {invalid_ops}. Must be one of {self.VALID_OPS} in replication profile '{profile['replication_profile_name']}'."
                )
        
        if profile["publication_type"] == "filtered" and "publication_tables" not in profile:
            raise ValueError(
                f"Filtered publication_type requires 'publication_tables' field in replication profile '{profile['replication_profile_name']}'."
                )
        
        if profile["publication_type"] == "schema" and "publication_schema" not in profile:
            raise ValueError(
                f"Schema publication_type requires 'publication_schema' field in replication profile '{profile['replication_profile_name']}'."
                )
    
    def get_connection_profiles(self) -> List[Dict[str, Any]]:
        """Returns all connection profiles."""
        return self.connection_profiles
    
    def get_replication_profiles(self) -> List[Dict[str, Any]]:
        """Returns all replication profiles."""
        return self.replication_profiles
    
    def get_connection_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetches a connection profile by name."""
        return next((conn for conn in self.connection_profiles if conn["name"] == name), None)
    
    def get_replication_by_publication(self, publication_name: str) -> Optional[Dict[str, Any]]:
        """Fetches a replication profile by publication name."""
        return next((rep for rep in self.replication_profiles if rep["publication_name"] == publication_name), None)

# Example usage
if __name__ == "__main__":
    parser = ReplicationConfigParser("config.yaml")
    print(parser.get_connection_profiles())
    print(parser.get_replication_profiles())