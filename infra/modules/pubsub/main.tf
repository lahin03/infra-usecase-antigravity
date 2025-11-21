variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "topics" {
  description = "Map of topics to create"
  type        = map(object({
    name = string
  }))
  default = {}
}

variable "dead_letter_topic" {
  description = "Name of the dead letter topic"
  type        = string
  default     = "dead-letter-topic"
}

resource "google_pubsub_topic" "dead_letter" {
  name    = var.dead_letter_topic
  project = var.project_id
}

resource "google_pubsub_topic" "topic" {
  for_each = var.topics
  name     = each.value.name
  project  = var.project_id
}

output "topic_ids" {
  value = { for k, v in google_pubsub_topic.topic : k => v.id }
}

output "topic_names" {
  value = { for k, v in google_pubsub_topic.topic : k => v.name }
}

output "dead_letter_topic_id" {
  value = google_pubsub_topic.dead_letter.id
}
