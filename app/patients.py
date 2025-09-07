from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Patient, User, Appointment
from app.middleware import validate_patient_data, handle_validation_errors, handle_database_error
from app import db
import uuid
from datetime import datetime, date
import re

patients_bp = Blueprint('patients', __name__)

def generate_patient_id():
    """Generate a unique patient ID"""
    return f"MED{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"

def validate_patient_form_data(data):
    """Enhanced validation for patient form data"""
    errors = []
    
    # Required fields validation
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'address', 'emergency_contact_name', 'emergency_contact_phone']
    
    for field in required_fields:
        if not data.get(field) or not str(data.get(field)).strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Name validation
    if data.get('first_name') and len(data['first_name'].strip()) < 2:
        errors.append("First name must be at least 2 characters long")
    
    if data.get('last_name') and len(data['last_name'].strip()) < 2:
        errors.append("Last name must be at least 2 characters long")
    
    # Date of birth validation
    if data.get('date_of_birth'):
        try:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            if dob > date.today():
                errors.append("Date of birth cannot be in the future")
            if dob < date(1900, 1, 1):
                errors.append("Date of birth seems invalid")
        except ValueError:
            errors.append("Invalid date of birth format. Use YYYY-MM-DD")
    
    # Phone number validation
    if data.get('phone'):
        phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
        phone_clean = re.sub(r'[\s\-\(\)]', '', data['phone'])
        if not phone_pattern.match(phone_clean):
            errors.append("Invalid phone number format")
    
    # Email validation
    if data.get('email'):
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(data['email']):
            errors.append("Invalid email address format")
    
    # Emergency contact validation
    if data.get('emergency_contact_phone'):
        phone_pattern = re.compile(r'^[\+]?[1-9][\d]{0,15}$')
        phone_clean = re.sub(r'[\s\-\(\)]', '', data['emergency_contact_phone'])
        if not phone_pattern.match(phone_clean):
            errors.append("Invalid emergency contact phone number format")
    
    # Age validation (if provided)
    if data.get('age'):
        try:
            age = int(data['age'])
            if age < 0 or age > 150:
                errors.append("Age must be between 0 and 150")
        except ValueError:
            errors.append("Age must be a valid number")
    
    return errors

@patients_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    """Create a new patient record with enhanced validation"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Enhanced validation
        validation_errors = validate_patient_form_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Generate unique patient ID if not provided
        if not data.get('patient_id'):
            data['patient_id'] = generate_patient_id()
        
        # Check if patient ID already exists
        existing_patient = Patient.query.filter_by(patient_id=data['patient_id']).first()
        if existing_patient:
            return jsonify({'error': 'Patient ID already exists'}), 409
        
        # Convert date string to date object
        try:
            date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Determine user_id for the patient
        if current_user.role in ['admin', 'doctor'] and data.get('user_id'):
            patient_user_id = data['user_id']
            if not User.query.get(patient_user_id):
                return jsonify({'error': 'Specified user not found'}), 404
        else:
            patient_user_id = current_user_id
        
        # Create new patient with all fields
        patient = Patient(
            patient_id=data['patient_id'],
            user_id=patient_user_id,
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            date_of_birth=date_of_birth,
            gender=data['gender'],
            phone=data.get('phone', '').strip(),
            email=data.get('email', '').strip(),
            address=data.get('address', '').strip(),
            medical_history=data.get('medical_history', '').strip(),
            current_medications=data.get('current_medications', '').strip(),
            allergies=data.get('allergies', '').strip(),
            emergency_contact_name=data.get('emergency_contact_name', '').strip(),
            emergency_contact_phone=data.get('emergency_contact_phone', '').strip(),
            emergency_contact_relationship=data.get('emergency_contact_relationship', '').strip(),
            blood_type=data.get('blood_type'),
            height=data.get('height'),
            weight=data.get('weight'),
            insurance_provider=data.get('insurance_provider', '').strip(),
            insurance_number=data.get('insurance_number', '').strip()
        )
        
        # Add age if provided
        if data.get('age'):
            try:
                patient.age = int(data['age'])
            except (ValueError, TypeError):
                pass  # Age will be calculated from DOB if invalid
        
        db.session.add(patient)
        db.session.commit()
        
        current_app.logger.info(f"Patient created: {patient.patient_id} by user {current_user_id}")
        
        return jsonify({
            'message': 'Patient created successfully',
            'patient': patient.to_dict(),
            'patient_id': patient.patient_id
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating patient: {str(e)}")
        return handle_database_error(e)

@patients_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    """Get all patients for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get patients with optional filters
        query = Patient.query.filter_by(user_id=current_user_id, is_active=True)
        
        # Apply filters
        if request.args.get('search'):
            search_term = request.args.get('search')
            query = query.filter(
                db.or_(
                    Patient.first_name.ilike(f'%{search_term}%'),
                    Patient.last_name.ilike(f'%{search_term}%'),
                    Patient.patient_id.ilike(f'%{search_term}%'),
                    Patient.phone.ilike(f'%{search_term}%'),
                    Patient.email.ilike(f'%{search_term}%')
                )
            )
        
        if request.args.get('gender'):
            query = query.filter_by(gender=request.args.get('gender'))
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        patients = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'patients': [patient.to_dict() for patient in patients.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': patients.total,
                'pages': patients.pages,
                'has_next': patients.has_next,
                'has_prev': patients.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get patients error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve patients'}), 500

@patients_bp.route('/patients/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    """Get a specific patient by ID"""
    try:
        current_user_id = get_jwt_identity()
        
        patient = Patient.query.filter_by(
            id=patient_id, 
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        return jsonify({'patient': patient.to_dict()})
        
    except Exception as e:
        return handle_database_error(e)

@patients_bp.route('/patients/my-patient', methods=['GET'])
@jwt_required()
def get_my_patient():
    """Get the current user's own patient record"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get current user to check role
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find patient record for this user
        patient = Patient.query.filter_by(
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not patient:
            return jsonify({'error': 'Patient record not found'}), 404
        
        return jsonify({'patient': patient.to_dict()})
        
    except Exception as e:
        return handle_database_error(e)

@patients_bp.route('/patients/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    """Update a patient record"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        patient = Patient.query.filter_by(
            id=patient_id, 
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Validate data if updating required fields
        if any(field in data for field in ['first_name', 'last_name', 'date_of_birth', 'gender']):
            validation_errors = validate_patient_form_data(data)
            if validation_errors:
                return jsonify({
                    'error': 'Validation failed',
                    'details': validation_errors
                }), 400
        
        # Update fields
        updateable_fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'email',
            'address', 'medical_history', 'current_medications', 'allergies',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'blood_type', 'height', 'weight', 'insurance_provider', 'insurance_number'
        ]
        
        for field in updateable_fields:
            if field in data:
                if field == 'date_of_birth':
                    try:
                        patient.date_of_birth = datetime.strptime(data[field], '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
                else:
                    setattr(patient, field, data[field].strip() if isinstance(data[field], str) else data[field])
        
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Patient updated successfully',
            'patient': patient.to_dict()
        }), 200
        
    except Exception as e:
        return handle_database_error(e)

@patients_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    """Soft delete a patient record"""
    try:
        current_user_id = get_jwt_identity()
        
        patient = Patient.query.filter_by(
            id=patient_id, 
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Soft delete
        patient.is_active = False
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Patient deleted successfully'
        }), 200
        
    except Exception as e:
        return handle_database_error(e)

@patients_bp.route('/patients/<int:patient_id>/appointments', methods=['GET'])
@jwt_required()
def get_patient_appointments(patient_id):
    """Get appointments for a specific patient"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify patient belongs to current user
        patient = Patient.query.filter_by(
            id=patient_id, 
            user_id=current_user_id, 
            is_active=True
        ).first()
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Get appointments
        appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
            Appointment.appointment_date.desc()
        ).all()
        
        return jsonify({
            'appointments': [appointment.to_dict() for appointment in appointments]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get patient appointments error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve appointments'}), 500

@patients_bp.route('/patients/search', methods=['GET'])
@jwt_required()
def search_patients():
    """Search patients by various criteria"""
    try:
        current_user_id = get_jwt_identity()
        search_term = request.args.get('q', '')
        
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400
        
        # Search in multiple fields
        patients = Patient.query.filter(
            db.and_(
                Patient.user_id == current_user_id,
                Patient.is_active == True,
                db.or_(
                    Patient.first_name.ilike(f'%{search_term}%'),
                    Patient.last_name.ilike(f'%{search_term}%'),
                    Patient.patient_id.ilike(f'%{search_term}%'),
                    Patient.phone.ilike(f'%{search_term}%'),
                    Patient.email.ilike(f'%{search_term}%'),
                    Patient.emergency_contact_name.ilike(f'%{search_term}%')
                )
            )
        ).limit(20).all()
        
        return jsonify({
            'patients': [patient.to_dict() for patient in patients]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Search patients error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@patients_bp.route('/patients/validate-id/<patient_id>', methods=['GET'])
@jwt_required()
def validate_patient_id(patient_id):
    """Check if a patient ID is available"""
    try:
        existing_patient = Patient.query.filter_by(patient_id=patient_id).first()
        return jsonify({
            'available': existing_patient is None,
            'patient_id': patient_id
        }), 200
    except Exception as e:
        current_app.logger.error(f"Validate patient ID error: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500 