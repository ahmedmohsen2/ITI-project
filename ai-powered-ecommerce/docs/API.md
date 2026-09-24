# JSON API

All endpoints use the Django session and CSRF protection. Errors use normal HTTP status codes. Product prices are returned as decimal strings.

## `GET /api/recommendations/`

Returns three arrays: `personalized`, `trending`, and `similar`. Each product contains `id`, `name`, `slug`, `price`, `image_url`, and `reason`. Anonymous visitors get trending and cold-start recommendations; authenticated users receive personalization based on their own recorded events.

## `POST /api/recommendations/<product_id>/click/`

Records a recommendation click for the current user or browser session. Send the session cookie and `X-CSRFToken` header. Response: `{"ok": true}`.

## Server-rendered workflows

`POST /cart/add/<product_id>/`, `POST /cart/item/<item_id>/update/`, `POST /cart/item/<item_id>/remove/`, and `POST /checkout/` are the cart and order mutation routes. Django forms handle registration, sign-in, and staff catalog/status changes.
