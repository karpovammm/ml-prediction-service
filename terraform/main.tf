# Terraform configuration
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "= 0.105.0"
    }
  }
}

variable "pm_endpoint" {
  type    = string
  default = "https://10.10.10.1:8006"
}

variable "template_file_id" {
  type    = string
  default = "local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
}

provider "proxmox" {
  endpoint = var.pm_endpoint
  insecure = true
}

locals {
  servers = {
    db = {
      id       = 210
      hostname = "db-lab6"
      ip       = "10.10.10.21"
      ram      = 1024
      disk     = 6
    }
    app = {
      id       = 211
      hostname = "app-lab6"
      ip       = "10.10.10.22"
      ram      = 2048
      disk     = 10
    }
  }
}

resource "proxmox_virtual_environment_container" "server" {
  for_each = local.servers

  node_name    = "pve-lab"
  vm_id        = each.value.id
  unprivileged = true
  started      = true
  tags         = sort([each.key, "lab6", "ml-project"])

  cpu {
    cores = 2
  }

  memory {
    dedicated = each.value.ram
    swap      = 512
  }

  disk {
    datastore_id = "local-lvm"
    size         = each.value.disk
  }

  operating_system {
    template_file_id = var.template_file_id
    type             = "ubuntu"
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr1"
  }

  initialization {
    hostname = each.value.hostname

    ip_config {
      ipv4 {
        address = "${each.value.ip}/24"
        gateway = "10.10.10.1"
      }
    }

    user_account {
      keys = [trimspace(file(pathexpand("~/.ssh/lab6_ansible.pub")))]
    }
  }

  lifecycle {
    # Флаги для Docker задаёт администратор узла Proxmox на этапе 7.
    ignore_changes = [features]
  }
}

output "lab6_addresses" {
  value = { for role, server in local.servers : role => server.ip }
}
