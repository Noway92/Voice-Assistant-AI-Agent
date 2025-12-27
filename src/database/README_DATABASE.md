# Restaurant Database - PostgreSQL Setup

This document describes the PostgreSQL database setup for the restaurant reservation system.

## Database Structure

The database consists of three main tables:

### 1. **clients**
Stores customer information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique client identifier |
| name | String(100) | Customer name |
| phone | String(20) | Customer phone (unique) |
| email | String(100) | Customer email (optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

### 2. **tables**
Stores restaurant table information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique table identifier |
| table_number | Integer | Table number (unique) |
| capacity | Integer | Maximum number of seats |
| location | String(50) | Location (indoor/outdoor) |
| is_active | Boolean | Whether table is active |
| created_at | Timestamp | Record creation time |

### 3. **reservations**
Stores reservation information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Unique reservation identifier |
| client_id | Integer (FK) | Reference to clients table |
| table_id | Integer (FK) | Reference to tables table |
| date | Date | Reservation date |
| time | String(10) | Reservation time (HH:MM) |
| num_guests | Integer | Number of guests |
| status | String(20) | Status (booked/cancelled/completed) |
| special_requests | Text | Special requests (optional) |
| created_at | Timestamp | Record creation time |
| updated_at | Timestamp | Last update time |

## Configuration

### Environment Variables (.env)
```
DB_HOST=mlangelier.com
DB_USER=admin
DB_PASSWORD=nwy03kkAledAppKC
DB_PORT=5432
DB_NAME=llm_agent_db
```

## Scripts

### 1. Database Initialization
Creates all database tables (run once).

```bash
python src/agents/database/init_database.py
```

What it does:
- Tests database connection
- Creates all tables (clients, tables, reservations, menu_items, orders, order_items)
- Populates initial restaurant tables (5 tables with different capacities)

### 2. CSV Migration
Migrates existing CSV data to PostgreSQL (run once).

```bash
python src/agents/database/migrate_csv_to_db.py
```

What it does:
- Reads reservation.csv
- Creates client records from CSV data
- Creates reservation records with proper relationships
- Skips invalid or placeholder data

### 3. Database Creation (if needed)
Creates the database on PostgreSQL server (only if you have permission).

```bash
python src/agents/database/create_database.py
```

## Using the Reservation Tools

### Import the tools

```python
from agents.tools.reservation_tools_sql import (
    ReservationToolsSQL,
    check_availability_tool,
    make_reservation_tool,
    cancel_reservation_tool,
    view_reservations_tool
)
```

### Check Availability

```python
result = ReservationToolsSQL.check_availability(
    date_str="2025-11-30",
    time="19:00",
    num_guests=4
)
print(result)
```

### Make a Reservation

```python
result = ReservationToolsSQL.make_reservation(
    date_str="2025-11-30",
    time="19:00",
    customer_name="John Doe",
    phone="0612345678",
    num_guests=4,
    special_requests="Window seat please"
)
print(result)
```

### Cancel a Reservation

```python
result = ReservationToolsSQL.cancel_reservation(
    date_str="2025-11-30",
    time="19:00",
    customer_name="John Doe"
)
print(result)
```

### View Reservations

```python
# View all reservations
result = ReservationToolsSQL.view_reservations()
print(result)

# View reservations for a specific date
result = ReservationToolsSQL.view_reservations(date_str="2025-11-30")
print(result)
```

### Get Reservations by Phone

```python
reservations = ReservationToolsSQL.get_reservations_by_phone("0612345678")
for reservation in reservations:
    print(f"Date: {reservation['date']}, Time: {reservation['time']}, Guests: {reservation['num_guests']}")
```

## Current Database Status

After migration, your database contains:

- **5 Tables**: Tables 1-5 with capacities of 2, 4, 6, 2, and 8 seats
- **3 Clients**: Jean Dupont, Noé, Marie Martin
- **3 Reservations**: Successfully migrated from CSV

## Key Features

1. **Automatic Client Management**: Clients are automatically created if they don't exist when making a reservation
2. **Table Availability**: The system automatically finds the smallest available table that fits the party size
3. **Relationship Management**: Foreign keys ensure data integrity between clients, tables, and reservations
4. **Status Tracking**: Reservations can be tracked as booked, cancelled, or completed

## Troubleshooting

### Connection Issues
If you encounter connection issues:
1. Verify PostgreSQL server is running
2. Check .env file has correct credentials
3. Ensure database exists on the server
4. Check firewall/network settings

### Migration Issues
If migration fails:
1. Ensure init_database.py was run first
2. Check CSV file encoding (should be UTF-8)
3. Verify CSV file path is correct

## Additional Tables

The database also includes tables for future features:
- **menu_items**: For restaurant menu management
- **orders**: For order tracking
- **order_items**: For order line items

These tables are created but not yet used by the current tools.
