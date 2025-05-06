from __init__ import create_app, db

app = create_app()

# Initialize database
with app.app_context():
    # Import models to create tables
    import models
    
    # Create database tables
    db.create_all()
    
    # Initialize default QR codes for statuses if they don't exist
    from models import StatusQRCode, OrderStatus
    from qr_manager import generate_status_qr_code
    
    existing_statuses = StatusQRCode.query.all()
    status_values = [
        (OrderStatus.VENDOR_RECEIVED, "Vendor Warehouse"),
        (OrderStatus.SHIPPING, "Shipping Facility"),
        (OrderStatus.OUT_FOR_DELIVERY, "Delivery Vehicle"),
        (OrderStatus.DELIVERED, "Customer Location")
    ]
    
    if not existing_statuses:
        for status, location in status_values:
            qr_code = StatusQRCode(status=status, location_description=location)
            db.session.add(qr_code)
        
        db.session.commit()
        
        # Generate QR codes for each status
        for qr_code in StatusQRCode.query.all():
            if not qr_code.qr_code:
                qr_data = generate_status_qr_code(qr_code.id, qr_code.status)
                qr_code.qr_code = qr_data
                db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)