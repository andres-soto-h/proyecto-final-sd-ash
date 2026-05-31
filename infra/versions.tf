terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }

  # Backend local por defecto. Para state remoto, descomentar y crear el storage del backend:
  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate"
  #   storage_account_name = "sttfstatefraud"
  #   container_name       = "tfstate"
  #   key                  = "fraud-detection.tfstate"
  # }
}
