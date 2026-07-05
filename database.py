"""
In-memory mock database for the Inventory Management System.

Each item is a dict resembling a flattened OpenFoodFacts "product" object,
plus the store-specific fields (id, price, quantity) that OpenFoodFacts
does not track.
"""

# Simple auto-incrementing counter to hand out new IDs
_next_id = 5

inventory = [
    {
        "id": 1,
        "product_name": "Organic Almond Milk",
        "brands": "Silk",
        "barcode": "0025293001165",
        "ingredients_text": "Filtered water, almonds, cane sugar, sea salt, "
                             "sunflower lecithin, vitamin A palmitate, vitamin D2.",
        "price": 3.99,
        "quantity": 42,
        "nutriscore_grade": None,
        "image_url": None,
    },
    {
        "id": 2,
        "product_name": "Peanut Butter Crunchy",
        "brands": "Skippy",
        "barcode": "0037600110152",
        "ingredients_text": "Roasted peanuts, sugar, hydrogenated vegetable "
                             "oil, salt.",
        "price": 4.49,
        "quantity": 30,
        "nutriscore_grade": None,
        "image_url": None,
    },
    {
        "id": 3,
        "product_name": "Sparkling Water - Lime",
        "brands": "LaCroix",
        "barcode": "0017082002105",
        "ingredients_text": "Carbonated water, natural lime flavor.",
        "price": 5.99,
        "quantity": 60,
        "nutriscore_grade": None,
        "image_url": None,
    },
    {
        "id": 4,
        "product_name": "Whole Wheat Pasta",
        "brands": "Barilla",
        "barcode": "0076808501867",
        "ingredients_text": "Whole wheat flour.",
        "price": 2.29,
        "quantity": 75,
        "nutriscore_grade": None,
        "image_url": None,
    },
]


def get_next_id():
    """Return the next available id and increment the internal counter."""
    global _next_id
    current = _next_id
    _next_id += 1
    return current