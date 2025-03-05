import argparse
from manager import CDCManager
from parser import ReplicationConfigParser

def main():
    parser = argparse.ArgumentParser(description="CLI for managing PostgreSQL CDC replication.")
    parser.add_argument("--config", type=str, required=True, help="Path to the replication YAML config file.")
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")
    
    # Create for all profiles
    subparsers.add_parser("create_all", help="Create publications and replication slots for all profiles.")
    
    # Create for a specific profile
    create_profile_parser = subparsers.add_parser("create_profile", help="Create publication and replication slot for a specific profile.")
    create_profile_parser.add_argument("profile_name", type=str, help="Replication profile name to process.")
    
    # Drop for all profiles
    subparsers.add_parser("drop_all", help="Drop publications and replication slots for all profiles.")
    
    # Drop for a specific profile
    drop_profile_parser = subparsers.add_parser("drop_profile", help="Drop publication and replication slot for a specific profile.")
    drop_profile_parser.add_argument("profile_name", type=str, help="Replication profile name to drop.")

    # Validate YAML
    subparsers.add_parser("validate_config", help="Validate the replication YAML configuration file.")
    
    args = parser.parse_args()

    if args.command == "validate_config":
        try:
            ReplicationConfigParser(args.config)
            print("✅ YAML validation successful.")
        except Exception as e:
            print(f"❌ YAML validation failed: {e}")
            exit(1)
    
    # Initialize CDC Manager
    cdc_manager = CDCManager(config_path=args.config)
    
    if args.command == "create_all":
        print("Creating publications and replication slots for all profiles...")
        cdc_manager.process_replication_profiles()
    
    elif args.command == "create_profile":
        profile = next((p for p in cdc_manager.replication_profiles if p["replication_profile_name"] == args.profile_name), None)
        if profile:
            print(f"Creating publication and replication slot for profile {args.profile_name}...")
            cdc_manager.process_replication_profile(profile)
        else:
            print(f"Error: Profile '{args.profile_name}' not found in config.")
    
    elif args.command == "drop_all":
        print("Dropping all replication slots and publications...")
        cdc_manager.drop_all_replication_profiles()
    
    elif args.command == "drop_profile":
        profile = next((p for p in cdc_manager.replication_profiles if p["replication_profile_name"] == args.profile_name), None)
        if profile:
            print(f"Dropping publication and replication slot for profile {args.profile_name}...")
            cdc_manager.drop_replication_for_profile(profile)
        else:
            print(f"Error: Profile '{args.profile_name}' not found in config.")

if __name__ == "__main__":
    main()
