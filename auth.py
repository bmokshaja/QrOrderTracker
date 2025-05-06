from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import User, UserRole
# Change this line:
from __init__ import db, login_manager  # Import from __init__ instead of app
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        return redirect_based_on_role(user.role)
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user.role)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        
        # Log in the new user
        login_user(user)
        
        return redirect_based_on_role(user.role)
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

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