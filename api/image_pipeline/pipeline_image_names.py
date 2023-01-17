from api import exceptions
from api.image_pipeline import pipeline_image_util
from typing import Dict, Tuple
from api.image_pipeline.classes import Github, Distgit, Brew, CDN, Delivery

VARIANT_BASE = "8Base-RHOSE"


# Driver functions
def pipeline_from_github(github_repo: str, version: str) -> Tuple[Dict[str, str], int]:
    """
    Function to list the GitHub repo, Brew package name, CDN repo name and delivery repo by getting the GitHub repo name as input.

    GitHub -> Distgit -> Brew -> CDN -> Delivery

    :param github_repo: Name of the GitHub repo we get as input. Eg: ironic-image
    :param version: OCP version
    :returns: Tuple containing the response payload as a dict and http status code as int
    """
    variant = f"{VARIANT_BASE}-{version}"

    if not pipeline_image_util.github_repo_is_available(github_repo):  # Check if the given GitHub repo actually exists
        # If incorrect GitHub name provided, no need to proceed.
        return {
                   "status": "error",
                   "payload": f"No github repo with name {github_repo} exists."
               }, 404
    # GitHub
    github_object = Github()
    github_object.openshift_version = version
    github_object.github_repo = github_repo
    github_object.upstream_github_url = f"https://github.com/openshift/{github_repo}"
    github_object.private_github_url = f"https://github.com/openshift-priv/{github_repo}"

    # GitHub -> Distgit
    distgit_repos = pipeline_image_util.github_to_distgit(github_repo, version)
    for distgit_repo_name in distgit_repos:
        # Distgit -> Delivery
        distgit_object = Distgit()
        distgit_object.distgit_repo_name = distgit_repo_name
        distgit_object.distgit_url = f"https://pkgs.devel.redhat.com/cgit/containers/{distgit_repo_name}"
        brew_object = pipeline_image_util.distgit_to_delivery(distgit_repo_name, version, variant)
        distgit_object.brew = brew_object

        github_object.distgit.append(distgit_object)

    return {
               "status": "success",
               "payload": github_object
           }, 200


def pipeline_from_distgit(distgit_repo_name, version) -> Tuple[Dict[str, str], int]:
    """
    Function to list the GitHub repo, Brew package name, CDN repo name and delivery repo by getting the distgit name as input.

    GitHub <- Distgit -> Brew -> CDN -> Delivery

    :param distgit_repo_name: Name of the distgit repo we get as input
    :param version: OCP version
    :returns: Tuple containing the response payload as a dict and http status code as int
    """
    variant = f"{VARIANT_BASE}-{version}"

    if not pipeline_image_util.distgit_is_available(
            distgit_repo_name):  # Check if the given distgit repo actually exists
        # If incorrect distgit name provided, no need to proceed.
        return {
                   "status": "error",
                   "payload": f"No distgit repo with name {distgit_repo_name} exists"
               }, 404

    # Distgit -> GitHub
    github_repo = pipeline_image_util.distgit_to_github(distgit_repo_name, version)
    github_object = Github()
    github_object.openshift_version = version
    github_object.github_repo = github_repo
    github_object.upstream_github_url = f"https://github.com/openshift/{github_repo}"
    github_object.private_github_url = f"https://github.com/openshift-priv/{github_repo}"

    distgit_object = Distgit()
    distgit_object.distgit_repo_name = distgit_repo_name
    distgit_object.distgit_url = f"https://pkgs.devel.redhat.com/cgit/containers/{distgit_repo_name}"

    brew_object = pipeline_image_util.distgit_to_delivery(distgit_repo_name, version, variant)

    distgit_object.brew = brew_object

    github_object.distgit.append(distgit_object)

    return {
               "status": "success",
               "payload": github_object
           }, 200


def pipeline_from_brew(brew_name, version) -> Tuple[Dict[str, str], int]:
    """
    Function to list the GitHub repo, Brew package name, CDN repo name and delivery repo by getting the brew name as input.

    GitHub <- Distgit <- Brew -> CDN -> Delivery

    :param brew_name: Name of the brew repo we get as input
    :param version: OCP version
    :returns: Tuple containing the response payload as a dict and http status code as int
    """
    variant = f"{VARIANT_BASE}-{version}"

    if not pipeline_image_util.brew_is_available(brew_name):  # Check if the given brew repo actually exists
        # If incorrect brew name provided, no need to proceed.
        return {
                   "status": "error",
                   "payload": f"No brew package with name {brew_name} exists."
               }, 404

    # Brew -> GitHub
    github_object, distgit_object, brew_object = pipeline_image_util.brew_to_github(brew_name, version)
    # Brew
    brew_id = pipeline_image_util.get_brew_id(brew_name)

    brew_object.brew_id = brew_id
    brew_object.brew_package_name = brew_name
    brew_object.brew_build_url = f"https://brewweb.engineering.redhat.com/brew/packageinfo?packageID={brew_id}"

    pipeline_image_util.brew_to_delivery(brew_name, variant, brew_object)

    distgit_object.brew = brew_object
    github_object.distgit.append(distgit_object)

    return {
               "status": "success",
               "payload": github_object
           }, 200


def pipeline_from_cdn(cdn_repo_name, version) -> Tuple[Dict[str, str], int]:
    """
    Function to list the GitHub repo, Brew package name, CDN repo name and delivery repo by getting the CDN name as input.

    GitHub <- Distgit <- Brew <- CDN -> Delivery

    :param cdn_repo_name: Name of the CDN repo we get as input
    :param version: OCP version
    :returns: Tuple containing the response payload as a dict and http status code as int
    """
    variant = f"{VARIANT_BASE}-{version}"

    if not pipeline_image_util.cdn_is_available(cdn_repo_name):  # Check if the given brew repo actually exists
        # If incorrect cdn repo provided, no need to proceed.
        return {
                   "status": "error",
                   "payload": f"No CDN repo with name {cdn_repo_name} exists."
               }, 404

    # CDN -> GitHub
    github_object, distgit_object, brew_object = pipeline_image_util.cdn_to_github(cdn_repo_name, version)

    # CDN
    cdn_object = pipeline_image_util.get_cdn_payload(cdn_repo_name, variant)

    # Keep the response JSON in the same format
    delivery_object = pipeline_image_util.cdn_to_delivery_payload(cdn_repo_name)
    cdn_object.delivery = delivery_object

    brew_object.cdn.append(cdn_object)
    distgit_object.brew = brew_object
    github_object.distgit.append(distgit_object)

    return {
               "status": "success",
               "payload": github_object
           }, 200


def pipeline_from_delivery(delivery_repo_name, version) -> Tuple[Dict[str, str], int]:
    """
    Function to list the GitHub repo, Brew package name, CDN repo name and delivery repo by getting the delivery repo name as input.

    GitHub <- Distgit <- Brew <- CDN <- Delivery

    :param delivery_repo_name: Name of the delivery repo we get as input
    :param version: OCP version
    :returns: Tuple containing the response payload as a dict and http status code as int
    """
    variant = f"{VARIANT_BASE}-{version}"

    if not pipeline_image_util.delivery_repo_is_available(
            delivery_repo_name):  # Check if the given Comet delivery repo actually exists
        # If incorrect delivery repo name provided, no need to proceed.

        return {
                   "status": "error",
                   "payload": f"No delivery repo with name {delivery_repo_name} exists"
               }, 404

    # Brew
    brew_name = pipeline_image_util.brew_from_delivery(delivery_repo_name)
    brew_id = pipeline_image_util.get_brew_id(brew_name)

    # Brew -> GitHub
    github_object, distgit_object, brew_object = pipeline_image_util.brew_to_github(brew_name, version)
    brew_object.brew_id = brew_id
    brew_object.brew_package_name = brew_name
    brew_object.brew_build_url = f"https://brewweb.engineering.redhat.com/brew/packageinfo?packageID={brew_id}"

    # Brew -> CDN
    cdn_repo_name = pipeline_image_util.brew_to_cdn_delivery(brew_name, variant, delivery_repo_name)
    cdn_object = pipeline_image_util.get_cdn_payload(cdn_repo_name, variant)

    # Delivery
    delivery_repo_id = pipeline_image_util.get_delivery_repo_id(delivery_repo_name)

    delivery_object = Delivery()
    delivery_object.delivery_repo_id = delivery_repo_id
    delivery_object.delivery_repo_name = delivery_repo_name
    delivery_object.delivery_repo_url = f"https://comet.engineering.redhat.com/containers/repositories/{delivery_repo_id}"

    cdn_object.delivery = delivery_object
    brew_object.cdn.append(cdn_object)
    distgit_object.brew = brew_object
    github_object.distgit.append(distgit_object)

    return {
               "status": "success",
               "payload": github_object
           }, 200
