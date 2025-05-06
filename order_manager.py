from models import OrderStatus, UserRole
from storage import storage
import random

def process_order_creation(customer_id, description, pickup_location, delivery_location):
    """Create a new order from a customer"""
    order = storage.create_order(customer_id, description, pickup_location, delivery_location)
    return order

def process_vendor_response(order_id, vendor_id, accepted):
    """Process a vendor's response to an order request"""
    if accepted:
        order = storage.assign_vendor_to_order(order_id, vendor_id)
        if order:
            order.update_status(OrderStatus.ACCEPTED)
            # Auto-assign a delivery partner when vendor accepts
            assign_delivery_partner(order_id)
            return order
    else:
        order = storage.get_order_by_id(order_id)
        if order:
            order.update_status(OrderStatus.REJECTED)
            return order
    return None

def assign_delivery_partner(order_id):
    """Auto-assign a delivery partner to an accepted order"""
    # Get all delivery partners
    delivery_partners = storage.get_users_by_role(UserRole.DELIVERY)
    
    if not delivery_partners:
        return None
    
    # Select a random delivery partner for now (in a real system, this would use logic based on availability, location, etc.)
    delivery_partner = random.choice(delivery_partners)
    
    # Assign the delivery partner to the order
    order = storage.assign_delivery_partner_to_order(order_id, delivery_partner.id)
    
    return order

def update_order_status(order_id, new_status):
    """Update the status of an order"""
    order = storage.update_order_status(order_id, new_status)
    return order

def get_order_by_tracking(order_id_string):
    """Get an order by its tracking ID (order_id)"""
    return storage.get_order_by_order_id(order_id_string)

def get_orders_for_customer(customer_id):
    """Get all orders for a specific customer"""
    return storage.get_orders_by_customer(customer_id)

def get_orders_for_vendor(vendor_id):
    """Get all orders assigned to a specific vendor"""
    return storage.get_orders_by_vendor(vendor_id)

def get_orders_for_delivery(delivery_partner_id):
    """Get all orders assigned to a specific delivery partner"""
    return storage.get_orders_by_delivery_partner(delivery_partner_id)

def get_pending_orders():
    """Get all pending orders (awaiting vendor acceptance)"""
    return storage.get_pending_orders()

def get_status_qr_codes():
    """Get all status QR codes (for admin)"""
    return storage.get_all_status_qr_codes()
