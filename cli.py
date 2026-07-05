"""
CLI frontend for the Inventory Management System.

Talks to the Flask API over HTTP (make sure `python app.py` is running
in another terminal first, on http://127.0.0.1:5000).
"""

import requests

BASE_URL = "http://127.0.0.1:5000"


def print_item(item):
    print(f"  ID: {item.get('id')}")
    print(f"  Name: {item.get('product_name')}")
    print(f"  Brand: {item.get('brands')}")
    print(f"  Barcode: {item.get('barcode')}")
    print(f"  Price: ${item.get('price')}")
    print(f"  Quantity: {item.get('quantity')}")
    print(f"  Ingredients: {item.get('ingredients_text')}")
    print(f"  Nutri-Score: {item.get('nutriscore_grade')}")
    print("-" * 40)


def safe_request(method, url, **kwargs):
    """Wrap requests calls with basic error handling for network/API failures."""
    try:
        response = requests.request(method, url, timeout=5, **kwargs)
        return response
    except requests.ConnectionError:
        print("Error: Could not connect to the API. Is 'python app.py' running?")
        return None
    except requests.Timeout:
        print("Error: The request timed out. Please try again.")
        return None
    except requests.RequestException as e:
        print(f"Error: An unexpected request error occurred: {e}")
        return None


def view_all_items():
    response = safe_request("GET", f"{BASE_URL}/inventory")
    if response is None:
        return
    if response.status_code == 200:
        items = response.json()
        if not items:
            print("Inventory is empty.")
        for item in items:
            print_item(item)
    else:
        print(f"Error fetching inventory: {response.status_code}")


def view_item_details():
    item_id = input("Enter item ID: ").strip()
    if not item_id.isdigit():
        print("Error: ID must be a number.")
        return
    response = safe_request("GET", f"{BASE_URL}/inventory/{item_id}")
    if response is None:
        return
    if response.status_code == 200:
        print_item(response.json())
    elif response.status_code == 404:
        print(f"No item found with ID {item_id}.")
    else:
        print(f"Error: {response.status_code}")


def add_new_item():
    name = input("Product name: ").strip()
    if not name:
        print("Error: Product name is required.")
        return
    brand = input("Brand (optional): ").strip()
    barcode = input("Barcode (optional): ").strip()

    price_input = input("Price: ").strip()
    quantity_input = input("Quantity: ").strip()
    try:
        price = float(price_input) if price_input else 0.0
        quantity = int(quantity_input) if quantity_input else 0
    except ValueError:
        print("Error: Price must be a number and quantity must be an integer.")
        return

    payload = {
        "product_name": name,
        "brands": brand,
        "barcode": barcode,
        "price": price,
        "quantity": quantity,
    }
    response = safe_request("POST", f"{BASE_URL}/inventory", json=payload)
    if response is None:
        return
    if response.status_code == 201:
        new_item = response.json()
        print("Item added successfully:")
        print_item(new_item)

        if barcode:
            enrich_choice = input("Try to enrich this item from OpenFoodFacts? (y/n): ").strip().lower()
            if enrich_choice == "y":
                enrich_item(item_id=new_item["id"])
    else:
        print(f"Error adding item: {response.status_code} - {response.text}")


def update_item():
    item_id = input("Enter item ID to update: ").strip()
    if not item_id.isdigit():
        print("Error: ID must be a number.")
        return

    print("Leave a field blank to keep it unchanged.")
    price_input = input("New price: ").strip()
    quantity_input = input("New quantity: ").strip()

    payload = {}
    if price_input:
        try:
            payload["price"] = float(price_input)
        except ValueError:
            print("Error: Price must be a number. Skipping price update.")
    if quantity_input:
        try:
            payload["quantity"] = int(quantity_input)
        except ValueError:
            print("Error: Quantity must be an integer. Skipping quantity update.")

    if not payload:
        print("No valid changes provided.")
        return

    response = safe_request("PATCH", f"{BASE_URL}/inventory/{item_id}", json=payload)
    if response is None:
        return
    if response.status_code == 200:
        print("Item updated successfully:")
        print_item(response.json())
    elif response.status_code == 404:
        print(f"No item found with ID {item_id}.")
    else:
        print(f"Error updating item: {response.status_code}")


def delete_item():
    item_id = input("Enter item ID to delete: ").strip()
    if not item_id.isdigit():
        print("Error: ID must be a number.")
        return
    confirm = input(f"Are you sure you want to delete item {item_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return
    response = safe_request("DELETE", f"{BASE_URL}/inventory/{item_id}")
    if response is None:
        return
    if response.status_code == 200:
        print(response.json().get("message"))
    elif response.status_code == 404:
        print(f"No item found with ID {item_id}.")
    else:
        print(f"Error deleting item: {response.status_code}")


def find_item_on_api():
    print("Search OpenFoodFacts by:")
    print("  1. Barcode")
    print("  2. Product name")
    choice = input("Choose an option (1/2): ").strip()

    params = {}
    if choice == "1":
        params["barcode"] = input("Enter barcode: ").strip()
    elif choice == "2":
        params["name"] = input("Enter product name: ").strip()
    else:
        print("Invalid choice.")
        return

    response = safe_request("GET", f"{BASE_URL}/inventory/lookup", params=params)
    if response is None:
        return
    if response.status_code == 200:
        print("Product found on OpenFoodFacts:")
        print_item(response.json())
    elif response.status_code == 404:
        print("Product not found on OpenFoodFacts.")
    else:
        print(f"Error: {response.status_code}")


def enrich_item(item_id=None):
    if item_id is None:
        item_id = input("Enter item ID to enrich from OpenFoodFacts: ").strip()
        if not item_id.isdigit():
            print("Error: ID must be a number.")
            return

    response = safe_request("POST", f"{BASE_URL}/inventory/{item_id}/enrich")
    if response is None:
        return
    if response.status_code == 200:
        print("Item enriched successfully:")
        print_item(response.json())
    elif response.status_code == 404:
        print("Could not enrich: item or matching OpenFoodFacts product not found.")
    else:
        print(f"Error: {response.status_code}")


MENU = """
==== Inventory Management CLI ====
1. View all inventory
2. View item details
3. Add new item
4. Update item (price/stock)
5. Delete item
6. Find item on OpenFoodFacts API
7. Enrich an existing item from OpenFoodFacts
8. Exit
"""

ACTIONS = {
    "1": view_all_items,
    "2": view_item_details,
    "3": add_new_item,
    "4": update_item,
    "5": delete_item,
    "6": find_item_on_api,
    "7": enrich_item,
}


def main():
    print("Welcome to the Inventory Management CLI.")
    print(f"Connecting to API at {BASE_URL} ...")
    while True:
        print(MENU)
        choice = input("Select an option (1-8): ").strip()
        if choice == "8":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid option, please choose 1-8.")
            continue
        action()


if __name__ == "__main__":
    main()