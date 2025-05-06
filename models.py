from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from __init__ import db

class UserRole:
    ADMIN = 'admin'
    VENDOR = 'vendor'
    DELIVERY = 'delivery'
    CUSTOMER = 'customer'

class OrderStatus:
    CREATED = 'created'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    VENDOR_RECEIVED = 'vendor_received'
    SHIPPING = 'shipping'
    OUT_FOR_DELIVERY = 'out_for_delivery'
    DELIVERED = 'delivered'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders_as_customer = db.relationship('Order', backref='customer', lazy='dynamic', 
                                        foreign_keys='Order.customer_id')
    orders_as_vendor = db.relationship('Order', backref='vendor', lazy='dynamic',
                                      foreign_keys='Order.vendor_id')
    orders_as_delivery = db.relationship('Order', backref='delivery_partner', lazy='dynamic',
                                        foreign_keys='Order.delivery_partner_id')
    
    # Override get_id from UserMixin to ensure it returns a string
    def get_id(self):
        return str(self.id)
    
    def __init__(self, username, email, password, role):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(36), unique=True, nullable=False)  # Use UUID as string
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    delivery_partner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    pickup_location = db.Column(db.Text, nullable=False)  # For quantity in our modification
    delivery_location = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default=OrderStatus.CREATED)
    qr_code = db.Column(db.Text, nullable=True)  # Store QR code data as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_status(self, status):
        self.status = status
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def assign_vendor(self, vendor_id):
        self.vendor_id = vendor_id
        db.session.commit()
        return self
    
    def assign_delivery_partner(self, delivery_partner_id):
        self.delivery_partner_id = delivery_partner_id
        db.session.commit()
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'vendor_id': self.vendor_id,
            'delivery_partner_id': self.delivery_partner_id,
            'description': self.description,
            'pickup_location': self.pickup_location,
            'delivery_location': self.delivery_location,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class StatusQRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(30), nullable=False)
    location_description = db.Column(db.Text, nullable=False)
    qr_code = db.Column(db.Text, nullable=True)  # Store QR code data as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'location_description': self.location_description,
            'created_at': self.created_at
        }