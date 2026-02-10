terraform {
  cloud {
    organization = "iqbalhakim"

    workspaces {
      name = "infra-myblog"
    }
  }
}
