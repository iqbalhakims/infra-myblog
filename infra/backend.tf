terraform {
  cloud {
    organization = "iqbalhakims"

    workspaces {
      name = "infra-myblog"
    }
  }
}
