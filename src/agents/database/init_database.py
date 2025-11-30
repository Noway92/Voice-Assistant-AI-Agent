"""
Script to initialize the restaurant database.
This script will:
1. Test the database connection
2. Create all necessary tables
3. Optionally populate initial table data
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database.db_config import engine, init_db, test_connection, SessionLocal
from agents.database.database import Client, Reservation, Table, MenuItem, Order, OrderItem


def create_initial_tables():
    """Create initial restaurant tables."""
    print("\n[Creating initial restaurant tables...]")

    db = SessionLocal()
    try:
        # Check if tables already exist
        existing_tables = db.query(Table).all()
        if existing_tables:
            print(f"[INFO] Found {len(existing_tables)} existing tables. Skipping table creation.")
            return

        # Create 5 tables with different capacities
        tables_data = [
            {"table_number": 1, "capacity": 2, "location": "indoor"},
            {"table_number": 2, "capacity": 4, "location": "indoor"},
            {"table_number": 3, "capacity": 6, "location": "indoor"},
            {"table_number": 4, "capacity": 2, "location": "outdoor"},
            {"table_number": 5, "capacity": 8, "location": "outdoor"},
        ]

        for table_data in tables_data:
            table = Table(**table_data)
            db.add(table)

        db.commit()
        print(f"[SUCCESS] Created {len(tables_data)} restaurant tables")

        # Display created tables
        for table_data in tables_data:
            print(f"  - Table {table_data['table_number']}: {table_data['capacity']} seats ({table_data['location']})")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error creating tables: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main initialization function."""
    print("=" * 60)
    print("Restaurant Database Initialization")
    print("=" * 60)

    # Step 1: Test connection
    print("\n[STEP 1] Testing database connection...")
    if not test_connection():
        print("\n[FAILED] Database initialization failed: Cannot connect to database")
        print("Please check your .env file and ensure PostgreSQL is running.")
        return False

    # Step 2: Create tables
    print("\n[STEP 2] Creating database tables...")
    try:
        init_db()
    except Exception as e:
        print(f"\n[FAILED] Failed to create tables: {str(e)}")
        return False

    # Step 3: Create initial restaurant tables
    try:
        create_initial_tables()
    except Exception as e:
        print(f"\n[FAILED] Failed to create initial tables: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] Database initialization completed successfully!")
    print("=" * 60)
    print("\nYou can now:")
    print("  - Make reservations using the reservation tools")
    print("  - Migrate existing CSV data using migrate_csv_to_db.py")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
