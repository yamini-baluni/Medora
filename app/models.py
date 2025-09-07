from datetime import datetime
import bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from flask_sqlalchemy import SQLAlchemy

# Create a local db instance that will be initialized by the Flask app
db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')  # user, admin, doctor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = db.relationship('Patient', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, first_name, last_name, phone=None, role='user'):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.role = role
        # Hash password immediately
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Hash password and store"""
        if password:
            try:
                # Generate salt and hash password
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                self.password_hash = password_hash.decode('utf-8')
                print(f"DEBUG: Password hashed successfully for {self.username}")
            except Exception as e:
                print(f"DEBUG: Password hashing failed for {self.username}: {e}")
                # Fallback to simple hash if bcrypt fails
                import hashlib
                self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """Verify password against hash"""
        if not self.password_hash:
            return False
        try:
            # Try bcrypt first
            if self.password_hash.startswith('$2b$'):
                return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
            else:
                # Fallback to SHA256
                import hashlib
                return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
        except Exception as e:
            print(f"DEBUG: Password check failed: {e}")
            return False
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    """Enhanced Patient model for storing comprehensive patient information"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)  # Custom patient ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer)  # Calculated field
    gender = db.Column(db.String(10), nullable=False)  # Male, Female, Other
    
    # Contact Information
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    
    # Medical Information
    medical_history = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    blood_type = db.Column(db.String(5))  # A+, B+, AB+, O+, A-, B-, AB-, O-
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    
    # Emergency Contact Information
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))
    
    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_number = db.Column(db.String(50))
    
    # System Fields
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, patient_id, user_id, first_name, last_name, date_of_birth, gender, **kwargs):
        self.patient_id = patient_id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        
        # Calculate age from date of birth
        if date_of_birth:
            today = datetime.now().date()
            self.age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @hybrid_property
    def full_name(self):
        """Get patient's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @hybrid_property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight and self.height > 0:
            height_m = self.height / 100  # Convert cm to meters
            return round(self.weight / (height_m * height_m), 1)
        return None
    
    @hybrid_property
    def bmi_category(self):
        """Get BMI category"""
        bmi = self.bmi
        if bmi is None:
            return None
        elif bmi < 18.5:
            return 'Underweight'
        elif bmi < 25:
            return 'Normal weight'
        elif bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'
    
    def to_dict(self):
        """Convert patient to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'medical_history': self.medical_history,
            'current_medications': self.current_medications,
            'allergies': self.allergies,
            'blood_type': self.blood_type,
            'height': self.height,
            'weight': self.weight,
            'bmi': self.bmi,
            'bmi_category': self.bmi_category,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'insurance_provider': self.insurance_provider,
            'insurance_number': self.insurance_number,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Patient {self.patient_id} - {self.full_name}>'

class Appointment(db.Model):
    """Appointment model for scheduling doctor visits"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_type = db.Column(db.String(50))  # Checkup, Consultation, Emergency, etc.
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='appointments')
    
    def to_dict(self):
        """Convert appointment to dictionary"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_name': self.doctor_name,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_type': self.appointment_type,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'notes': self.notes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.patient_id} on {self.appointment_date}>' 