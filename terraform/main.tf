
resource "postgresql_publication" "publications" {
  for_each = { for pub in var.publications : pub.name => pub }

  name          = each.value.name
  publish_param = each.value.ops

  # Set tables only for "filtered" type, otherwise null
  tables = each.value.type == "filtered" ? lookup(each.value, "tables", null) : null

  # Set all_tables only for "all" type, otherwise null
  all_tables = each.value.type == "all" ? true : null
}


resource "postgresql_replication_slot" "slots" {
  for_each = { for slot in var.replication_slots : slot.name => slot }

  name          = each.value.name
  plugin        = each.value.output_plugin
}