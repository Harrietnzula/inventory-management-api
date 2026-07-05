"""
Flask REST API for the Inventory Management System.

Routes:
    GET    /inventory                -> list all items
    GET    /inventory/<id>           -> get a single item
    POST   /inventory                -> create a new item
    PATCH  /inventory/<id>           -> update an existing item
    DELETE /inventory/<id>           -> delete an item
    GET    /inventory/lookup         -> look up a product on OpenFoodFacts by barcode or name
    POST   /inventory/<id>/enrich    -> merge OpenFoodFacts data into an existing item
"""

import requests
from flask import Flask, jsonify, request

from database import inventory, get_next_id

app = Flask(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org"
USER_AGENT = "InventoryManagementLab/1.0 (student@example.com)"


def find_item(item_id):
    """Helper: return the item dict with the given id, or None."""
    return next((item for item in inventory if item["id"] == item_id), None)


# ---------------------------------------------------------------------------
# CRUD routes
# ---------------------------------------------------------------------------

@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": f"Item with id {item_id} not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def create_item():
    data = request.get_json(silent=True)
    if not data or "product_name" not in data:
        return jsonify({"error": "Request body must include at least 'product_name'"}), 400

    new_item = {
        "id": get_next_id(),
        "product_name": data.get("product_name"),
        "brands": data.get("brands", ""),
        "barcode": data.get("barcode", ""),
        "ingredients_text": data.get("ingredients_text", ""),
        "price": data.get("price", 0.0),
        "quantity": data.get("quantity", 0),
        "nutriscore_grade": data.get("nutriscore_grade"),
        "image_url": data.get("image_url"),
    }
    inventory.append(new_item)
    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": f"Item with id {item_id} not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must contain fields to update"}), 400

    # Only allow known fields to be updated; ignore/reject id changes
    updatable_fields = {
        "product_name", "brands", "barcode", "ingredients_text",
        "price", "quantity", "nutriscore_grade", "image_url",
    }
    for key, value in data.items():
        if key in updatable_fields:
            item[key] = value

    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": f"Item with id {item_id} not found"}), 404

    inventory.remove(item)
    return jsonify({"message": f"Item {item_id} deleted successfully"}), 200


# ---------------------------------------------------------------------------
# External API integration (OpenFoodFacts)
# ---------------------------------------------------------------------------

def fetch_from_openfoodfacts(barcode=None, name=None):
    """
    Query OpenFoodFacts by barcode (preferred, exact) or by product name
    (search, returns the first match). Returns a dict of product fields
    or None if nothing was found / the request failed.
    """
    headers = {"User-Agent": USER_AGENT}

    try:
        if barcode:
            url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json"
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != 1:
                return None
            product = data["product"]
        elif name:
            url = f"{OFF_BASE_URL}/cgi/search.pl"
            params = {"search_terms": name, "search_simple": 1, "json": 1, "page_size": 1}
            resp = requests.get(url, headers=headers, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            products = data.get("products", [])
            if not products:
                return None
            product = products[0]
        else:
            return None
    except requests.RequestException:
        return None

    return {
        "product_name": product.get("product_name", ""),
        "brands": product.get("brands", ""),
        "barcode": product.get("code", barcode or ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "nutriscore_grade": product.get("nutriscore_grade"),
        "image_url": product.get("image_url"),
    }


@app.route("/inventory/lookup", methods=["GET"])
def lookup_product():
    barcode = request.args.get("barcode")
    name = request.args.get("name")

    if not barcode and not name:
        return jsonify({"error": "Provide a 'barcode' or 'name' query parameter"}), 400

    result = fetch_from_openfoodfacts(barcode=barcode, name=name)
    if result is None:
        return jsonify({"error": "Product not found on OpenFoodFacts"}), 404

    return jsonify(result), 200


@app.route("/inventory/<int:item_id>/enrich", methods=["POST"])
def enrich_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": f"Item with id {item_id} not found"}), 404

    result = fetch_from_openfoodfacts(barcode=item.get("barcode"), name=item.get("product_name"))
    if result is None:
        return jsonify({"error": "No matching product found on OpenFoodFacts to enrich with"}), 404

    # Only fill in fields that are currently empty, keep local price/quantity untouched
    for key, value in result.items():
        if value and not item.get(key):
            item[key] = value

    return jsonify(item), 200


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)