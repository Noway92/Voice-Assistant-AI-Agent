"""
Script to migrate reservation data from CSV to PostgreSQL database.
This script will:
1. Read the existing reservation.csv file
2. Extract unique tables and create them in the database
3. Extract unique clients and create them in the database
4. Create reservations with proper relationships
"""

import sys
import os
import csv
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database.db_config import SessionLocal, test_connection
from agents.database.database import Client, Reservation, Table


def migrate_tables_from_csv(csv_file_path: str):
    """Extract and create unique tables from CSV."""
    print("\n[STEP 1] Migrating tables...")

    db = SessionLocal()
    try:
        # Check if tables already exist
        existing_tables = db.query(Table).all()
        if existing_tables:
            print(f"[INFO] Found {len(existing_tables)} existing tables in database.")
            print("[INFO] Keeping existing tables (they were created during initialization)")
            return

        # Read unique tables from CSV
        tables_dict = {}
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                table_number = int(row['table_number'])
                capacity = int(row['capacity'])

                if table_number not in tables_dict:
                    tables_dict[table_number] = capacity

        # Create tables in database (only if none exist)
        for table_number, capacity in sorted(tables_dict.items()):
            table = Table(
                table_number=table_number,
                capacity=capacity,
                location="indoor",  # Default location
                is_active=True
            )
            db.add(table)

        db.commit()
        print(f"[SUCCESS] Created {len(tables_dict)} tables")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error migrating tables: {str(e)}")
        raise
    finally:
        db.close()


def migrate_clients_and_reservations(csv_file_path: str):
    """Extract and create clients and their reservations from CSV."""
    print("\n[STEP 2] Migrating clients and reservations...")

    db = SessionLocal()
    try:
        # Check if data already exists
        existing_clients = db.query(Client).count()
        existing_reservations = db.query(Reservation).count()

        if existing_clients > 0 or existing_reservations > 0:
            print(f"[INFO] Found {existing_clients} clients and {existing_reservations} reservations in database.")
            print("[INFO] Skipping migration to preserve existing data.")
            print("[INFO] If you want to re-migrate, please clear the data first.")
            return

        # Get table ID mapping
        tables = db.query(Table).all()
        table_map = {table.table_number: table.id for table in tables}

        # Track clients by phone
        client_map = {}

        # Read reservations from CSV
        reservations_created = 0
        clients_created = 0

        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip available (empty) slots
                if row['status'] in ['available', 'avaible'] or not row['customer_name']:
                    continue

                customer_name = row['customer_name'].strip()
                phone = row['phone'].strip()

                # Skip invalid entries
                if not customer_name or customer_name == '[Customer\'s Name]':
                    continue
                if not phone or phone == '[Customer\'s Phone Number]':
                    continue

                # Create or get client
                if phone not in client_map:
                    client = Client(name=customer_name, phone=phone)
                    db.add(client)
                    db.flush()  # Get the client ID
                    client_map[phone] = client.id
                    clients_created += 1
                else:
                    client_id = client_map[phone]

                # Parse date
                try:
                    reservation_date = datetime.strptime(row['date'], "%Y-%m-%d").date()
                except ValueError:
                    print(f"[WARNING] Skipping invalid date: {row['date']}")
                    continue

                # Get table ID
                table_number = int(row['table_number'])
                if table_number not in table_map:
                    print(f"[WARNING] Table {table_number} not found, skipping reservation")
                    continue

                # Create reservation
                reservation = Reservation(
                    client_id=client_map[phone],
                    table_id=table_map[table_number],
                    date=reservation_date,
                    time=row['time'],
                    num_guests=int(row['num_guests']) if row['num_guests'] and int(row['num_guests']) > 0 else 1,
                    status="booked",
                    special_requests=row['special_requests'] if row['special_requests'] and row['special_requests'] != '[]' else None
                )
                db.add(reservation)
                reservations_created += 1

        db.commit()
        print(f"[SUCCESS] Created {clients_created} clients")
        print(f"[SUCCESS] Created {reservations_created} reservations")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error migrating clients and reservations: {str(e)}")
        raise
    finally:
        db.close()


def main():
    """Main migration function."""
    print("=" * 60)
    print("CSV to PostgreSQL Migration")
    print("=" * 60)

    # Locate CSV file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(script_dir, "reservation.csv")

    if not os.path.exists(csv_file_path):
        print(f"\n[ERROR] CSV file not found at: {csv_file_path}")
        return False

    print(f"\n[INFO] CSV file found: {csv_file_path}")

    # Test connection
    print("\n[Testing database connection...]")
    if not test_connection():
        print("\n[FAILED] Migration failed: Cannot connect to database")
        print("Please check your .env file and ensure PostgreSQL is running.")
        return False

    try:
        # Migrate tables
        migrate_tables_from_csv(csv_file_path)

        # Migrate clients and reservations
        migrate_clients_and_reservations(csv_file_path)

        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed successfully!")
        print("=" * 60)
        print("\nYour reservation data has been migrated to PostgreSQL.")
        print("You can now use the SQL-based reservation tools.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
