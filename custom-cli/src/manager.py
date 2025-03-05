import psycopg2
import boto3
import os
import json
from parser import ReplicationConfigParser
from typing import Dict, Any, Optional, Sequence, Union, Set
from pydantic import BaseModel
from urllib.parse import urlparse
from dotenv import load_dotenv
from psycopg2.extensions import cursor, connection as ConnectionExt
from psycopg2.extras import LogicalReplicationConnection, ReplicationCursor

load_dotenv()

class DBCredential(BaseModel):
    database: str
    username: str
    password: str
    host: str
    port: int = 5432

class CDCManager:
    def __init__(self, config_path: str):
        self.parser = ReplicationConfigParser(yaml_path=config_path)
        self.connection_profiles = self.parser.get_connection_profiles()
        self.replication_profiles = self.parser.get_replication_profiles()
        self.replication_schemas = self._extract_schemas()
    
    def get_connection_credentials(self, connection_name: str) -> DBCredential:
        """Fetches connection credentials from AWS Secrets Manager or environment variables."""
        connection = next((conn for conn in self.connection_profiles if conn["name"] == connection_name), None)
        if not connection:
            raise ValueError(f"Connection profile '{connection_name}' not found.")
        
        if connection["type"] == "AWS_SECRETS":
            creds = self._fetch_aws_secrets(connection["credential_id"])
        elif connection["type"] == "ENV_SECRETS":
            creds = self._fetch_env_secrets(connection["credential_id"])
        else:
            raise ValueError(f"Invalid connection type '{connection['type']}' for profile '{connection_name}'.")
        
        return DBCredential(**creds)
    
    def _fetch_aws_secrets(self, secret_name: str) -> Dict[str, Any]:
        """Fetches secrets from AWS Secrets Manager."""
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager')
        
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = response.get("SecretString")
            return json.loads(secret) if secret else {}
        except Exception as e:
            raise RuntimeError(f"Failed to fetch secret '{secret_name}': {e}")
    
    def _fetch_env_secrets(self, env_var: str) -> Dict[str, Any]:
        """Parses database credentials from an environment variable containing a PostgreSQL URL."""
        secret_value = os.getenv(env_var)
        if not secret_value:
            raise ValueError(f"Environment variable '{env_var}' not set.")
        
        parsed_url = urlparse(secret_value)
        return {
            "database": parsed_url.path.lstrip("/"),
            "username": parsed_url.username,
            "password": parsed_url.password,
            "host": parsed_url.hostname,
            "port": parsed_url.port or 5432
        }
    
    def _extract_schemas(self) -> Set[str]:
        """Extracts distinct schemas from the replication profiles."""
        schemas = set()
        for profile in self.replication_profiles:
            if profile["publication_type"] == "schema" and "publication_schema" in profile:
                schemas.add(profile["publication_schema"])
            elif profile["publication_type"] == "filtered" and "publication_tables" in profile:
                for table in profile["publication_tables"]:
                    schema = table.split(".")[0]  # Extract schema from fully qualified table name
                    schemas.add(schema)
        return schemas
    
    def _get_conn(self, creds: DBCredential, connection_factory: Optional[Any] = None) -> ConnectionExt:
        """Returns a psycopg2 connection with an optional factory for replication support."""
        return psycopg2.connect(
            database=creds.database,
            user=creds.username,
            password=creds.password,
            host=creds.host,
            port=creds.port,
            connection_factory=connection_factory,
        )
    
    def _get_rep_conn(self, creds: DBCredential) -> LogicalReplicationConnection:
        """Returns a LogicalReplicationConnection for PostgreSQL logical replication."""
        return self._get_conn(creds, LogicalReplicationConnection)

    
    def create_replication_slot(self, name: str, cur: ReplicationCursor, output_plugin: str = "pgoutput") -> Optional[Dict[str, str]]:
        """Creates a replication slot if it doesn't exist yet."""
        try:
            cur.create_replication_slot(name, output_plugin=output_plugin)
            print(f'Successfully created replication slot "{name}".')
            result = cur.fetchone()
            return {
                "slot_name": result[0],
                "consistent_point": result[1],
                "snapshot_name": result[2],
                "output_plugin": result[3],
            }
        except psycopg2.errors.DuplicateObject:  # the replication slot already exists
            print(
                f'Replication slot "{name}" cannot be created because it already exists.'
            )

    
    def grant_schema_privileges(self, conn: ConnectionExt, replication_user: str) -> None:
        """Grants required privileges to the replication user for only the relevant schemas."""
        cur = conn.cursor()
        for schema in self.replication_schemas:
            cur.execute(f"GRANT USAGE ON SCHEMA {schema} TO {replication_user};")
            cur.execute(f"GRANT SELECT, REFERENCES ON ALL TABLES IN SCHEMA {schema} TO {replication_user};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT, REFERENCES ON TABLES TO {replication_user};")
        
        conn.commit()
        cur.close()
        print(f"Granted replication privileges for schemas: {self.replication_schemas}")

    def create_publication(self, pub_name: str, pub_ops: str, pub_type: str, schema_name: Optional[str], cur: cursor) -> None:
        """Creates a publication based on the specified publication type and operations."""
        try:
            if pub_type == "all":
                cur.execute(f"CREATE PUBLICATION {pub_name} FOR ALL TABLES WITH (publish = '{pub_ops}');")
            elif pub_type == "schema" and schema_name:
                cur.execute(f"CREATE PUBLICATION {pub_name} FOR TABLES IN SCHEMA {schema_name} WITH (publish = '{pub_ops}');")
            elif pub_type == "filtered":
                cur.execute(f"CREATE PUBLICATION {pub_name} WITH (publish = '{pub_ops}');")
            print(f"Successfully created publication {pub_name} with type '{pub_type}'.")
        except psycopg2.errors.DuplicateObject:
            print(f"Publication {pub_name} already exists.")

    
    def add_table_to_publication(self, table: str, pub_name: str, cur: cursor) -> None:
        """Adds a table to a publication."""
        try:
            cur.execute(f"ALTER PUBLICATION {pub_name} ADD TABLE {table};")
            print(f"Successfully added {table} to publication {pub_name}.")
        except psycopg2.errors.DuplicateObject:
            print(f"Table {table} is already in publication {pub_name}.")
    
    def drop_replication_slot(self, name: str, cur: ReplicationCursor) -> None:
        """Drops a replication slot if it exists."""
        try:
            cur.drop_replication_slot(name)
            print(f'Successfully dropped replication slot "{name}".')
        except psycopg2.errors.UndefinedObject:  # the replication slot does not exist
            print(
                f'Replication slot "{name}" cannot be dropped because it does not exist.'
            )
    
    def drop_publication(self, name: str, cur: cursor) -> None:
        """Drops a publication if it exists."""
        try:
            cur.execute(f"DROP PUBLICATION {name};")
            cur.connection.commit()
            print(f"Successfully dropped publication {name}.")
        except psycopg2.errors.UndefinedObject:  # the publication does not exist
            print(
                f"Publication {name} cannot be dropped because it does not exist."
            )
    
    def drop_replication_for_profile(self, profile: Dict[str, Any]) -> None:
        """Drops the replication slot and publication for a given replication profile."""
        connection_name = profile["connection_profile"]
        creds = self.get_connection_credentials(connection_name)
        conn = self._get_rep_conn(creds)
        cur = conn.cursor()
        
        print(f"Dropping replication slot {profile['slot_name']}")
        self.drop_replication_slot(profile["slot_name"], cur)
        
        print(f"Dropping publication {profile['publication_name']}")
        self.drop_publication(profile["publication_name"], cur)
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Dropped replication setup for profile: {profile['replication_profile_name']}")
    
    def drop_all_replication_profiles(self) -> None:
        """Drops all replication slots and publications across all configured profiles."""
        for profile in self.replication_profiles:
            self.drop_replication_for_profile(profile)
    
    def process_replication_profile(self, profile: Dict[str, Any]) -> None:
        """Processes a single replication profile to create publications and replication slots."""
        connection_name = profile["connection_profile"]
        creds = self.get_connection_credentials(connection_name)
        conn = self._get_rep_conn(creds)
        cur = conn.cursor()
        
        pub_ops = ', '.join(profile["publication_ops"])
        pub_type = profile["publication_type"]
        schema_name = profile.get("publication_schema")

        # replication_user = creds.username  # Assuming the user running replication is the connection user
        # super user already should have the required privileges so this "may" not be necessary
        # self.grant_schema_privileges(conn, replication_user)
        
        print(f"Creating publication {profile['publication_name']} with ops {pub_ops} and type {pub_type}")
        self.create_publication(profile["publication_name"], pub_ops, pub_type, schema_name, cur)
        
        if "publication_tables" in profile and pub_type == "filtered":
            for table in profile["publication_tables"]:
                self.add_table_to_publication(table, profile["publication_name"], cur)
        
        print(f"Creating replication slot {profile['slot_name']}")
        slot_info = self.create_replication_slot(profile["slot_name"], cur)
        
        if slot_info:
            print(
                f"Replication Slot Created:\n"
                f"  - Slot Name: {slot_info['slot_name']}\n"
                f"  - Consistent Point: {slot_info['consistent_point']}\n"
                f"  - Snapshot Name: {slot_info['snapshot_name']}\n"
                f"  - Output Plugin: {slot_info['output_plugin']}"
            )

        conn.commit()
        cur.close()
        conn.close()
        print(f"Processed replication profile: {profile['replication_profile_name']}")

    
    def process_replication_profiles(self) -> None:
        """Processes all replication profiles by calling process_replication_profile for each one."""
        for profile in self.replication_profiles:
            self.process_replication_profile(profile)
    