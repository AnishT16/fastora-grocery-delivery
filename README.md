# Fastora

Fastora is a quick-commerce grocery delivery web application built with Django and Django REST Framework. The application supports product browsing, cart management, inventory tracking, scheduled and express order delivery, payment handling, and customer memberships.

## Tech Stack

- Backend: Python, Django, Django REST Framework
- Database: PostgreSQL
- Frontend: Django Templates, HTML5, CSS3, JavaScript
- Authentication: Django Session Authentication and Token-based API Authentication

## Key Features

- User authentication with roles (customer, delivery partner, dispatcher, staff)
- Product catalog organized by categories (groceries, fruits, beauty, electronics, pharmacy, etc.)
- Shopping cart and checkout with real-time stock reservations
- Delivery slot management and neighbourhood order pooling
- Payment processing for Cash on Delivery (COD) and online payments
- Fastora Plus membership plans with delivery discounts and fee waivers
- Admin reporting dashboard for delivery metrics and order statistics

## Project Structure

```
Fastora/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # User management, roles, and profiles
│   │   ├── carts/          # Shopping cart logic
│   │   ├── delivery/       # Delivery zones, slots, pricing, and batch pooling
│   │   ├── inventory/      # Stock tracking and reservations
│   │   ├── memberships/    # Customer subscription plans
│   │   ├── orders/         # Order creation and fulfillment
│   │   ├── payment/        # Payment processing and COD configuration
│   │   └── products/       # Product catalog and categories
│   ├── fastora/            # Project settings and root URLs
│   ├── common/             # Shared custom exceptions
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── static/             # CSS, images, and static assets
│   └── templates/          # HTML templates
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- PostgreSQL database server running locally

### 2. Clone the repository and create a virtual environment

```bash
git clone <repository-url>
cd Fastora/backend
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Database configuration

Ensure PostgreSQL is running and create a database named `fastora_db`:

```sql
CREATE DATABASE fastora_db;
```

Update database credentials in `backend/fastora/settings.py` if your PostgreSQL username or password differs from the defaults (`postgres` / `postgres`).

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.
