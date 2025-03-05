publications = [
  {
    name   = "cdc_pub"
    ops    = ["insert", "update", "delete"]
    type   = "filtered"
    tables = ["bookies.bets", "bookies.transactions", "sims.sessions"]
  },
  {
    name   = "cdc_pub_2"
    ops    = ["insert", "update", "delete"]
    type   = "filtered"
    tables = ["bookies.users", "sims.games", "sims.players", "nasa.missions", "nasa.spacecrafts"]
  },
  {
    name   = "cdc_pub_3"
    ops    = ["delete"]
    type   = "all"
  }
]

replication_slots = [
  {
    name           = "cdc_slot"
    output_plugin = "pgoutput"
  },
  {
    name           = "cdc_slot_2"
    output_plugin = "pgoutput"
  },
  {
    name           = "cdc_slot_3"
    output_plugin = "pgoutput"
  }
]


db_host     = "localhost"
db_name     = "postgres"
db_username = "postgres"
db_password = "postgres"
