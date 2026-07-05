"""
Unit tests for the Inventory Management API.

Run with: pytest -v
"""

import sys
import os
from unittest.mock import patch, Mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
from database import inventory as shared_inventory


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_inventory():
    """Snapshot and restore the in-memory inventory around every test
    so tests don't leak state into each other."""
    original = [item.copy() for item in shared_inventory]
    yield
    shared_inventory.clear()
    shared_inventory.extend(original)


# ---------------------------------------------------------------------------
# GET /inventory
# ---------------------------------------------------------------------------

def test_get_all_inventory(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == len(shared_inventory)


# ---------------------------------------------------------------------------
# GET /inventory/<id>
# ---------------------------------------------------------------------------

def test_get_single_item_found(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == 1
    assert data["product_name"] == "Organic Almond Milk"


def test_get_single_item_not_found(client):
    response = client.get("/inventory/9999")
    assert response.status_code == 404
    assert "error" in response.get_json()


# ---------------------------------------------------------------------------
# POST /inventory
# ---------------------------------------------------------------------------

def test_create_item_success(client):
    payload = {"product_name": "New Item", "brands": "TestBrand", "price": 1.99, "quantity": 5}
    response = client.post("/inventory", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["product_name"] == "New Item"
    assert "id" in data
    # confirm it was actually added to the shared inventory list
    assert any(item["id"] == data["id"] for item in shared_inventory)


def test_create_item_missing_name(client):
    response = client.post("/inventory", json={"brands": "NoName"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_item_no_body(client):
    response = client.post("/inventory")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# PATCH /inventory/<id>
# ---------------------------------------------------------------------------

def test_update_item_success(client):
    response = client.patch("/inventory/1", json={"price": 5.55, "quantity": 100})
    assert response.status_code == 200
    data = response.get_json()
    assert data["price"] == 5.55
    assert data["quantity"] == 100


def test_update_item_not_found(client):
    response = client.patch("/inventory/9999", json={"price": 5.55})
    assert response.status_code == 404


def test_update_item_no_body(client):
    response = client.patch("/inventory/1")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /inventory/<id>
# ---------------------------------------------------------------------------

def test_delete_item_success(client):
    response = client.delete("/inventory/1")
    assert response.status_code == 200
    assert not any(item["id"] == 1 for item in shared_inventory)


def test_delete_item_not_found(client):
    response = client.delete("/inventory/9999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /inventory/lookup (mocked external API)
# ---------------------------------------------------------------------------

def test_lookup_missing_params(client):
    response = client.get("/inventory/lookup")
    assert response.status_code == 400


def test_lookup_success_by_barcode(client):
    mock_response = Mock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {
        "status": 1,
        "product": {
            "product_name": "Mock Product",
            "brands": "MockBrand",
            "code": "1234567890123",
            "ingredients_text": "water, sugar",
            "nutriscore_grade": "b",
            "image_url": "http://example.com/img.jpg",
        },
    }
    with patch("app.requests.get", return_value=mock_response):
        response = client.get("/inventory/lookup?barcode=1234567890123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["product_name"] == "Mock Product"


def test_lookup_not_found(client):
    mock_response = Mock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {"status": 0}
    with patch("app.requests.get", return_value=mock_response):
        response = client.get("/inventory/lookup?barcode=0000000000000")
    assert response.status_code == 404


def test_lookup_api_failure(client):
    import requests as requests_module
    with patch("app.requests.get", side_effect=requests_module.ConnectionError):
        response = client.get("/inventory/lookup?barcode=1234567890123")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /inventory/<id>/enrich (mocked external API)
# ---------------------------------------------------------------------------

def test_enrich_item_success(client):
    mock_response = Mock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {
        "status": 1,
        "product": {
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "code": "0025293001165",
            "ingredients_text": "Filtered water, almonds, cane sugar",
            "nutriscore_grade": "c",
            "image_url": "http://example.com/almond.jpg",
        },
    }
    with patch("app.requests.get", return_value=mock_response):
        response = client.post("/inventory/1/enrich")
    assert response.status_code == 200
    data = response.get_json()
    assert data["nutriscore_grade"] == "c"
    assert data["image_url"] == "http://example.com/almond.jpg"


def test_enrich_item_not_found(client):
    response = client.post("/inventory/9999/enrich")
    assert response.status_code == 404