from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
from database.db_config import SessionLocal
from database.database import Order, OrderItem, MenuItem


class OrderToolsSQL:
    """Tools for managing restaurant orders with PostgreSQL."""

    @staticmethod
    def create_order(
        customer_name: str,
        customer_phone: str,
        order_type: str = "takeaway"
    ) -> str:
        """
        Create a new order.

        Args:
            customer_name: Customer's name
            customer_phone: Customer's phone number
            order_type: Type of order (takeaway, delivery)

        Returns:
            Confirmation message with order ID
        """
        db: Session = SessionLocal()
        try:
            # Validate order type
            if order_type not in ["takeaway", "delivery"]:
                return f"Invalid order type. Please choose 'takeaway' or 'delivery'."
            
            # Create new order
            order = Order(
                customer_name=customer_name,
                customer_phone=customer_phone,
                order_type=order_type,
                table_number=None,
                status="preparing",
                total_amount=0.0
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return (f"Order #{order.id} created for {customer_name} (Phone: {customer_phone}). "
                   f"Order type: {order_type}. "
                   f"You can now add items to your order.")
        
        except Exception as e:
            db.rollback()
            return f"Error creating order: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def add_item_to_order(
        order_id: int,
        item_name: str,
        quantity: int,
        special_requests: str = ""
    ) -> str:
        """
        Add an item to an existing order.

        Args:
            order_id: ID of the order
            item_name: Name of the menu item
            quantity: Quantity to add
            special_requests: Special preparation requests (optional)

        Returns:
            Confirmation message with updated total
        """
        db: Session = SessionLocal()
        try:
            # Find the order
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return f"Observation: Order #{order_id} not found"
            
            if order.status not in ["preparing"]:
                return f"Observation: Cannot modify order #{order_id}. Order status is: {order.status}"
            
            # Find the menu item (case-insensitive partial match)
            menu_item = db.query(MenuItem).filter(
                MenuItem.name.ilike(f"%{item_name}%"),
                MenuItem.is_available == True
            ).first()
            
            if not menu_item:
                return f"Menu item '{item_name}' not found or not available"
            
            # Check if item already exists in order
            existing_item = db.query(OrderItem).filter(
                OrderItem.order_id == order_id,
                OrderItem.menu_item_id == menu_item.id
            ).first()
            
            if existing_item:
                # Update quantity of existing item
                existing_item.quantity += quantity
                existing_item.subtotal = existing_item.quantity * existing_item.unit_price
                db.flush()  # Ensure update is written before calculating total
                message = f"Updated {menu_item.name} quantity to {existing_item.quantity}"
            else:
                # Add new item
                subtotal = menu_item.price * quantity
                order_item = OrderItem(
                    order_id=order_id,
                    menu_item_id=menu_item.id,
                    quantity=quantity,
                    unit_price=menu_item.price,
                    subtotal=subtotal,
                    special_requests=special_requests if special_requests else None
                )
                db.add(order_item)
                db.flush()  # Ensure insert is written before calculating total
                message = f"Added {quantity}x {menu_item.name} to order"
            
            # Update order total
            order.total_amount = sum(
                item.subtotal for item in db.query(OrderItem).filter(
                    OrderItem.order_id == order_id
                ).all()
            )
            
            db.commit()
            
            return f"{message}. Current total: €{order.total_amount:.2f}"
        
        except Exception as e:
            db.rollback()
            return f"Error adding item: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def update_item_quantity(
        order_id: int,
        item_name: str,
        new_quantity: int
    ) -> str:
        """
        Update the quantity of an item in an order.

        Args:
            order_id: ID of the order
            item_name: Name of the menu item
            new_quantity: New quantity (use 0 to remove)

        Returns:
            Confirmation message
        """
        db: Session = SessionLocal()
        try:
            # Find the order
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return f"Order #{order_id} not found"
            
            if order.status not in ["preparing"]:
                return f"Cannot modify order #{order_id}. Order status is: {order.status}"
            
            # Find the menu item
            menu_item = db.query(MenuItem).filter(
                MenuItem.name.ilike(f"%{item_name}%")
            ).first()
            
            if not menu_item:
                return f"Observation: Menu item '{item_name}' not found"
            
            # Find the order item
            order_item = db.query(OrderItem).filter(
                OrderItem.order_id == order_id,
                OrderItem.menu_item_id == menu_item.id
            ).first()
            
            if not order_item:
                return f"Observation: {menu_item.name} is not in order #{order_id}"
            
            if new_quantity == 0:
                # Remove item
                db.delete(order_item)
                message = f"Removed {menu_item.name} from order"
            else:
                # Update quantity
                order_item.quantity = new_quantity
                order_item.subtotal = order_item.unit_price * new_quantity
                message = f"Updated {menu_item.name} quantity to {new_quantity}"
            
            # Update order total
            order.total_amount = sum(
                item.subtotal for item in db.query(OrderItem).filter(
                    OrderItem.order_id == order_id
                ).all()
            )
            
            db.commit()
            
            return f"Observation: {message}. Current total: €{order.total_amount:.2f}"
        
        except Exception as e:
            db.rollback()
            return f"Observation: Error updating item: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def remove_item_from_order(
        order_id: int,
        item_name: str
    ) -> str:
        """
        Remove an item from an order.

        Args:
            order_id: ID of the order
            item_name: Name of the menu item to remove

        Returns:
            Confirmation message
        """
        return OrderToolsSQL.update_item_quantity(order_id, item_name, 0)

    @staticmethod
    def view_order(order_id: int) -> str:
        """
        View all items in an order with total.

        Args:
            order_id: ID of the order

        Returns:
            Formatted order details
        """
        db: Session = SessionLocal()
        try:
            # Find the order
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return f"Order #{order_id} not found"
            
            # Get order items
            order_items = (
                db.query(OrderItem, MenuItem)
                .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
                .filter(OrderItem.order_id == order_id)
                .all()
            )
            
            if not order_items:
                return f"Order #{order_id} is empty. Add items to continue."
            
            # Format order details
            items_list = []
            for order_item, menu_item in order_items:
                item_line = f"{order_item.quantity}x {menu_item.name} - €{order_item.subtotal:.2f}"
                if order_item.special_requests:
                    item_line += f" (Note: {order_item.special_requests})"
                items_list.append(item_line)
            
            order_details = (
                f"Order #{order.id} for {order.customer_name} ({order.customer_phone})\n"
                f"Status: {order.status}\n"
                f"Type: {order.order_type}\n"
                f"Items:\n" + "\n".join(f"  - {item}" for item in items_list) + "\n"
                f"Total: €{order.total_amount:.2f}"
            )
            
            if order.special_instructions:
                order_details += f"\nSpecial instructions: {order.special_instructions}"
            
            return order_details
        
        except Exception as e:
            return f"Error viewing order: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def finalize_order(
        order_id: int,
        special_instructions: str = ""
    ) -> str:
        """
        Finalize an order and submit it to the kitchen.

        Args:
            order_id: ID of the order
            special_instructions: Any special instructions for the order

        Returns:
            Confirmation message with estimated time
        """
        db: Session = SessionLocal()
        try:
            # Find the order
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return f"Order #{order_id} not found"
            
            if order.status != "preparing":
                return f"Order #{order_id} has already been finalized. Status: {order.status}"
            
            # Check if order has items
            item_count = db.query(OrderItem).filter(OrderItem.order_id == order_id).count()
            if item_count == 0:
                return f"Cannot finalize empty order #{order_id}. Please add items first."
            
            # Update order status
            order.status = "ready"
            if special_instructions:
                order.special_instructions = special_instructions
            
            db.commit()
            
            # Estimate preparation time (simple logic: 5 min per item)
            estimated_time = item_count * 5
            
            return (f"Order #{order.id} confirmed and sent to kitchen! "
                   f"Total: €{order.total_amount:.2f}. "
                   f"Estimated preparation time: {estimated_time} minutes. "
                   f"You will be notified when your order is ready.")
        
        except Exception as e:
            db.rollback()
            return f"Error finalizing order: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def check_order_status(
        customer_phone: str,
        order_id: Optional[int] = None
    ) -> str:
        """
        Check the status of an order by phone number or order ID.

        Args:
            customer_phone: Customer's phone number
            order_id: Optional specific order ID

        Returns:
            Order status information
        """
        db: Session = SessionLocal()
        try:
            if order_id:
                # Look for specific order
                order = db.query(Order).filter(
                    Order.id == order_id,
                    Order.customer_phone == customer_phone
                ).first()
                
                if not order:
                    return f"No order #{order_id} found for phone number {customer_phone}"
                
                orders = [order]
            else:
                # Look for all active orders for this phone number
                orders = db.query(Order).filter(
                    Order.customer_phone == customer_phone,
                    Order.status.in_(["preparing", "ready"])
                ).order_by(Order.created_at.desc()).all()
                
                if not orders:
                    return f"No active orders found for phone number {customer_phone}"
            
            # Format order statuses
            status_messages = []
            for order in orders:
                status_map = {
                    "preparing": "Being prepared in the kitchen",
                    "ready": "Ready for pickup/delivery!",
                    "delivered": "Delivered",
                    "cancelled": "Cancelled"
                }
                
                status_msg = (
                    f"Order #{order.id} - {status_map.get(order.status, order.status)}\n"
                    f"  Total: €{order.total_amount:.2f}\n"
                    f"  Placed: {order.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
                status_messages.append(status_msg)
            
            return "\n\n".join(status_messages)
        
        except Exception as e:
            return f"Error checking order status: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def cancel_order(
        order_id: int,
        customer_phone: str
    ) -> str:
        """
        Cancel an order.

        Args:
            order_id: ID of the order
            customer_phone: Customer's phone number (for verification)

        Returns:
            Confirmation message
        """
        db: Session = SessionLocal()
        try:
            # Find the order
            order = db.query(Order).filter(
                Order.id == order_id,
                Order.customer_phone == customer_phone
            ).first()
            
            if not order:
                return f"Order #{order_id} not found for phone number {customer_phone}"
            
            if order.status == "cancelled":
                return f"Order #{order_id} is already cancelled"
            
            if order.status in ["delivered", "completed"]:
                return f"Cannot cancel order #{order_id} - order has already been {order.status}"
            
            # Cancel the order
            order.status = "cancelled"
            db.commit()
            
            return (f"Order #{order_id} has been cancelled successfully. "
                   f"Total amount: €{order.total_amount:.2f}")
        
        except Exception as e:
            db.rollback()
            return f"Error cancelling order: {str(e)}"
        finally:
            db.close()


# Tool functions for LangChain/agent integration
def create_order_tool(
    customer_name: str,
    customer_phone: str,
    order_type: str = "takeaway"
) -> str:
    """Create a new order."""
    return OrderToolsSQL.create_order(customer_name, customer_phone, order_type)


def add_item_tool(
    order_id: int,
    item_name: str,
    quantity: int,
    special_requests: str = ""
) -> str:
    """Add an item to an order."""
    return OrderToolsSQL.add_item_to_order(order_id, item_name, quantity, special_requests)


def update_item_tool(
    order_id: int,
    item_name: str,
    new_quantity: int
) -> str:
    """Update item quantity in an order."""
    return OrderToolsSQL.update_item_quantity(order_id, item_name, new_quantity)


def remove_item_tool(
    order_id: int,
    item_name: str
) -> str:
    """Remove an item from an order."""
    return OrderToolsSQL.remove_item_from_order(order_id, item_name)


def view_order_tool(order_id: int) -> str:
    """View order details."""
    return OrderToolsSQL.view_order(order_id)


def finalize_order_tool(
    order_id: int,
    special_instructions: str = ""
) -> str:
    """Finalize and submit an order."""
    return OrderToolsSQL.finalize_order(order_id, special_instructions)


def check_status_tool(
    customer_phone: str,
    order_id: int = None
) -> str:
    """Check order status."""
    return OrderToolsSQL.check_order_status(customer_phone, order_id)


def cancel_order_tool(
    order_id: int,
    customer_phone: str
) -> str:
    """Cancel an order."""
    return OrderToolsSQL.cancel_order(order_id, customer_phone)
