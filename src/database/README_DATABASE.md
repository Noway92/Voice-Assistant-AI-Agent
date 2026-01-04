# Restaurant Database - PostgreSQL Setup

This document describes the PostgreSQL database setup for the Voice Assistant AI Agent restaurant system. The database supports three main features: **reservations**, **orders**, and **general inquiries**.

## Database Structure

The database consists of the following tables:

### 1. **Client** (Customers)
Stores customer information for reservations and orders.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique client identifier |
| name | String(100) | Customer name |
| phone | String(20) | Customer phone (unique) |
| email | String(100) | Customer email (optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 2. **Table** (Restaurant Tables)
Stores restaurant table information for reservations.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique table identifier |
| table_number | Integer | Table number (unique) |
| capacity | Integer | Maximum number of seats |
| location | String(50) | Location (indoor/outdoor) |
| is_active | Boolean | Whether table is available |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 3. **Reservation** (Table Reservations)
Stores reservation information for customers.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique reservation identifier |
| client_id | Integer (FK) | Reference to Client table |
| table_id | Integer (FK) | Reference to Table table |
| reservation_date | Date | Reservation date |
| reservation_time | String(10) | Reservation time (HH:MM format) |
| num_guests | Integer | Number of guests |
| status | String(20) | Status: pending/confirmed/cancelled/completed |
| special_requests | Text | Special requests (optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 4. **MenuItem** (Menu Items)
Stores restaurant menu items for ordering.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique menu item identifier |
| name | String(200) | Menu item name |
| category | String(50) | Category (appetizer/main/dessert/drink) |
| description | Text | Item description |
| price | Float | Price in currency |
| available | Boolean | Whether item is available |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 5. **Order** (Customer Orders)
Stores order information for customers.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique order identifier |
| client_id | Integer (FK) | Reference to Client table |
| order_date | Date | Order date |
| status | String(20) | Status: pending/preparing/ready/completed/cancelled |
| total_price | Float | Order total |
| order_type | String(20) | Type: takeaway/delivery |
| special_instructions | Text | Special instructions (optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 6. **OrderItem** (Order Line Items)
Stores individual items within each order.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique order item identifier |
| order_id | Integer (FK) | Reference to Order table |
| menu_item_id | Integer (FK) | Reference to MenuItem table |
| quantity | Integer | Quantity ordered |
| unit_price | Float | Price per unit at time of order |
| special_requests | Text | Item-specific requests (optional) |
| created_at | Timestamp | Record creation time |

## Configuration

## Database Initialization

### 1. Initialize the Database
Creates all tables and initial data (run once on first setup).

```bash
python src/database/init_database.py
```

**What it does:**
- Tests database connection
- Creates all tables: Client, Table, Reservation, MenuItem, Order, OrderItem
- Populates 5 restaurant tables with different capacities (2, 4, 6, 2, 8 seats)
- Creates some sample menu items

### 2. View Database Contents
Display current database contents for debugging.

```bash
python src/database/view_database_contents.py
```

**What it does:**
- Shows all clients, tables, reservations, menu items, orders, and order items
- Displays counts and details for each table

### 3. Test Reservation Tools
Test reservation functionality.

```bash
python src/database/test_reservation_tools.py
```

**What it does:**
- Tests availability checking
- Tests reservation creation
- Tests reservation cancellation
- Tests viewing reservations

## Using the Tools

### Reservation Tools

Import the reservation tools:

```python
from src.agents.tools.reservation_tools import (
    check_availability_tool,
    make_reservation_tool,
    cancel_reservation_tool,
    view_reservations_tool
)
```

**Check Availability:**
```python
result = check_availability_tool("2025-11-30, 19:00, 4")
print(result)
```

**Make a Reservation:**
```python
result = make_reservation_tool("2025-11-30, 19:00, John Doe, 0612345678, 4, Window seat please")
print(result)
```

**Cancel a Reservation:**
```python
result = cancel_reservation_tool("2025-11-30, 19:00, John Doe")
print(result)
```

**View Reservations:**
```python
result = view_reservations_tool("2025-11-30")
print(result)
```

### Order Tools

Import the order tools:

```python
from src.agents.tools.order_tools_sql import (
    create_order_tool,
    add_item_tool,
    update_item_tool,
    remove_item_tool,
    view_order_tool,
    finalize_order_tool,
    check_status_tool,
    cancel_order_tool
)
```

**Create Order:**
```python
result = create_order_tool("John Smith", "0612345678", "takeaway")
# Returns: "Order #1 created for John Smith"
```

**Add Item to Order:**
```python
result = add_item_tool(1, "Pizza Margherita", 2, "extra cheese")
# Returns: "Added 1x Pizza Margherita to order"
```

**View Order:**
```python
result = view_order_tool(1)
# Returns: Order summary with items and total
```

**Finalize Order:**
```python
result = finalize_order_tool(1, "Please prepare quickly")
# Returns: Confirmation message
```

## Agents Integration

The Voice Assistant uses three main agents that interact with the database:

### 1. **Table Reservation Agent**
Handles restaurant table reservations. Uses reservation tools to:
- Check table availability
- Create new reservations
- View existing reservations
- Cancel reservations

### 2. **Order Handling Agent**
Handles customer food orders. Uses order tools to:
- Create new orders
- Add/remove items from orders
- View order details
- Finalize orders for kitchen

### 3. **General Inquiry Agent**
Answers general questions about the restaurant using RAG (ChromaDB):
- Menu information
- Restaurant hours
- Location and contact
- Dietary restrictions
- Special offers

## Database Relationships

```
Client
├── Reservation (one-to-many)
├── Order (one-to-many)
│   └── OrderItem (one-to-many)
│       └── MenuItem (many-to-one)

Table
└── Reservation (one-to-many)

MenuItem
└── OrderItem (one-to-many)
```

## Current Status

After initialization, the database contains:
- **5 Tables**: Capacities from 2 to 8 seats
- **Sample Menu Items**: Various categories (appetizers, mains, desserts, drinks)
- **No Initial Reservations or Orders**: Created dynamically through the agent

## Key Features

1. **Automatic Client Management**: Clients are created if they don't exist during reservations or orders
2. **Table Availability**: System finds the smallest suitable table for the party size
3. **Relationship Integrity**: Foreign keys ensure data consistency
4. **Status Tracking**: All reservations and orders have status tracking
5. **Timestamps**: All records track creation and modification times

## Troubleshooting

### Connection Issues
- Verify PostgreSQL server is running
- Check `.env` file has correct credentials
- Ensure database exists on the PostgreSQL server
- Verify network/firewall allows connection to `mlangelier.com:5432`

### Data Issues
- Run `init_database.py` again to reset all tables
- Check `view_database_contents.py` to inspect current state
- Verify foreign key relationships are correct

### Agent Issues
- Ensure database is initialized before starting agents
- Check database logs in `src/database/` directory
- Verify all required Python packages are installed
