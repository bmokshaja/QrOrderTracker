import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from models import User, Order, StatusQRCode, OrderStatus, UserRole
from werkzeug.security import generate_password_hash
import mysql.connector
from mysql.connector import Error

# Load environment variables
load_dotenv()

class MySQLStorage:
    def __init__(self):
        self.connect()
        self.create_tables()
        self.initialize_default_data()
    
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USERNAME', 'root'),
                password=os.getenv('DB_PASSWORD', '12345678'),
                database=os.getenv('DB_NAME', 'qrordertracker')
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise e
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            # Create Users table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create Orders table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id VARCHAR(36) PRIMARY KEY,
                order_id VARCHAR(50) NOT NULL UNIQUE,
                customer_id VARCHAR(36) NOT NULL,
                vendor_id VARCHAR(36),
                delivery_partner_id VARCHAR(36),
                description TEXT NOT NULL,
                pickup_location TEXT NOT NULL,
                delivery_location TEXT NOT NULL,
                status VARCHAR(50) NOT NULL,
                qr_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES users(id)
            )
            """)
            
            # Create Status QR Codes table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_qr_codes (
                id VARCHAR(36) PRIMARY KEY,
                status VARCHAR(50) NOT NULL,
                location_description TEXT NOT NULL,
                qr_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            self.connection.commit()
            print("Tables created successfully")
        except Error as e:
            print(f"Error creating tables: {e}")
            self.connection.rollback()
            raise e
    
    def initialize_default_data(self):
        """Initialize default admin user and status QR codes if they don't exist"""
        try:
            # Check if admin exists
            self.cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin = self.cursor.fetchone()
            
            if not admin:
                # Create default admin
                admin_id = str(uuid.uuid4())
                self.cursor.execute(
                    "INSERT INTO users (id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                    (admin_id, "admin", "admin@example.com", generate_password_hash("admin123"), UserRole.ADMIN.value)
                )
                
                # Create default status QR codes
                statuses = [
                    (OrderStatus.VENDOR_RECEIVED.value, "Vendor location"),
                    (OrderStatus.SHIPPING.value, "Shipping center"),
                    (OrderStatus.OUT_FOR_DELIVERY.value, "Delivery vehicle"),
                    (OrderStatus.DELIVERED.value, "Customer location")
                ]
                
                for status, location in statuses:
                    self.cursor.execute(
                        "INSERT INTO status_qr_codes (id, status, location_description) VALUES (%s, %s, %s)",
                        (str(uuid.uuid4()), status, location)
                    )
                
                self.connection.commit()
                print("Default data initialized")
        except Error as e:
            print(f"Error initializing default data: {e}")
            self.connection.rollback()
    
    # User management
    def create_user(self, username, email, password, role):
        try:
            user_id = str(uuid.uuid4())
            self.cursor.execute(
                "INSERT INTO users (id, username, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (user_id, username, email, password, role.value)
            )
            self.connection.commit()
            return self.get_user_by_id(user_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        try:
            self.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_data = self.cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=UserRole(user_data['role'])
                )
            return None
        except Error as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_username(self, username):
        try:
            self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user_data = self.cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=UserRole(user_data['role'])
                )
            return None
        except Error as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email):
        try:
            self.cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user_data = self.cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=UserRole(user_data['role'])
                )
            return None
        except Error as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_users_by_role(self, role):
        try:
            self.cursor.execute("SELECT * FROM users WHERE role = %s", (role.value,))
            users_data = self.cursor.fetchall()
            return [
                User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=UserRole(user_data['role'])
                ) for user_data in users_data
            ]
        except Error as e:
            print(f"Error getting users: {e}")
            return []
    
    # Order management
    def create_order(self, customer_id, description, pickup_location, delivery_location):
        try:
            order_id = str(uuid.uuid4())
            order_id_string = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            self.cursor.execute(
                """INSERT INTO orders 
                (id, order_id, customer_id, description, pickup_location, delivery_location, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (order_id, order_id_string, customer_id, description, pickup_location, 
                 delivery_location, OrderStatus.CREATED.value)
            )
            
            self.connection.commit()
            return self.get_order_by_id(order_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error creating order: {e}")
            return None
    
    def get_order_by_id(self, order_id):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order_data = self.cursor.fetchone()
            if order_data:
                return Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                )
            return None
        except Error as e:
            print(f"Error getting order: {e}")
            return None
    
    def get_order_by_order_id(self, order_id_string):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id_string,))
            order_data = self.cursor.fetchone()
            if order_data:
                return Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                )
            return None
        except Error as e:
            print(f"Error getting order: {e}")
            return None
    
    def get_orders_by_customer(self, customer_id):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE customer_id = %s", (customer_id,))
            orders_data = self.cursor.fetchall()
            return [
                Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                ) for order_data in orders_data
            ]
        except Error as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_orders_by_vendor(self, vendor_id):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE vendor_id = %s", (vendor_id,))
            orders_data = self.cursor.fetchall()
            return [
                Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                ) for order_data in orders_data
            ]
        except Error as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_orders_by_delivery_partner(self, delivery_partner_id):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE delivery_partner_id = %s", (delivery_partner_id,))
            orders_data = self.cursor.fetchall()
            return [
                Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                ) for order_data in orders_data
            ]
        except Error as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_pending_orders(self):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE status = %s", (OrderStatus.CREATED.value,))
            orders_data = self.cursor.fetchall()
            return [
                Order(
                    id=order_data['id'],
                    order_id=order_data['order_id'],
                    customer_id=order_data['customer_id'],
                    description=order_data['description'],
                    pickup_location=order_data['pickup_location'],
                    delivery_location=order_data['delivery_location'],
                    status=OrderStatus(order_data['status']),
                    vendor_id=order_data['vendor_id'],
                    delivery_partner_id=order_data['delivery_partner_id'],
                    qr_code=order_data['qr_code']
                ) for order_data in orders_data
            ]
        except Error as e:
            print(f"Error getting pending orders: {e}")
            return []
    
    def update_order_status(self, order_id, status):
        try:
            self.cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                (status.value, order_id)
            )
            self.connection.commit()
            return self.get_order_by_id(order_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error updating order status: {e}")
            return None
    
    def assign_vendor_to_order(self, order_id, vendor_id):
        try:
            self.cursor.execute(
                "UPDATE orders SET vendor_id = %s WHERE id = %s",
                (vendor_id, order_id)
            )
            self.connection.commit()
            return self.get_order_by_id(order_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error assigning vendor: {e}")
            return None
    
    def assign_delivery_partner_to_order(self, order_id, delivery_partner_id):
        try:
            self.cursor.execute(
                "UPDATE orders SET delivery_partner_id = %s WHERE id = %s",
                (delivery_partner_id, order_id)
            )
            self.connection.commit()
            return self.get_order_by_id(order_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error assigning delivery partner: {e}")
            return None
    
    # Status QR code management
    def get_status_qr_code(self, qr_code_id):
        try:
            self.cursor.execute("SELECT * FROM status_qr_codes WHERE id = %s", (qr_code_id,))
            qr_data = self.cursor.fetchone()
            if qr_data:
                return StatusQRCode(
                    id=qr_data['id'],
                    status=OrderStatus(qr_data['status']),
                    location_description=qr_data['location_description'],
                    qr_code=qr_data['qr_code']
                )
            return None
        except Error as e:
            print(f"Error getting status QR code: {e}")
            return None
    
    def get_all_status_qr_codes(self):
        try:
            self.cursor.execute("SELECT * FROM status_qr_codes")
            qr_codes_data = self.cursor.fetchall()
            return [
                StatusQRCode(
                    id=qr_data['id'],
                    status=OrderStatus(qr_data['status']),
                    location_description=qr_data['location_description'],
                    qr_code=qr_data['qr_code']
                ) for qr_data in qr_codes_data
            ]
        except Error as e:
            print(f"Error getting all status QR codes: {e}")
            return []
    
    def update_qr_code_for_order(self, order_id, qr_code):
        try:
            self.cursor.execute(
                "UPDATE orders SET qr_code = %s WHERE id = %s",
                (qr_code, order_id)
            )
            self.connection.commit()
            return self.get_order_by_id(order_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error updating QR code for order: {e}")
            return None
    
    def update_qr_code_for_status(self, qr_code_id, qr_code):
        try:
            self.cursor.execute(
                "UPDATE status_qr_codes SET qr_code = %s WHERE id = %s",
                (qr_code, qr_code_id)
            )
            self.connection.commit()
            return self.get_status_qr_code(qr_code_id)
        except Error as e:
            self.connection.rollback()
            print(f"Error updating QR code for status: {e}")
            return None

# Create a global instance of the storage
storage = MySQLStorage()