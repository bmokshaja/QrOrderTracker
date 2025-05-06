from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
import uuid
import random
from datetime import datetime

from models import User, Order, StatusQRCode, UserRole, OrderStatus
from qr_manager import generate_order_qr_code, generate_status_qr_code, decode_qr_data
# Change this line:
from __init__ import db  # Import db from __init__ instead of from app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
    return render_template('index.html')

def redirect_based_on_role(role):
    if role == UserRole.ADMIN:
        return redirect(url_for('main.admin_dashboard'))
    elif role == UserRole.VENDOR:
        return redirect(url_for('main.vendor_dashboard'))
    elif role == UserRole.DELIVERY:
        return redirect(url_for('main.delivery_dashboard'))
    elif role == UserRole.CUSTOMER:
        return redirect(url_for('main.customer_dashboard'))
    else:
        return redirect(url_for('main.index'))

# Customer routes
@main_bp.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != UserRole.CUSTOMER:
        flash('Access denied: You must be a customer to view this page.')
        return redirect(url_for('main.index'))
    
    # Get all orders for this customer
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    
    return render_template('customer_dashboard.html', orders=orders)

@main_bp.route('/customer/create-order', methods=['GET', 'POST'])
@login_required
def create_order():
    if current_user.role != UserRole.CUSTOMER:
        flash('Access denied: You must be a customer to create orders.')
        return redirect(url_for('main.index'))
    
    # Get all vendors for the dropdown
    vendors = User.query.filter_by(role=UserRole.VENDOR).all()
    
    if request.method == 'POST':
        description = request.form.get('description')
        pickup_location = request.form.get('pickup_location')
        delivery_location = request.form.get('delivery_location')
        vendor_id = request.form.get('vendor_id')
        
        if not (description and pickup_location and delivery_location and vendor_id):
            flash('All fields are required.')
            return redirect(url_for('main.create_order'))
        
        # Create a unique order ID
        order_id = str(uuid.uuid4())
        
        # Create the order
        order = Order(
            order_id=order_id,
            customer_id=current_user.id,
            vendor_id=vendor_id,
            description=description,
            pickup_location=pickup_location,
            delivery_location=delivery_location,
            status=OrderStatus.CREATED
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Order created successfully and assigned to vendor!')
        return redirect(url_for('main.customer_dashboard'))
    
    return render_template('create_order_new.html', vendors=vendors)

@main_bp.route('/customer/track-order', methods=['GET', 'POST'])
@login_required
def track_order():
    if current_user.role != UserRole.CUSTOMER:
        flash('Access denied: You must be a customer to track orders.')
        return redirect(url_for('main.index'))
    
    order = None
    
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.filter_by(order_id=order_id).first()
        
        if not order:
            flash('Order not found.')
    
    return render_template('track_order.html', order=order)

@main_bp.route('/order-status/<order_id>')
def order_status(order_id):
    order = Order.query.filter_by(order_id=order_id).first()
    
    if not order:
        flash('Order not found.')
        return redirect(url_for('main.index'))
    
    return render_template('order_status.html', order=order)

# Vendor routes
@main_bp.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    if current_user.role != UserRole.VENDOR:
        flash('Access denied: You must be a vendor to view this page.')
        return redirect(url_for('main.index'))
    
    # Get pending orders and orders assigned to this vendor
    pending_orders = Order.query.filter_by(status=OrderStatus.CREATED).all()
    assigned_orders = Order.query.filter_by(vendor_id=current_user.id).all()
    
    return render_template('vendor_dashboard.html', 
                          pending_orders=pending_orders,
                          assigned_orders=assigned_orders)

@main_bp.route('/vendor/respond-to-order/<order_id>/<action>')
@login_required
def respond_to_order(order_id, action):
    if current_user.role != UserRole.VENDOR:
        flash('Access denied: You must be a vendor to respond to orders.')
        return redirect(url_for('main.index'))
    
    # Check if the action is valid
    if action not in ['accept', 'reject']:
        flash('Invalid action.')
        return redirect(url_for('main.vendor_dashboard'))
    
    order = Order.query.get(order_id)
    if not order:
        flash('Order not found.')
        return redirect(url_for('main.vendor_dashboard'))
    
    if action == 'accept':
        order.vendor_id = current_user.id
        order.status = OrderStatus.ACCEPTED
        
        # Auto-assign a delivery partner when vendor accepts
        delivery_partners = User.query.filter_by(role=UserRole.DELIVERY).all()
        if delivery_partners:
            # Select a random delivery partner (in a real system, this would use logic based on availability, location, etc.)
            delivery_partner = random.choice(delivery_partners)
            order.delivery_partner_id = delivery_partner.id
        
        db.session.commit()
        flash('Order accepted successfully!')
    else:
        order.status = OrderStatus.REJECTED
        db.session.commit()
        flash('Order rejected successfully!')
    
    return redirect(url_for('main.vendor_dashboard'))

# Delivery Partner routes
@main_bp.route('/delivery/dashboard')
@login_required
def delivery_dashboard():
    if current_user.role != UserRole.DELIVERY:
        flash('Access denied: You must be a delivery partner to view this page.')
        return redirect(url_for('main.index'))
    
    # Get orders assigned to this delivery partner
    assigned_orders = Order.query.filter_by(delivery_partner_id=current_user.id).all()
    
    return render_template('delivery_dashboard.html', assigned_orders=assigned_orders)

@main_bp.route('/delivery/scanner')
@login_required
def scanner_page():
    if current_user.role != UserRole.DELIVERY:
        flash('Access denied: You must be a delivery partner to use the scanner.')
        return redirect(url_for('main.index'))
    
    return render_template('scanner.html')

@main_bp.route('/scanner')
def public_scanner_page():
    """Public scanner page for anyone to scan order QR codes"""
    return render_template('public_scanner.html')

@main_bp.route('/api/process-qr-scan', methods=['POST'])
def process_qr_scan():
    data = request.json.get('qr_data')
    if not data:
        return jsonify({'success': False, 'error': 'No QR data provided.'})
        
    # Decode the QR code to check its type
    decoded_data = decode_qr_data(data)
    
    if decoded_data['type'] == 'order':
        # This is an order QR code, get the order details
        order = Order.query.filter_by(order_id=decoded_data['order_id']).first()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found.'})
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    
    # If it's a status QR code, verify the user is a delivery partner
    if decoded_data['type'] == 'status' and current_user.role != UserRole.DELIVERY:
        return jsonify({'success': False, 'error': 'Access denied: You must be a delivery partner to scan status QR codes.'})
    
    if decoded_data['type'] == 'status':
        # Get the associated status
        status = decoded_data['status']
        
        # Get all orders assigned to this delivery partner
        assigned_orders = Order.query.filter_by(delivery_partner_id=current_user.id).all()
        
        if not assigned_orders:
            return jsonify({'success': False, 'error': 'You have no assigned orders to update.'})
        
        # Update the status of all assigned orders that haven't reached this status yet
        success_orders = []
        for order in assigned_orders:
            # Don't update if order has already passed this status
            # This is a simple check, a real app would have a more sophisticated status progression
            order_status_index = list(OrderStatus.__dict__.values()).index(order.status) if order.status in OrderStatus.__dict__.values() else -1
            current_status_index = list(OrderStatus.__dict__.values()).index(status) if status in OrderStatus.__dict__.values() else -1
            
            if order_status_index < current_status_index:
                order.status = status
                db.session.commit()
                success_orders.append(order)
        
        if success_orders:
            order_ids = ", ".join([order.order_id for order in success_orders])
            return jsonify({
                'success': True, 
                'message': f'Orders {order_ids} updated to status: {status}',
                'status': status
            })
        else:
            return jsonify({'success': False, 'error': 'No orders were updated. Orders may have already passed this status.'})
    elif decoded_data['type'] == 'order':
        # This is an order QR code, get the order ID
        order_id = decoded_data['order_id']
        
        # Find the order
        order = Order.query.filter_by(order_id=order_id).first()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found.'})
        
        # Return order information
        return jsonify({
            'success': True,
            'message': f'Order {order.order_id} found.',
            'type': 'order',
            'order_id': order.order_id,
            'status': order.status,
            'redirect_url': url_for('main.order_status', order_id=order.order_id)
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid QR code type. Expected status or order QR code.'})

# Admin routes
@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != UserRole.ADMIN:
        flash('Access denied: You must be an admin to view this page.')
        return redirect(url_for('main.index'))
    
    # Get all orders
    all_orders = Order.query.all()
    
    # Get all status QR codes
    status_qr_codes = StatusQRCode.query.all()
    
    # Generate QR codes if they don't exist
    for qr_code in status_qr_codes:
        if not qr_code.qr_code:
            qr_data = generate_status_qr_code(qr_code.id, qr_code.status)
            qr_code.qr_code = qr_data
            db.session.commit()
    
    # Get all users by role
    vendors = User.query.filter_by(role=UserRole.VENDOR).all()
    delivery_partners = User.query.filter_by(role=UserRole.DELIVERY).all()
    customers = User.query.filter_by(role=UserRole.CUSTOMER).all()
    
    return render_template('admin_dashboard_new.html',
                          orders=all_orders,
                          status_qr_codes=status_qr_codes,
                          vendors=vendors,
                          delivery_partners=delivery_partners,
                          customers=customers)

@main_bp.route('/admin/edit-user/<user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash('Access denied: You must be an admin to edit users.')
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('main.admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        
        if username and email and role:
            # Update the user
            user.username = username
            user.email = email
            user.role = role
            db.session.commit()
            
            flash(f'User {username} updated successfully.')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('All fields are required.')
    
    return render_template('edit_user.html', user=user, UserRole=UserRole)

@main_bp.route('/admin/deactivate-user/<user_id>')
@login_required
def deactivate_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash('Access denied: You must be an admin to deactivate users.')
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('main.admin_dashboard'))
    
    # In a real app, you would implement deactivation logic here
    # For now, we'll just display a message
    flash(f'User {user.username} has been deactivated.')
    return redirect(url_for('main.admin_dashboard'))