"""
Database Contents Viewer
Displays all data from all tables in the restaurant database
"""

import sys
import os

# Disable SQLAlchemy echo before importing db_config
os.environ['SQLALCHEMY_SILENCE'] = '1'

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from datetime import datetime
from tabulate import tabulate

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey patch to disable echo
import db_config as db_config_module
db_config_module.engine.echo = False

from db_config import SessionLocal, test_connection
from database import Client, Reservation, Table, MenuItem, Order, OrderItem


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def view_clients():
    """Display all clients"""
    print_header("CLIENTS")
    
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        
        if not clients:
            print("No clients found.")
            return
        
        data = []
        for client in clients:
            data.append([
                client.id,
                client.name,
                client.phone,
                client.email or "N/A",
                client.created_at.strftime('%Y-%m-%d %H:%M') if client.created_at else "N/A"
            ])
        
        headers = ["ID", "Name", "Phone", "Email", "Created"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(clients)} client(s)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def view_tables():
    """Display all tables"""
    print_header("TABLES")
    
    db = SessionLocal()
    try:
        tables = db.query(Table).all()
        
        if not tables:
            print("No tables found.")
            return
        
        data = []
        for table in tables:
            status = "Active" if table.is_active else "Inactive"
            data.append([
                table.id,
                table.table_number,
                table.capacity,
                table.location or "N/A",
                status
            ])
        
        headers = ["ID", "Table #", "Capacity", "Location", "Status"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(tables)} table(s)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def view_reservations():
    """Display all reservations"""
    print_header("RESERVATIONS")
    
    db = SessionLocal()
    try:
        reservations = db.query(Reservation).all()
        
        if not reservations:
            print("No reservations found.")
            return
        
        data = []
        for res in reservations:
            client_name = res.client.name if res.client else "Unknown"
            table_num = res.table.table_number if res.table else "N/A"
            data.append([
                res.id,
                client_name,
                res.client.phone if res.client else "N/A",
                table_num,
                res.date.strftime('%Y-%m-%d') if res.date else "N/A",
                res.time,
                res.num_guests,
                res.status,
                res.special_requests[:30] + "..." if res.special_requests and len(res.special_requests) > 30 else (res.special_requests or "")
            ])
        
        headers = ["ID", "Client", "Phone", "Table", "Date", "Time", "Guests", "Status", "Special Requests"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print(f"\nTotal: {len(reservations)} reservation(s)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def view_menu_items():
    """Display all menu items"""
    print_header("MENU ITEMS")
    
    db = SessionLocal()
    try:
        menu_items = db.query(MenuItem).all()
        
        if not menu_items:
            print("No menu items found.")
            return
        
        # Group by category
        categories = {}
        for item in menu_items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        for category, items in sorted(categories.items()):
            print(f"\n{category.upper()}")
            print("-" * 80)
            
            data = []
            for item in items:
                available = "✓" if item.is_available else "✗"
                data.append([
                    item.id,
                    item.name,
                    f"${item.price:.2f}",
                    available,
                    item.description[:40] + "..." if item.description and len(item.description) > 40 else (item.description or "")
                ])
            
            headers = ["ID", "Name", "Price", "Available", "Description"]
            print(tabulate(data, headers=headers, tablefmt="grid"))
        
        print(f"\n\nTotal: {len(menu_items)} menu item(s)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def view_orders():
    """Display all orders with their items"""
    print_header("ORDERS")
    
    db = SessionLocal()
    try:
        orders = db.query(Order).order_by(Order.created_at.desc()).all()
        
        if not orders:
            print("No orders found.")
            return
        
        for order in orders:
            print(f"\n{'─' * 80}")
            print(f"Order #{order.id}")
            print(f"{'─' * 80}")
            print(f"Customer: {order.customer_name} ({order.customer_phone})")
            print(f"Type: {order.order_type}")
            print(f"Status: {order.status}")
            print(f"Table: {order.table_number if order.table_number else 'N/A'}")
            print(f"Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else 'N/A'}")
            print(f"Updated: {order.updated_at.strftime('%Y-%m-%d %H:%M:%S') if order.updated_at else 'N/A'}")
            
            if order.special_instructions:
                print(f"Instructions: {order.special_instructions}")
            
            # Get order items
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            
            if order_items:
                print(f"\nItems:")
                items_data = []
                for item in order_items:
                    menu_item = db.query(MenuItem).filter(MenuItem.id == item.menu_item_id).first()
                    item_name = menu_item.name if menu_item else "Unknown Item"
                    special = item.special_requests[:30] + "..." if item.special_requests and len(item.special_requests) > 30 else (item.special_requests or "")
                    items_data.append([
                        item_name,
                        item.quantity,
                        f"${item.unit_price:.2f}",
                        f"${item.subtotal:.2f}",
                        special
                    ])
                
                headers = ["Item", "Qty", "Unit Price", "Subtotal", "Special Requests"]
                print(tabulate(items_data, headers=headers, tablefmt="grid"))
            else:
                print("\nNo items in this order.")
            
            print(f"\nTotal: ${order.total_amount:.2f}")
        
        print(f"\n\nTotal: {len(orders)} order(s)")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def view_statistics():
    """Display database statistics"""
    print_header("DATABASE STATISTICS")
    
    db = SessionLocal()
    try:
        stats = []
        
        # Count records in each table
        stats.append(["Clients", db.query(Client).count()])
        stats.append(["Tables", db.query(Table).count()])
        stats.append(["Reservations", db.query(Reservation).count()])
        stats.append(["Menu Items", db.query(MenuItem).count()])
        stats.append(["Orders", db.query(Order).count()])
        stats.append(["Order Items", db.query(OrderItem).count()])
        
        # Reservation stats
        active_reservations = db.query(Reservation).filter(Reservation.status == "booked").count()
        stats.append(["Active Reservations", active_reservations])
        
        # Order stats
        preparing_orders = db.query(Order).filter(Order.status == "preparing").count()
        ready_orders = db.query(Order).filter(Order.status == "ready").count()
        stats.append(["Preparing Orders", preparing_orders])
        stats.append(["Ready Orders", ready_orders])
        
        # Menu stats
        available_items = db.query(MenuItem).filter(MenuItem.is_available == True).count()
        stats.append(["Available Menu Items", available_items])
        
        # Revenue (total from all orders)
        total_revenue = db.query(Order).filter(Order.status.in_(["ready", "delivered"])).with_entities(
            db.func.sum(Order.total_amount)
        ).scalar() or 0
        stats.append(["Total Revenue", f"${total_revenue:.2f}"])
        
        headers = ["Metric", "Value"]
        print(tabulate(stats, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


def add_menu_item():
    """Add a new menu item"""
    print_header("ADD NEW MENU ITEM")
    
    db = SessionLocal()
    try:
        name = input("Item name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return
        
        category = input("Category (appetizer/main/dessert/drink): ").strip().lower()
        if category not in ['appetizer', 'main', 'dessert', 'drink']:
            print("❌ Invalid category")
            return
        
        description = input("Description: ").strip()
        
        price_str = input("Price ($): ").strip()
        try:
            price = float(price_str)
        except ValueError:
            print("❌ Invalid price")
            return
        
        ingredients = input("Ingredients (optional): ").strip() or None
        is_available = input("Available? (y/n, default=y): ").strip().lower() != 'n'
        
        new_item = MenuItem(
            name=name,
            category=category,
            description=description,
            price=price,
            ingredients=ingredients,
            is_available=is_available
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        print(f"\n✓ Menu item '{name}' added successfully with ID {new_item.id}!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def delete_menu_item():
    """Delete a menu item"""
    print_header("DELETE MENU ITEM")
    
    db = SessionLocal()
    try:
        item_id_str = input("Enter menu item ID to delete: ").strip()
        try:
            item_id = int(item_id_str)
        except ValueError:
            print("❌ Invalid ID")
            return
        
        item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            print(f"❌ Menu item with ID {item_id} not found")
            return
        
        confirm = input(f"Delete '{item.name}'? (yes/no): ").strip().lower()
        if confirm == 'yes':
            db.delete(item)
            db.commit()
            print(f"✓ Menu item '{item.name}' deleted successfully!")
        else:
            print("Deletion cancelled.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def add_client():
    """Add a new client"""
    print_header("ADD NEW CLIENT")
    
    db = SessionLocal()
    try:
        name = input("Client name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return
        
        phone = input("Phone number: ").strip()
        if not phone:
            print("❌ Phone cannot be empty")
            return
        
        email = input("Email (optional): ").strip() or None
        
        new_client = Client(name=name, phone=phone, email=email)
        
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        
        print(f"\n✓ Client '{name}' added successfully with ID {new_client.id}!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def add_order():
    """Add a new order"""
    print_header("ADD NEW ORDER")
    
    db = SessionLocal()
    try:
        customer_name = input("Customer name: ").strip()
        if not customer_name:
            print("❌ Name cannot be empty")
            return
        
        customer_phone = input("Phone number: ").strip()
        if not customer_phone:
            print("❌ Phone cannot be empty")
            return
        
        order_type = input("Order type (takeaway/delivery/dine-in, default=takeaway): ").strip().lower() or 'takeaway'
        if order_type not in ['takeaway', 'delivery', 'dine-in']:
            print("❌ Invalid order type")
            return
        
        table_number = None
        if order_type == 'dine-in':
            table_num_str = input("Table number (optional): ").strip()
            if table_num_str:
                try:
                    table_number = int(table_num_str)
                except ValueError:
                    print("⚠ Invalid table number, skipping")
        
        new_order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            order_type=order_type,
            table_number=table_number,
            status='preparing',
            total_amount=0.0
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        print(f"\n✓ Order #{new_order.id} created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def modify_order():
    """Modify an existing order"""
    print_header("MODIFY ORDER")
    
    db = SessionLocal()
    try:
        order_id_str = input("Enter order ID to modify: ").strip()
        try:
            order_id = int(order_id_str)
        except ValueError:
            print("❌ Invalid ID")
            return
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            print(f"❌ Order with ID {order_id} not found")
            return
        
        print(f"\nCurrent order details:")
        print(f"  Customer: {order.customer_name}")
        print(f"  Phone: {order.customer_phone}")
        print(f"  Type: {order.order_type}")
        print(f"  Status: {order.status}")
        print(f"  Total: ${order.total_amount:.2f}")
        
        print("\nWhat would you like to modify?")
        print("  1. Status")
        print("  2. Special instructions")
        print("  0. Cancel")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            print("\nStatus options: preparing, ready, delivered, cancelled")
            new_status = input("New status: ").strip().lower()
            if new_status in ['preparing', 'ready', 'delivered', 'cancelled']:
                order.status = new_status
                db.commit()
                print(f"✓ Order status updated to '{new_status}'!")
            else:
                print("❌ Invalid status")
        elif choice == '2':
            new_instructions = input("Special instructions: ").strip()
            order.special_instructions = new_instructions
            db.commit()
            print("✓ Special instructions updated!")
        elif choice == '0':
            print("Modification cancelled.")
        else:
            print("❌ Invalid option")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def delete_order():
    """Delete an order"""
    print_header("DELETE ORDER")
    
    db = SessionLocal()
    try:
        order_id_str = input("Enter order ID to delete: ").strip()
        try:
            order_id = int(order_id_str)
        except ValueError:
            print("❌ Invalid ID")
            return
        
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            print(f"❌ Order with ID {order_id} not found")
            return
        
        confirm = input(f"Delete Order #{order_id} for {order.customer_name}? (yes/no): ").strip().lower()
        if confirm == 'yes':
            db.delete(order)
            db.commit()
            print(f"✓ Order #{order_id} deleted successfully!")
        else:
            print("Deletion cancelled.")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()
    
    input("\nPress Enter to continue...")


def show_table_menu(table_name, view_func, add_func=None, modify_func=None, delete_func=None):
    """Show menu for a specific table"""
    while True:
        view_func()
        
        print("\n" + "─"*80)
        print("OPTIONS:")
        options = []
        if add_func:
            options.append("1. Add new entry")
        if modify_func:
            options.append("2. Modify entry")
        if delete_func:
            options.append("3. Delete entry")
        options.append("0. Back to main menu")
        
        for opt in options:
            print(f"  {opt}")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1' and add_func:
            add_func()
        elif choice == '2' and modify_func:
            modify_func()
        elif choice == '3' and delete_func:
            delete_func()
        elif choice == '0':
            break
        else:
            print("❌ Invalid option")
            input("Press Enter to continue...")


def main_menu():
    """Display main interactive menu"""
    while True:
        print("\n" + "="*80)
        print("  RESTAURANT DATABASE MANAGER")
        print("="*80)
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        print("\nSELECT TABLE TO VIEW:")
        print("  1. Database Statistics")
        print("  2. Clients")
        print("  3. Tables")
        print("  4. Reservations")
        print("  5. Menu Items")
        print("  6. Orders")
        print("  0. Exit")
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == '1':
            view_statistics()
            input("\nPress Enter to continue...")
        elif choice == '2':
            show_table_menu("Clients", view_clients, add_client, None)
        elif choice == '3':
            show_table_menu("Tables", view_tables, None, None)
        elif choice == '4':
            show_table_menu("Reservations", view_reservations, None, None)
        elif choice == '5':
            show_table_menu("Menu Items", view_menu_items, add_menu_item, delete_menu_item)
        elif choice == '6':
            show_table_menu("Orders", view_orders, add_order, modify_order, delete_order)
        elif choice == '0':
            print("\n" + "="*80)
            print("  Goodbye!")
            print("="*80 + "\n")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number between 0 and 6.")
            input("Press Enter to continue...")


def main():
    """Main function"""
    # Test connection first
    if not test_connection():
        print("\n❌ Could not connect to database. Please check your configuration.")
        return
    
    print("\n✓ Database connection successful!")
    
    # Start interactive menu
    main_menu()


if __name__ == "__main__":
    main()
