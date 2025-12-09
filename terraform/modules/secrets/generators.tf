# Generate random secret values if secret_keys is provided but secret_data is empty

resource "random_password" "secrets" {
  for_each = length(var.secret_data) == 0 && length(var.secret_keys) > 0 ? toset(var.secret_keys) : toset([])

  length  = var.secret_key_length
  special = true
}

locals {
  # Use provided secret_data or generate from secret_keys
  generated_secret_data = length(var.secret_data) > 0 ? var.secret_data : {
    for key in var.secret_keys : key => random_password.secrets[key].result
  }
}

