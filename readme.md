# **Change Data Capture (CDC) Management with PostgreSQL**

## **Overview**
This project provides **two approaches** to managing **PostgreSQL publications and replication slots** for Change Data Capture (CDC):
1. **Custom Python CLI** (`custom-cli/`) - Uses a YAML configuration file (`replication.yml`) to manage replication objects declaratively.
2. **Terraform Implementation** (`terraform/`) - Uses Terraform to provision and manage replication objects.

The **Makefile** simplifies execution by abstracting complex commands into easy-to-run targets.

## 📂 Project Structure
This project is organized as follows:

.
├── Makefile             # Main Makefile for managing CLI, Terraform, and Docker
├── custom-cli/          # Custom Python CLI for CDC management
│   ├── Makefile         # CLI-specific Makefile
│   ├── replication.yml  # YAML config defining replication profiles
│   └── src/             # Source code for the CLI
│       ├── cdc_cli.py   # CLI entrypoint
│       ├── manager.py   # Manages replication slots & publications
│       └── parser.py    # YAML parser & validator
├── docker/              # Dockerized PostgreSQL setup
│   ├── docker-compose.yml # Docker setup for PostgreSQL
│   └── init.sql         # Initialization SQL scripts
├── terraform/           # Terraform scripts for managing CDC
│   ├── main.tf          # Terraform resources (publications, slots)
│   ├── outputs.tf       # Outputs for Terraform state
│   ├── provider.tf      # PostgreSQL provider config
│   ├── terraform.tfstate # Terraform state file
│   ├── terraform.tfvars # Variables for Terraform
│   └── variables.tf     # Terraform variable definitions
├── requirements.txt      # Python dependencies
└── readme.md             # Project documentation


---

## **🚀 Quick Start**

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/JesuFemi-O/postgres-cdc-manager.git
cd postgres-cdc-manager
```

### **2️⃣ Setup the Environment**
```sh
make setup
```
This will:
- Start a **PostgreSQL** database in Docker
- Create a **Python virtual environment**
- Install dependencies
- Initialize Terraform

---

## **🛠️ Available Commands**
### **General Setup**
| Command               | Description |
|-----------------------|-------------|
| `make setup`         | Full project setup (Docker, Python, Terraform) |
| `make help`          | Show available commands |

### **🐳 Docker Commands**
| Command              | Description |
|----------------------|-------------|
| `make docker-up`    | Start the database in Docker |
| `make docker-down`  | Stop the database container |
| `make docker-reset` | Reset the database container |

### **⚡ Python CLI Commands**
| Command                  | Description |
|--------------------------|-------------|
| `make validate_config`   | Validate `replication.yml` file |
| `make create_all`        | Create replication slots & publications for **all profiles** |
| `make create_profile PROFILE=cdc_pub` | Create for a **specific profile** |
| `make drop_all`          | Drop **all** replication slots & publications |
| `make drop_profile PROFILE=cdc_pub` | Drop **a specific profile** |

### **🌍 Terraform Commands**
| Command                | Description |
|------------------------|-------------|
| `make terraform-init`  | Initialize Terraform |
| `make terraform-apply` | Apply Terraform configuration |
| `make terraform-destroy` | Destroy Terraform-managed CDC objects |

### **📊 PostgreSQL Inspection**
| Command                          | Description |
|----------------------------------|-------------|
| `make show_publications`         | Show all publications |
| `make show_publication_tables PUB_NAME=cdc_pub` | Show tables in a **specific publication** |
| `make show_replication_slots`    | Show all replication slots |

### **🧹 Cleanup**
| Command      | Description |
|-------------|-------------|
| `make clean` | Reset Terraform state and remove Python virtual environment |

---

## **📄 Understanding `replication.yml`**
The YAML configuration defines **how replication objects should be managed**. It consists of two key sections: **CONNECTION_PROFILES** and **REPLICATION_PROFILES**.

### **🔹 CONNECTION_PROFILES**
Defines **database connections**.

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | ✅ | Unique connection name |
| `type` | string | ✅ | Either `AWS_SECRETS` or `ENV_SECRETS` |
| `credential_id` | string | ✅ | Identifier for retrieving credentials |

Example:
```yaml
CONNECTION_PROFILES:
  - name: dev_pg_db
    type: ENV_SECRETS
    credential_id: PG_URL
```

---

### **🔹 REPLICATION_PROFILES**
Defines **CDC replication configurations**.

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `replication_profile_name` | string | ✅ | Unique identifier for the profile |
| `connection_profile` | string | ✅ | Associated connection profile |
| `publication_name` | string | ✅ | Name of the PostgreSQL publication |
| `slot_name` | string | ✅ | Name of the replication slot |
| `publication_ops` | list<string> | ✅ | Allowed operations (`INSERT`, `UPDATE`, `DELETE`) |
| `publication_type` | string | ✅ | `all`, `schema`, or `filtered` |
| `publication_tables` | list<string> | ❌ (Required if `publication_type=filtered`) | Tables to replicate |
| `publication_schema` | string | ❌ (Required if `publication_type=schema`) | Schema to replicate |

Example:
```yaml
REPLICATION_PROFILES:
  - replication_profile_name: prod_to_dev
    connection_profile: dev_pg_db
    publication_name: cdc_dev_pub
    slot_name: cdc_dev_slot
    publication_ops:
      - INSERT
      - UPDATE
      - DELETE
    publication_type: filtered
    publication_tables:
      - bookies.bets
      - bookies.transactions
```


---

## **🛠️ Terraform Approach**
Instead of using Python, Terraform can also be used to **declaratively manage replication objects**.

### **🔹 Example Terraform Variables**
```hcl
variable "publications" {
  type = list(object({
    name  = string
    ops   = list(string)
    type  = string
    tables = optional(list(string))
  }))
}
```

### **🔹 Example Terraform Configuration**
```hcl
resource "postgresql_publication" "publications" {
  for_each = { for pub in var.publications : pub.name => pub }
  name          = each.value.name
  publish_param = each.value.ops
  tables        = each.value.type == "filtered" ? lookup(each.value, "tables", null) : null
  all_tables    = each.value.type == "all" ? true : null
}
```

---

## **📌 Choosing Between Python CLI & Terraform**
| Feature | Python CLI | Terraform |
|---------|------------|------------|
| **Control Over Replication Objects** | ✅ Yes | ✅ Yes |
| **Declarative Approach** | ❌ No | ✅ Yes |
| **Schema-Level Publications** | ✅ Yes | ❌ No |
| **Granular Object Updates** | ✅ Yes | ✅ Yes |
| **Integration with CI/CD** | ✅ Yes | ✅ Yes |
| **Maintenance Overhead** | ⚠️ Higher | ✅ Lower |

### **💡 Recommendation**
- **If you need flexibility**, custom logic, and schema-level publications → **Use the Python CLI**
- **If you want simplicity and declarative control** → **Use Terraform**

---

## **📢 Final Thoughts**
This project was built to **solve a real-world problem**—managing **CDC replication slots and publications** in a structured way. 

**Key takeaways:**
- **Infrastructure-as-Code (IAC) matters.** Terraform ensures **repeatability and consistency**.
- **Schema-level publications are a Python advantage.** Terraform doesn’t natively support `FOR TABLES IN SCHEMA` yet.
- **Makefiles simplify workflows.** Running `make setup` abstracts complex setup steps into one command.

🔗 **Full Source Code:** [GitHub Repo](https://github.com/your-org/pg-cdc-manager)

---

### **📢 Some Cool Next Steps**
- **[ ] Add CI/CD integration for automatic Terraform validation**
- **[ ] Explore Debezium integration for streaming CDC events**
