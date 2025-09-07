from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Patient, Appointment
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get dashboard data for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user info
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get patient count
        patient_count = Patient.query.filter_by(
            user_id=current_user_id, 
            is_active=True
        ).count()
        
        # Get appointment count
        appointment_count = Appointment.query.join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True
        ).count()
        
        # Get recent patients (last 5)
        recent_patients = Patient.query.filter_by(
            user_id=current_user_id, 
            is_active=True
        ).order_by(Patient.created_at.desc()).limit(5).all()
        
        # Get upcoming appointments (next 7 days)
        today = datetime.now().date()
        week_from_now = today + timedelta(days=7)
        
        upcoming_appointments = Appointment.query.join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= week_from_now,
            Appointment.status == 'scheduled'
        ).order_by(Appointment.appointment_date).limit(5).all()
        
        # Get gender distribution
        gender_stats = db.session.query(
            Patient.gender, 
            func.count(Patient.id)
        ).filter_by(
            user_id=current_user_id, 
            is_active=True
        ).group_by(Patient.gender).all()
        
        gender_distribution = {gender: count for gender, count in gender_stats}
        
        # Get age distribution
        age_stats = db.session.query(
            func.floor(func.datediff(func.curdate(), Patient.date_of_birth) / 365.25).label('age_group'),
            func.count(Patient.id)
        ).filter_by(
            user_id=current_user_id, 
            is_active=True
        ).group_by('age_group').order_by('age_group').all()
        
        age_distribution = {}
        for age_group, count in age_stats:
            if age_group is not None:
                if age_group < 18:
                    age_range = '0-17'
                elif age_group < 30:
                    age_range = '18-29'
                elif age_group < 50:
                    age_range = '30-49'
                elif age_group < 65:
                    age_range = '50-64'
                else:
                    age_range = '65+'
                
                age_distribution[age_range] = age_distribution.get(age_range, 0) + count
        
        # Get blood type distribution
        blood_type_stats = db.session.query(
            Patient.blood_type, 
            func.count(Patient.id)
        ).filter_by(
            user_id=current_user_id, 
            is_active=True
        ).filter(Patient.blood_type.isnot(None)).group_by(Patient.blood_type).all()
        
        blood_type_distribution = {blood_type: count for blood_type, count in blood_type_stats}
        
        # Get appointment status distribution
        appointment_status_stats = db.session.query(
            Appointment.status, 
            func.count(Appointment.id)
        ).join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True
        ).group_by(Appointment.status).all()
        
        appointment_status_distribution = {status: count for status, count in appointment_status_stats}
        
        # Get monthly patient registration trend (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_registrations = db.session.query(
            func.date_format(Patient.created_at, '%Y-%m').label('month'),
            func.count(Patient.id)
        ).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            Patient.created_at >= six_months_ago
        ).group_by('month').order_by('month').all()
        
        monthly_trend = {month: count for month, count in monthly_registrations}
        
        return jsonify({
            'user': user.to_dict(),
            'statistics': {
                'total_patients': patient_count,
                'total_appointments': appointment_count,
                'gender_distribution': gender_distribution,
                'age_distribution': age_distribution,
                'blood_type_distribution': blood_type_distribution,
                'appointment_status_distribution': appointment_status_distribution,
                'monthly_registrations': monthly_trend
            },
            'recent_patients': [patient.to_dict() for patient in recent_patients],
            'upcoming_appointments': [appointment.to_dict() for appointment in upcoming_appointments]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve dashboard data'}), 500

@dashboard_bp.route('/dashboard/quick-stats', methods=['GET'])
@jwt_required()
def get_quick_stats():
    """Get quick statistics for the dashboard"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get counts
        patient_count = Patient.query.filter_by(
            user_id=current_user_id, 
            is_active=True
        ).count()
        
        today = datetime.now().date()
        
        # Today's appointments
        today_appointments = Appointment.query.join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            func.date(Appointment.appointment_date) == today
        ).count()
        
        # This week's appointments
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_appointments = Appointment.query.join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            func.date(Appointment.appointment_date).between(week_start, week_end)
        ).count()
        
        # New patients this month
        month_start = today.replace(day=1)
        new_patients_month = Patient.query.filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            Patient.created_at >= month_start
        ).count()
        
        return jsonify({
            'quick_stats': {
                'total_patients': patient_count,
                'today_appointments': today_appointments,
                'week_appointments': week_appointments,
                'new_patients_month': new_patients_month
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Quick stats error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve quick stats'}), 500

@dashboard_bp.route('/dashboard/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for the current user"""
    try:
        current_user_id = get_jwt_identity()
        notifications = []
        
        # Check for upcoming appointments (next 24 hours)
        tomorrow = datetime.now() + timedelta(days=1)
        upcoming_appointments = Appointment.query.join(Patient).filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            Appointment.appointment_date <= tomorrow,
            Appointment.appointment_date >= datetime.now(),
            Appointment.status == 'scheduled'
        ).all()
        
        for appointment in upcoming_appointments:
            notifications.append({
                'type': 'appointment_reminder',
                'message': f'Appointment with {appointment.doctor_name} for {appointment.patient.first_name} {appointment.patient.last_name}',
                'date': appointment.appointment_date.isoformat(),
                'priority': 'medium'
            })
        
        # Check for patients with missing critical information
        patients_missing_info = Patient.query.filter(
            Patient.user_id == current_user_id,
            Patient.is_active == True,
            db.or_(
                Patient.emergency_contact_name.is_(None),
                Patient.emergency_contact_phone.is_(None),
                Patient.allergies.is_(None)
            )
        ).limit(5).all()
        
        for patient in patients_missing_info:
            missing_fields = []
            if not patient.emergency_contact_name:
                missing_fields.append('emergency contact')
            if not patient.emergency_contact_phone:
                missing_fields.append('emergency phone')
            if not patient.allergies:
                missing_fields.append('allergies')
            
            notifications.append({
                'type': 'missing_info',
                'message': f'Patient {patient.first_name} {patient.last_name} is missing: {", ".join(missing_fields)}',
                'patient_id': patient.id,
                'priority': 'low'
            })
        
        return jsonify({
            'notifications': notifications
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Notifications error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve notifications'}), 500 