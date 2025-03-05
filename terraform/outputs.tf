output "created_publications" {
  value = { for pub in postgresql_publication.publications : pub.name => pub.name }
}

output "created_replication_slots" {
  value = { for slot in postgresql_replication_slot.slots : slot.name => slot.name }
}
