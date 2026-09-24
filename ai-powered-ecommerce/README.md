# Northstar Market: AI-powered e-commerce

A server-rendered Django storefront with a relational catalogue, persistent cart, atomic checkout, customer accounts, staff operations, and an explainable recommendation engine. The frontend uses Django templates, HTML, CSS, and Vanilla JavaScript only.

## Stack and layout

- Python 3.11+, Django 5.2, PostgreSQL 14+ (`psycopg` driver)
- Django templates, responsive CSS, Vanilla JavaScript
- `config/`: settings and URL/WSGI/ASGI entry points
- `store/`: persistence, validation, request handlers, commerce services, admin registration
- `templates/store/`, `static/`: server-rendered pages and assets
- `docs/`: API contract, ER diagram, recommendation design, setup

## Run locally

On Windows, run `start.bat` from Explorer or a terminal. With no `.env`, it starts a local SQLite demo; pass another port as an argument when needed, for example `start.bat 8001`. To use PostgreSQL, create `.env` from `.env.example`, set its database credentials, then run `start.bat`.

See [docs/SETUP.md](docs/SETUP.md) for manual setup. In short: install `requirements.txt`, prepare PostgreSQL, run migrations, optionally load demo data, create a staff account, and start the Django server.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

## Data model

Django's built-in `User` handles credentials and staff authorization. `Category` and `Product` describe the catalogue. `Cart` and `CartItem` support customer carts and anonymous session carts. `Order` and `OrderItem` preserve checkout totals and purchase-time prices. `UserInteraction` stores product views, category searches, cart additions, purchases, and recommendation clicks. See [docs/ERD.mmd](docs/ERD.mmd).

## Main workflows

- Register, login, logout, product browsing/search/category filters, and paginated catalogue.
- Cart quantities are checked against stock. Checkout locks relevant rows in a database transaction, calculates prices on the server, creates order snapshots, decrements inventory, records purchases, and empties the cart.
- Customers see only their own order history and details. Staff-only `/manage/` screens manage products, categories, and order statuses. Django admin is also enabled at `/admin/`.
- Recommendations combine weighted behavioral category affinity, same-category similarity, and recent popularity. See [docs/AI_RECOMMENDATION.md](docs/AI_RECOMMENDATION.md).

## API and validation

See [docs/API.md](docs/API.md) for the JSON recommendation endpoint and click tracking. Other commerce workflows use CSRF-protected Django form posts. Inputs use Django forms and model validators; customer order access and staff operations are checked on the server.

## Verification

Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`. Use `python manage.py collectstatic --noinput` for a production static build. Configure `DEBUG=False`, a strong `SECRET_KEY`, HTTPS, and a production-grade static/media host before deployment.

## Demo data

`python manage.py seed_demo` idempotently creates example categories and products. It does not create users or fake customer interactions. Create staff separately with `createsuperuser`; normal use generates recommendation signals organically.

## Limitations

No real payment gateway, shipment integration, product image upload, or external LLM is included. The recommendation implementation is an explainable ranking baseline; recommendation quality depends on observed traffic.
