# Inventory Management System

A Flask REST API + CLI tool for managing store inventory, with product
enrichment from the [OpenFoodFacts API](https://world.openfoodfacts.org).

## Features

- Full CRUD REST API for inventory items (Flask)
- Lookup and enrichment of items using real OpenFoodFacts product data
- Command-line interface for day-to-day inventory operations
- Unit test suite (pytest) covering all routes, including mocked external API calls

## Project Structure

```
inventory-api/
├── app.py              # Flask app + all routes
├── database.py         # In-memory mock database (list of dicts)
├── cli.py              # CLI frontend that talks to the API over HTTP
├── requirements.txt
├── tests/
│   └── test_app.py     # pytest suite
└── README.md
```

## Setup

1. Clone the repo and enter the project folder:
   ```bash
   git clone <your-repo-url>
   cd inventory-api
   ```
2. Create a virtual environment (recommended) and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the API

```bash
python app.py
```

The API will be available at `http://127.0.0.1:5000`.

## Running the CLI

In a **second terminal** (with the API still running):

```bash
python cli.py
```

Follow the on-screen menu to view, add, update, delete, or look up inventory items.

## Running Tests

```bash
pytest -v
```

All external OpenFoodFacts calls are mocked in the test suite, so tests run
offline and don't hit rate limits.

## API Reference

| Method | Route                        | Description                                             |
|--------|-------------------------------|----------------------------------------------------------|
| GET    | `/inventory`                  | List all inventory items                                  |
| GET    | `/inventory/<id>`              | Get a single item by ID                                   |
| POST   | `/inventory`                  | Create a new item (`product_name` required)                |
| PATCH  | `/inventory/<id>`              | Update one or more fields of an item                       |
| DELETE | `/inventory/<id>`              | Remove an item                                             |
| GET    | `/inventory/lookup?barcode=` or `?name=` | Look up a product on OpenFoodFacts without saving it |
| POST   | `/inventory/<id>/enrich`       | Fetch OpenFoodFacts data and merge it into an existing item |

### Example: creating an item

```bash
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Almond Milk", "brands": "Silk", "price": 3.99, "quantity": 20}'
```

### Example: looking up a product by barcode

```bash
curl "http://127.0.0.1:5000/inventory/lookup?barcode=3017620422003"
```

## Notes

- The database is an in-memory Python list (`database.py`) and resets every
  time the Flask server restarts. This is intentional for the scope of this lab.
- OpenFoodFacts requests use a custom `User-Agent` per their API guidelines,
  and results are gracefully handled if the product isn't found or the
  request fails (network errors, timeouts, rate limits).