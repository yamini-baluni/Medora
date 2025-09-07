from app import create_app, db
from app.models import User, Patient, Appointment

def init_database():
    """Initialize database tables"""
    try:
        print("🔧 Initializing database...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@medora.com',
                password='Admin123!',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("🔧 Please run the database setup script first:")
        print("   python setup_database.py")
        return False
    return True

def main():
    """Main application entry point"""
    print("🚀 Starting Medora Medical Records Management System...")
    print("=" * 60)
    
    # Create Flask app
    app = create_app()
    
    # Initialize database within app context
    with app.app_context():
        if not init_database():
            print("❌ Failed to start application due to database issues.")
            print("Please fix the database connection and try again.")
            return
    
    print("🌐 Starting Flask web server...")
    print("📱 Application will be available at: http://localhost:5000")
    print("🔑 Default login: admin / Admin123!")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
