import requests
import yaml
from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.product_releases import (
    get_product_ga,
    get_product_groups,
    get_product_release,
    get_product_releases,
    get_products_overview,
)
from lib.products import PRODUCTS


def _respond(function, *args):
    try:
        return Response(function(*args))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except LookupError as exc:
        return Response({"error": str(exc)}, status=404)
    except (requests.RequestException, TypeError, yaml.YAMLError):
        return Response({"error": "Release data is temporarily unavailable. Please retry."}, status=502)


@api_view(["GET"])
def products(request):
    return Response(list(PRODUCTS.values()))


@api_view(["GET"])
def overview(request):
    return _respond(get_products_overview)


@api_view(["GET"])
def groups(request, product_id):
    return _respond(get_product_groups, product_id)


@api_view(["GET"])
def ga(request, product_id):
    return _respond(get_product_ga, product_id)


@api_view(["GET"])
def releases(request, product_id):
    return _respond(get_product_releases, product_id, request.query_params.get("group", ""))


@api_view(["GET"])
def release_detail(request, product_id):
    return _respond(get_product_release, product_id, request.query_params.get("group", ""), request.query_params.get("assembly", ""))
