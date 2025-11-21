variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create"
  type        = map(string) # key: account_id, value: display_name
}

variable "project_roles" {
  description = "Map of list of roles to assign to service accounts"
  type        = map(list(string)) # key: account_id, value: list of roles
}

resource "google_service_account" "sa" {
  for_each     = var.service_accounts
  account_id   = each.key
  display_name = each.value
  project      = var.project_id
}

resource "google_project_iam_member" "roles" {
  for_each = {
    for pair in flatten([
      for sa_key, roles in var.project_roles : [
        for role in roles : {
          sa_key = sa_key
          role   = role
        }
      ]
    ]) : "${pair.sa_key}-${pair.role}" => pair
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.sa[each.value.sa_key].email}"
}

output "emails" {
  value = { for k, v in google_service_account.sa : k => v.email }
}
