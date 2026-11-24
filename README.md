# ShopFlow BIOMedical

ShopFlow BIOMedical is a full-stack inventory and order dashboard built with Django REST Framework and React. It synchronizes Shopify products, inventory variants, and orders into a local SQLite database and provides a Vite-powered dashboard for reviewing catalog and stock information.

## Features

- JWT-based account registration and login
- Shopify product and variant synchronization
- Shopify order synchronization
- Inventory levels and configurable minimum stock values
- Low-stock and out-of-stock views
- Shopify webhook receiving, verification, registration, and queued processing
- React dashboard for products, inventory, orders, overview metrics, and Shopify connection status
- Django admin interface

## Tech stack

**Backend**

- Python
- Django 5.2
- Django REST Framework
- Simple JWT
- SQLite
- Shopify Admin GraphQL API

**Frontend**

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios

## Project structure

```text
shopflow-BIOMedical/
├── apps/
│   ├── accounts/       # User registration and JWT authentication
│   ├── orders/         # Orders and order items
│   ├── products/       # Products, variants, and stock thresholds
│   └── shopify/        # Shopify API client, sync, and webhooks
├── config/             # Django project settings and root URLs
├── frontend/           # React and Vite dashboard
├── db.sqlite3          # Local SQLite database
├── manage.py
└── requirements.txt
```

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- A Shopify store for Shopify integration features

## Backend setup

From the repository root, create and activate a virtual environment.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Apply database migrations and create an administrator account:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Start the Django development server:

```powershell
python manage.py runserver
```

The backend runs at `http://127.0.0.1:8000/`.

## Frontend setup

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

The dashboard runs at `http://localhost:5173/` by default. Vite proxies `/api` requests to `http://127.0.0.1:8000`.

To build the frontend for deployment:

```powershell
npm run build
```

## Environment variables

Create environment variables in PowerShell before starting Django. The following Shopify variables are required for Shopify API operations:

```powershell
$env:SHOPIFY_SHOP="your-store.myshopify.com"
$env:SHOPIFY_CLIENT_ID="your-shopify-client-id"
$env:SHOPIFY_CLIENT_SECRET="your-shopify-client-secret"
$env:SHOPIFY_API_VERSION="2026-10"
```

Optional Django settings:

| Variable | Default | Description |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Development-only key | Django secret key; set a strong value in production |
| `DJANGO_DEBUG` | `true` | Set to `false` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated allowed hostnames |
| `SHOPIFY_WEBHOOK_BASE_URL` | Empty | Public HTTPS base URL used when registering webhooks |

Frontend environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Django target used by the Vite development proxy |
| `VITE_API_BASE_URL` | `/api` | API base URL used by the built frontend |

For example:

```powershell
$env:BACKEND_URL="http://127.0.0.1:8000"
cd frontend
npm run dev
```

For a deployment using a separate API domain:

```powershell
$env:VITE_API_BASE_URL="https://api.example.com/api"
npm run build
```

## Shopify setup

After configuring the Shopify environment variables, test the connection through the dashboard or by sending a POST request:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/shopify/test-connection/" -Method Post
```

Synchronize existing Shopify products and variants:

```powershell
python manage.py sync_shopify_products
```

Shopify orders and products can also be synchronized through the application's integration services as implemented by the webhook handlers.

### Webhooks

Set a public HTTPS callback base URL before registering webhooks:

```powershell
$env:SHOPIFY_WEBHOOK_BASE_URL="https://your-public-domain.example"
python manage.py register_shopify_webhooks
```

The application registers these Shopify topics:

- `products/create`
- `products/update`
- `products/delete`
- `inventory_levels/update`
- `orders/create`

The callback endpoint is:

```text
https://your-public-domain.example/api/shopify/webhooks/
```

Received events are stored in the database. Process pending events once:

```powershell
python manage.py process_shopify_webhooks
```

Run the processor continuously:

```powershell
python manage.py process_shopify_webhooks --watch --interval 5 --limit 10
```

## API overview

| Method | Endpoint | Authentication |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Public |
| `POST` | `/api/auth/login/` | Public |
| `POST` | `/api/auth/token/refresh/` | Public |
| `GET` | `/api/products/` | Public |
| `GET` | `/api/products/variants/` | Public |
| `GET` | `/api/products/variants/low-stock/` | Public |
| `GET` | `/api/products/variants/out-of-stock/` | Public |
| `PATCH` | `/api/products/variants/{id}/minimum-stock/` | Admin |
| `GET` | `/api/orders/` | Public |
| `POST` | `/api/shopify/test-connection/` | Public |
| `POST` | `/api/shopify/webhooks/` | Shopify HMAC |

### Authentication

Obtain a JWT access and refresh token:

```powershell
$body = @{
    username = "your-username"
    password = "your-password"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method Post -Body $body -ContentType "application/json"
```

Send the access token for protected admin endpoints:

```text
Authorization: Bearer <access-token>
```

## Testing

Run the Django test suite:

```powershell
python manage.py test
```

The repository contains unit tests for Shopify product and order synchronization, webhook security, and integration helpers.

Shopify integration tests are skipped unless enabled:

```powershell
$env:RUN_SHOPIFY_INTEGRATION_TESTS="1"
python manage.py test apps.shopify.tests.test_shopify_integration
```

## Production notes

- Replace `DJANGO_SECRET_KEY` with a persistent secret.
- Set `DJANGO_DEBUG=false`.
- Restrict `DJANGO_ALLOWED_HOSTS` to production domains.
- Replace SQLite with a managed database if the deployment requires concurrent writes or high availability.
- Use HTTPS for the Shopify webhook base URL.
- Configure Django and Vite static/deployment hosting separately.
- Keep Shopify credentials in environment variables or a secret manager; do not commit them to source control.
