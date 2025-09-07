from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import User
from app import db
import re

def jwt_required(fn):
    """Decorator to protect routes with JWT authentication"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid or missing token'}), 401
    return wrapper

def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

def doctor_required(fn):
    """Decorator to require doctor role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in ['doctor', 'admin']:
                return jsonify({'error': 'Doctor access required'}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True
    pattern = r'^[\+]?[1-9][\d]{0,15}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def validate_patient_data(data):
    """Validate patient data"""
    errors = []
    
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate gender
    if data.get('gender') and data['gender'] not in ['Male', 'Female', 'Other']:
        errors.append("Gender must be Male, Female, or Other")
    
    # Validate blood type
    if data.get('blood_type'):
        valid_blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if data['blood_type'] not in valid_blood_types:
            errors.append("Invalid blood type")
    
    # Validate height and weight
    if data.get('height') and (data['height'] <= 0 or data['height'] > 300):
        errors.append("Height must be between 0 and 300 cm")
    
    if data.get('weight') and (data['weight'] <= 0 or data['weight'] > 500):
        errors.append("Weight must be between 0 and 500 kg")
    
    return errors

def validate_appointment_data(data):
    """Validate appointment data"""
    errors = []
    
    required_fields = ['patient_id', 'doctor_name', 'appointment_date']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate appointment type
    if data.get('appointment_type'):
        valid_types = ['Checkup', 'Consultation', 'Emergency', 'Follow-up', 'Surgery', 'Other']
        if data['appointment_type'] not in valid_types:
            errors.append("Invalid appointment type")
    
    # Validate status
    if data.get('status'):
        valid_statuses = ['scheduled', 'completed', 'cancelled', 'rescheduled']
        if data['status'] not in valid_statuses:
            errors.append("Invalid appointment status")
    
    return errors

def handle_validation_errors(errors):
    """Return validation errors in a consistent format"""
    return jsonify({
        'error': 'Validation failed',
        'details': errors
    }), 400

def log_request_info():
    """Log request information for debugging"""
    current_app.logger.info(f"Request: {request.method} {request.path}")
    current_app.logger.info(f"Headers: {dict(request.headers)}")
    if request.is_json:
        current_app.logger.info(f"Body: {request.get_json()}")

def handle_database_error(error):
    """Handle database errors gracefully"""
    db.session.rollback()
    current_app.logger.error(f"Database error: {str(error)}")
    
    if "Duplicate entry" in str(error):
        return jsonify({'error': 'Resource already exists'}), 409
    elif "foreign key constraint fails" in str(error).lower():
        return jsonify({'error': 'Referenced resource does not exist'}), 400
    else:
        return jsonify({'error': 'Database operation failed'}), 500 