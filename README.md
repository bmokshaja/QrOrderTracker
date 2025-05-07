QR Order Tracker
A comprehensive QR code-based order tracking system that allows managing and tracking orders through their entire lifecycle. This application supports multiple user roles, real-time status updates via QR codes, and a complete order management workflow.

🌟 Features
Multiple User Roles: Admin, Customer, Vendor, and Delivery Partner
QR Code Generation: Unique QR codes for orders and status updates
QR Code Scanning: Web-based scanner for updating order status
Complete Order Lifecycle: Track orders from creation to delivery
Responsive Design: Works on desktop, tablet, and mobile devices

🔧 Technologies
Backend
Flask: Web framework
SQLAlchemy: ORM for database operations
PyMySQL: MySQL database connector
Frontend
Bootstrap: Responsive UI components
HTML5/CSS3: Markup and styling
JavaScript: Client-side interactivity
HTML5-QRCode: QR code scanning library
Other
QRCode: QR code generation library
Pillow: Image processing

📁 Project Structure
app.py: Application entry point

__init__.py: Package initialization

models.py: Database models for users, orders, and QR codes

routes.py: URL route definitions

auth.py: User authentication and authorization

qr_manager.py: QR code generation and processing

order_manager.py: Order CRUD operations

storage.py: Database connection and operations

templates/: HTML templates

static/: CSS, JavaScript, and images

Procfile & runtime.txt: Deployment configuration

📋 Prerequisites
Python 3.9+
MySQL database
pip (Python package manager)
