class Github:
    def __init__(self):
        self.openshift_version = ""
        self.github_repo = ""
        self.upstream_github_url = ""
        self.private_github_url = ""
        self.distgit = []


class Distgit:
    def __init__(self):
        self.distgit_repo_name = ""
        self.distgit_url = ""
        self.brew = None


class Brew:
    def __init__(self):
        self.brew_id = 0
        self.brew_build_url = ""
        self.brew_package_name = ""
        self.bundle_component = ""
        self.bundle_distgit = ""
        self.payload_tag = ""
        self.cdn = []


class CDN:
    def __init__(self):
        self.cdn_repo_id = 0
        self.cdn_repo_name = ""
        self.cdn_repo_url = ""
        self.variant_name = ""
        self.variant_id = 0
        self.delivery = None


class Delivery:
    def __init__(self):
        self.delivery_repo_id = ""
        self.delivery_repo_name = ""
        self.delivery_repo_url = ""
