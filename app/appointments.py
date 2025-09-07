from flask import Blueprint, request, jsonify
from app.models import Appointment, Patient, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.middleware import doctor_required, admin_required
from app import db
from datetime import datetime
import traceback

appointments_bp = Blueprint('appointments', __name__)

def handle_database_error(e):
    """Handle database errors consistently"""
    print(f"Database error: {str(e)}")
    return jsonify({'error': 'Database operation failed'}), 500

@appointments_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """Get all appointments (admin/doctor) or user's own appointments"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Admin and doctors can see all appointments
        if current_user.role in ['admin', 'doctor']:
            appointments = Appointment.query.filter_by(is_active=True).all()
        else:
            # Regular users can only see their own appointments
            patient = Patient.query.filter_by(user_id=current_user_id, is_active=True).first()
            if not patient:
                return jsonify({'error': 'Patient record not found'}), 404
            appointments = Appointment.query.filter_by(patient_id=patient.id, is_active=True).all()
        
        return jsonify({
            'appointments': [appointment.to_dict() for appointment in appointments]
        })
        
    except Exception as e:
        return handle_database_error(e)

@appointments_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    """Get a specific appointment"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment or not appointment.is_active:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Check if user has access to this appointment
        if current_user.role not in ['admin', 'doctor']:
            patient = Patient.query.filter_by(user_id=current_user_id, is_active=True).first()
            if not patient or appointment.patient_id != patient.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'appointment': appointment.to_dict()})
        
    except Exception as e:
        return handle_database_error(e)

@appointments_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    """Create a new appointment (admin/doctor only)"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if current_user.role not in ['admin', 'doctor']:
            return jsonify({'error': 'Only doctors and admins can create appointments'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'appointment_date', 'appointment_time', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Check if patient exists
        patient = Patient.query.get(data['patient_id'])
        if not patient or not patient.is_active:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Create appointment
        appointment = Appointment(
            patient_id=data['patient_id'],
            doctor_id=current_user_id,
            appointment_date=datetime.strptime(data['appointment_date'], '%Y-%m-%d').date(),
            appointment_time=datetime.strptime(data['appointment_time'], '%H:%M').time(),
            reason=data['reason'],
            status='Scheduled',
            notes=data.get('notes', ''),
            created_by=current_user_id
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment created successfully',
            'appointment': appointment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return handle_database_error(e)

@appointments_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    """Update an appointment (admin/doctor only)"""
    try:
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if current_user.role not in ['admin', 'doctor']:
            return jsonify({'error': 'Only doctors and admins can update appointments'}), 403
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment or not appointment.is_active:
            return jsonify({'error': 'Appointment not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'appointment_date' in data:
            appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        if 'appointment_time' in data:
            appointment.appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        if 'reason' in data:
            appointment.reason = data['reason']
        if 'status' in data:
            appointment.status = data['status']
        if 'notes' in data:
            appointment.notes = data['notes']
        
        appointment.updated_at = datetime.utcnow()
        appointment.updated_by = current_user_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Appointment updated successfully',
            'appointment': appointment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return handle_database_error(e)

@appointments_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    """Delete an appointment (admin/doctor only)"""
    try:
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if current_user.role not in ['admin', 'doctor']:
            return jsonify({'error': 'Only doctors and admins can delete appointments'}), 403
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment or not appointment.is_active:
            return jsonify({'error': 'Appointment not found'}), 404
        
        # Soft delete
        appointment.is_active = False
        appointment.updated_at = datetime.utcnow()
        appointment.updated_by = current_user_id
        
        db.session.commit()
        
        return jsonify({'message': 'Appointment deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return handle_database_error(e)

@appointments_bp.route('/appointments/search', methods=['GET'])
@jwt_required()
def search_appointments():
    """Search appointments by various criteria"""
    try:
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Get search parameters
        patient_name = request.args.get('patient_name', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        status = request.args.get('status', '')
        
        # Build query
        query = Appointment.query.filter_by(is_active=True)
        
        if patient_name:
            query = query.join(Patient).filter(
                (Patient.first_name.ilike(f'%{patient_name}%')) |
                (Patient.last_name.ilike(f'%{patient_name}%'))
            )
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date <= date_to_obj)
            except ValueError:
                pass
        
        if status:
            query = query.filter(Appointment.status == status)
        
        # Apply role-based filtering
        if current_user.role not in ['admin', 'doctor']:
            patient = Patient.query.filter_by(user_id=current_user_id, is_active=True).first()
            if patient:
                query = query.filter(Appointment.patient_id == patient.id)
            else:
                return jsonify({'error': 'Patient record not found'}), 404
        
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        return jsonify({
            'appointments': [appointment.to_dict() for appointment in appointments]
        })
        
    except Exception as e:
        return handle_database_error(e)
