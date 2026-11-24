# Shopflow frontend

React dashboard for the Shopflow Django API.

## Run locally

1. Start the Django backend from the repository root:

   ```powershell
   python manage.py runserver
   ```

2. Install frontend dependencies and start Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Vite proxies `/api` requests to `http://127.0.0.1:8000` by default. To use a backend on a different address, set `BACKEND_URL` before starting the dev server. For a deployed frontend, set `VITE_API_BASE_URL` to the API base URL (for example, `https://api.example.com/api`).

## Available screens

- Overview: product and inventory counts, order summary, recent orders, and stock alerts.
- Products: searchable product catalog.
- Inventory: searchable stock levels with status filters.
- Orders: searchable Shopify orders and fulfillment status.
- Settings: Shopify connection test.

The read views use the backend's public endpoints. Shopify credentials remain configured on the backend.
