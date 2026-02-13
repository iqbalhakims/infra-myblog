terraform {
  cloud {
    organization = "iqbal-hakim"

    workspaces {
      name = "infra-myblog"
    }
  }
}
