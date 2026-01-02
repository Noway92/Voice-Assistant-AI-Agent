"""
Test script for Order Handling System
Tests database connection, order creation, item management, and order status updates
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_config import SessionLocal, test_connection
from database.database import Order, OrderItem, MenuItem
from agents.tools.order_tools import OrderToolsSQL


def populate_sample_menu_items():
    """Populate database with sample menu items for testing"""
    db = SessionLocal()
    try:
        # Check if menu items already exist
        existing = db.query(MenuItem).count()
        if existing > 0:
            print(f"Menu already has {existing} items, skipping population.")
            return {'success': True, 'created': False}
        
        # Sample menu items
        menu_items = [
            MenuItem(name="Margherita Pizza", category="main", description="Classic tomato and mozzarella", 
                    price=12.50, is_available=True, ingredients="Tomato, Mozzarella, Basil"),
            MenuItem(name="Pepperoni Pizza", category="main", description="Spicy pepperoni pizza", 
                    price=14.00, is_available=True, ingredients="Tomato, Mozzarella, Pepperoni"),
            MenuItem(name="Caesar Salad", category="appetizer", description="Fresh romaine with caesar dressing", 
                    price=8.50, is_available=True, ingredients="Romaine, Parmesan, Croutons"),
            MenuItem(name="Tiramisu", category="dessert", description="Classic Italian dessert", 
                    price=6.50, is_available=True, ingredients="Mascarpone, Coffee, Cocoa"),
            MenuItem(name="Coca Cola", category="drink", description="Classic soda", 
                    price=3.00, is_available=True, ingredients="Carbonated water"),
            MenuItem(name="Lasagna", category="main", description="Traditional beef lasagna", 
                    price=13.50, is_available=True, ingredients="Beef, Pasta, Tomato, Cheese"),
        ]
        
        for item in menu_items:
            db.add(item)
        
        db.commit()
        print(f"✓ Successfully added {len(menu_items)} menu items to database!")
        return {'success': True, 'created': True, 'count': len(menu_items)}
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error populating menu items: {e}")
        return {'success': False, 'created': False}
    finally:
        db.close()


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_database_connection():
    """Test if database connection works"""
    print_section("TEST 1: Database Connection")
    
    try:
        result = test_connection()
        if result:
            print("✓ Database connection successful!")
            return True
        else:
            print("✗ Database connection failed!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_check_menu_items():
    """Check if menu items exist in database"""
    print_section("TEST 2: Check Menu Items")
    
    db = SessionLocal()
    try:
        menu_items = db.query(MenuItem).all()
        
        if not menu_items:
            print("⚠ No menu items found in database!")
            print("Attempting to populate with sample menu items...\n")
            db.close()
            result = populate_sample_menu_items()
            return result
        
        print(f"✓ Found {len(menu_items)} menu items:")
        for item in menu_items[:5]:  # Show first 5
            available = "Available" if item.is_available else "Not Available"
            print(f"  - {item.name} (${item.price}) - {available}")
        
        if len(menu_items) > 5:
            print(f"  ... and {len(menu_items) - 5} more items")
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking menu items: {e}")
        return False
    finally:
        db.close()


def test_create_order():
    """Test creating a new order"""
    print_section("TEST 3: Create Order")
    
    tools = OrderToolsSQL()
    
    # Create test order
    result = tools.create_order(
        customer_name="Test Customer",
        customer_phone="0612345678",
        order_type="takeaway"
    )
    
    print(f"Result: {result}")
    
    # Extract order ID from result
    if "Order #" in result:
        order_id = int(result.split("#")[1].split()[0])
        print(f"✓ Order created successfully! Order ID: {order_id}")
        return order_id
    else:
        print("✗ Failed to create order")
        return None


def test_add_items_to_order(order_id):
    """Test adding items to an order"""
    print_section("TEST 4: Add Items to Order")
    
    if not order_id:
        print("Skipping - No valid order ID")
        return False
    
    tools = OrderToolsSQL()
    
    # Get a menu item to add
    db = SessionLocal()
    try:
        menu_item = db.query(MenuItem).filter(MenuItem.is_available == True).first()
        
        if not menu_item:
            print("No available menu items to add")
            return False
        
        print(f"Adding: {menu_item.name} (${menu_item.price})")
        
        # Add item to order
        result = tools.add_item_to_order(
            order_id=order_id,
            item_name=menu_item.name,
            quantity=2,
            special_requests="Extra spicy please"
        )
        
        print(f"Result: {result}")
        
        if "successfully" in result.lower() or "added" in result.lower():
            print("Item added successfully!")
            
            # Try adding another item
            menu_item2 = db.query(MenuItem).filter(
                MenuItem.is_available == True,
                MenuItem.id != menu_item.id
            ).first()
            
            if menu_item2:
                print(f"\nAdding second item: {menu_item2.name}")
                result2 = tools.add_item_to_order(
                    order_id=order_id,
                    item_name=menu_item2.name,
                    quantity=1
                )
                print(f"Result: {result2}")
            
            return True
        else:
            print("Failed to add item")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()


def test_view_order(order_id):
    """Test viewing order details"""
    print_section("TEST 5: View Order")
    
    if not order_id:
        print("Skipping - No valid order ID")
        return False
    
    tools = OrderToolsSQL()
    
    result = tools.view_order(order_id)
    print(result)
    
    if "Order #" in result:
        print("Order retrieved successfully!")
        return True
    else:
        print("Failed to view order")
        return False


def test_update_item(order_id):
    """Test updating item quantity"""
    print_section("TEST 6: Update Item Quantity")
    
    if not order_id:
        print("Skipping - No valid order ID")
        return False
    
    tools = OrderToolsSQL()
    db = SessionLocal()
    
    try:
        # Get first item in the order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or not order.items:
            print("No items in order to update")
            return False
        
        first_item = order.items[0]
        item_name = first_item.menu_item.name
        
        print(f"Updating quantity of '{item_name}' to 3")
        
        result = tools.update_item_quantity(
            order_id=order_id,
            item_name=item_name,
            new_quantity=3
        )
        
        print(f"Result: {result}")
        
        if "updated" in result.lower():
            print("Item quantity updated successfully!")
            return True
        else:
            print("Failed to update item")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()


def test_check_order_status(order_id):
    """Test checking order status"""
    print_section("TEST 7: Check Order Status")
    
    if not order_id:
        print("Skipping - No valid order ID")
        return False
    
    tools = OrderToolsSQL()
    
    result = tools.check_order_status(
        customer_phone="0612345678"
    )
    
    print(result)
    
    if "Order #" in result or "found" in result.lower():
        print("Order status retrieved successfully!")
        return True
    else:
        print("Failed to check status")
        return False


def test_finalize_order(order_id):
    """Test finalizing an order"""
    print_section("TEST 8: Finalize Order")
    
    if not order_id:
        print("Skipping - No valid order ID")
        return False
    
    tools = OrderToolsSQL()
    
    result = tools.finalize_order(
        order_id=order_id,
        special_instructions="Please call when you arrive"
    )
    
    print(f"Result: {result}")
    
    if "confirmed" in result.lower() or "finalized" in result.lower() or "submitted" in result.lower():
        print("Order finalized successfully!")
        return True
    else:
        print("Failed to finalize order")
        return False


def test_database_integrity(order_id):
    """Check database records directly"""
    print_section("TEST 9: Database Integrity Check")
    
    db = SessionLocal()
    try:
        # Count orders
        total_orders = db.query(Order).count()
        print(f"Total orders in database: {total_orders}")
        
        # Count order items
        total_items = db.query(OrderItem).count()
        print(f"Total order items in database: {total_items}")
        
        if order_id:
            # Check specific order
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                print(f"\nTest Order #{order_id} Details:")
                print(f"  Customer: {order.customer_name}")
                print(f"  Phone: {order.customer_phone}")
                print(f"  Type: {order.order_type}")
                print(f"  Status: {order.status}")
                print(f"  Total: ${order.total_amount:.2f}")
                print(f"  Items: {len(order.items)}")
                
                for idx, item in enumerate(order.items, 1):
                    print(f"    {idx}. {item.menu_item.name} x{item.quantity} - ${item.subtotal:.2f}")
                    if item.special_requests:
                        print(f"       Special: {item.special_requests}")
        
        print("\nDatabase integrity check completed!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()


def cleanup_test_menu_items():
    """Clean up test menu items"""
    print_section("CLEANUP: Remove Test Menu Items")
    
    response = input("\nDo you want to delete the sample menu items? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Keeping menu items in database.")
        return
    
    db = SessionLocal()
    try:
        # Delete all menu items (this will also remove related order_items due to foreign key constraints)
        count = db.query(MenuItem).delete()
        db.commit()
        print(f"Deleted {count} menu items from database!")
    except Exception as e:
        db.rollback()
        print(f"Error deleting menu items: {e}")
    finally:
        db.close()


def cleanup_test_order(order_id):
    """Optional: Clean up test order"""
    print_section("CLEANUP: Remove Test Order")
    
    if not order_id:
        print("No order to clean up")
        return
    
    response = input(f"\nDo you want to delete test order #{order_id}? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Keeping test order in database.")
        return
    
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            db.delete(order)
            db.commit()
            print(f"Test order #{order_id} deleted successfully!")
        else:
            print(f"Order #{order_id} not found")
    except Exception as e:
        db.rollback()
        print(f"Error deleting order: {e}")
    finally:
        db.close()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  ORDER HANDLING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    test_order_id = None
    menu_created = False
    results = []
    
    # Run tests
    results.append(("Database Connection", test_database_connection()))
    
    menu_result = test_check_menu_items()
    if isinstance(menu_result, dict):
        results.append(("Menu Items Check", menu_result['success']))
        menu_created = menu_result.get('created', False)
    else:
        results.append(("Menu Items Check", menu_result))
    
    test_order_id = test_create_order()
    results.append(("Create Order", test_order_id is not None))
    
    results.append(("Add Items", test_add_items_to_order(test_order_id)))
    results.append(("View Order", test_view_order(test_order_id)))
    results.append(("Update Item", test_update_item(test_order_id)))
    results.append(("Check Status", test_check_order_status(test_order_id)))
    results.append(("Finalize Order", test_finalize_order(test_order_id)))
    results.append(("Database Integrity", test_database_integrity(test_order_id)))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if test_order_id:
        print(f"\n  Test Order ID: {test_order_id}")
        cleanup_test_order(test_order_id)
    
    # Cleanup menu items if they were created by this test
    if menu_created:
        cleanup_test_menu_items()
    
    print("\n" + "="*70)
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
