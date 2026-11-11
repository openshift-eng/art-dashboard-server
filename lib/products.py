"""Product identities shared by release discovery and shipment validation."""
import re

PRODUCTS = {
    "openshift": {
        "id": "openshift", "name": "OpenShift", "description": "OpenShift Container Platform",
        "shipment_product": "ocp", "group_prefix": "openshift", "release_streams": True,
    },
    "acm": {
        "id": "acm", "name": "ACM", "description": "Advanced Cluster Management",
        "shipment_product": "rhacm2", "group_prefix": "acm", "release_streams": False,
    },
    "mce": {
        "id": "mce", "name": "MCE", "description": "Multicluster Engine",
        "shipment_product": "multicluster-engine", "group_prefix": "mce", "release_streams": False,
    },
}


def get_product(product_id):
    if product_id not in PRODUCTS:
        raise ValueError(f"Unsupported product: {product_id}")
    return PRODUCTS[product_id]


def product_for_group(group):
    for product in PRODUCTS.values():
        if re.fullmatch(rf"{re.escape(product['group_prefix'])}-\d+\.\d+", group or ""):
            return product
    raise ValueError(f"Unsupported release group: {group}")


def validate_product_group(product_id, group):
    product = get_product(product_id)
    if product_for_group(group)["id"] != product_id:
        raise ValueError(f"Group {group} does not belong to {product['name']}")
    return product


def version_key(value):
    """Sort dotted numeric versions first, then naturally ordered assembly labels."""
    match = re.fullmatch(r"(?:[a-z]+-)?(\d+(?:\.\d+)+)(.*)", value)
    if not match:
        label = tuple((1, int(part)) if part.isdigit() else (0, part) for part in re.split(r"(\d+)", value))
        return (), False, label
    numbers = tuple(int(part) for part in match.group(1).split("."))
    suffix = match.group(2)
    natural_suffix = tuple((1, int(part)) if part.isdigit() else (0, part) for part in re.split(r"(\d+)", suffix))
    return numbers, not bool(suffix), natural_suffix
