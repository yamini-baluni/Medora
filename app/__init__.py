from flask import Flask, send_from_directory, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from datetime import timedelta

# Import the local db instance from models
from app.models import db

# Initialize other extensions
migrate = Migrate()
jwt = JWTManager()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'mysql+pymysql://medora_user:medora123@localhost/medora_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Missing token'}), 401
    
    # Register blueprints - use lazy imports to avoid circular dependencies
    def register_blueprints():
        from app.auth import auth_bp
        from app.patients import patients_bp
        from app.dashboard import dashboard_bp
        from app.appointments import appointments_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api')
        app.register_blueprint(patients_bp, url_prefix='/api')
        app.register_blueprint(dashboard_bp, url_prefix='/api')
        app.register_blueprint(appointments_bp, url_prefix='/api')
    
    # Register blueprints after all models are loaded
    register_blueprints()
    
    # Route for serving the main page
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    # Route for serving the new Add Patient page
    @app.route('/add-patient')
    def add_patient():
        return send_from_directory('static', 'add-patient.html')
    
    # Route for serving the Sign In page
    @app.route('/signin')
    def signin():
        return send_from_directory('static', 'signin.html')
    
    # Route for serving the Register page
    @app.route('/register')
    def register():
        return send_from_directory('static', 'register.html')
    
    # Route for serving the Dashboard page
    @app.route('/dashboard')
    def dashboard():
        return send_from_directory('static', 'dashboard.html')
    
    # Route for serving the Appointments page
    @app.route('/appointments')
    def appointments():
        return send_from_directory('static', 'appointments.html')
    
    # Route for serving the Medical Records page
    @app.route('/medical-records')
    def medical_records():
        return send_from_directory('static', 'medical-records.html')
    
    # Route for serving the Prescriptions page
    @app.route('/prescriptions')
    def prescriptions():
        return send_from_directory('static', 'prescriptions.html')
    
    # Route for serving the Billing page
    @app.route('/billing')
    def billing():
        return send_from_directory('static', 'billing.html')
    
    # Compute root-level static directory (../static)
    ROOT_STATIC_DIR = os.path.abspath(os.path.join(app.root_path, '..', 'static'))

    def serve_static_anywhere(filename):
        """Serve a file from app/static first, then project-level /static."""
        try:
            return send_from_directory('static', filename)
        except Exception:
            try:
                return send_from_directory(ROOT_STATIC_DIR, filename)
            except Exception:
                return {'error': 'Resource not found'}, 404

    # Route for serving the Admin Dashboard page
    @app.route('/admin-dashboard')
    def admin_dashboard():
        return serve_static_anywhere('admin-dashboard.html')
    
    # Route for serving the Doctor Dashboard page
    @app.route('/doctor-dashboard')
    def doctor_dashboard():
        return serve_static_anywhere('doctor-dashboard.html')
    
    # Route for serving the Patient Dashboard page
    @app.route('/patient-dashboard')
    def patient_dashboard():
        return serve_static_anywhere('patient-dashboard.html')
    
    # Route for serving static files (must be last to avoid catching API routes)
    @app.route('/<path:filename>')
    def static_files(filename):
        # Don't serve files if the path starts with /api
        if filename.startswith('api/'):
            return {'error': 'API endpoint not found'}, 404
        return serve_static_anywhere(filename)
    
    # Request context handlers
    @app.before_request
    def before_request():
        """Ensure database session is available for each request"""
        pass
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Clean up database session after application context ends"""
        if exception:
            db.session.rollback()
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Clean up database session after each request"""
        if exception:
            db.session.rollback()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app
