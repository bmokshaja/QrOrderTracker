import qrcode
import io
import base64
from flask import url_for

def generate_order_qr_code(order_id):
    """Generate a QR code for an order that links to the order status page"""
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add the order tracking URL to the QR code
    data = f"ORDER:{order_id}"
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create an image from the QR Code instance
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to a BytesIO object
    buffered = io.BytesIO()
    img.save(buffered)
    
    # Return the base64 encoded string
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_status_qr_code(status_id, status):
    """Generate a QR code for a status update point (for admin/delivery)"""
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add status information to the QR code
    data = f"STATUS:{status_id}:{status}"
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create an image from the QR Code instance
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to a BytesIO object
    buffered = io.BytesIO()
    img.save(buffered)
    
    # Return the base64 encoded string
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def decode_qr_data(qr_data):
    """Decode QR code data to extract information"""
    try:
        # Split the QR code data by the colon
        parts = qr_data.split(':')
        
        if parts[0] == 'ORDER':
            # Order QR code
            return {
                'type': 'order',
                'order_id': parts[1]
            }
        elif parts[0] == 'STATUS':
            # Status QR code
            return {
                'type': 'status',
                'status_id': parts[1],
                'status': parts[2]
            }
        else:
            return {'type': 'unknown', 'data': qr_data}
    except Exception as e:
        return {'type': 'error', 'message': str(e)}
