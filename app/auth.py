from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.models import User
from app.middleware import validate_email, validate_password, validate_phone, handle_validation_errors
from app import db
import uuid
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        print("🔍 REGISTRATION STARTED")
        data = request.get_json()
        
        if not data:
            print("❌ No data provided")
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"📝 Received data: {data}")
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                print(f"❌ Missing required field: {field}")
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            print(f"❌ Invalid email format: {data['email']}")
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            print(f"❌ Password validation failed: {message}")
            return jsonify({'error': message}), 400
        
        # Validate phone if provided
        if data.get('phone') and not validate_phone(data['phone']):
            print(f"❌ Invalid phone format: {data['phone']}")
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            print(f"❌ Username already exists: {data['username']}")
            return jsonify({'error': 'Username already exists'}), 409
        
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            print(f"❌ Email already exists: {data['email']}")
            return jsonify({'error': 'Email already exists'}), 409
        
        print("✅ All validations passed")
        
        # Create new user
        try:
            print("👤 Creating User object...")
            user = User(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone'),
                role=data.get('role', 'user')
            )
            
            print(f"✅ User object created: {user.username}")
            print(f"🔐 Password hash length: {len(user.password_hash) if user.password_hash else 0}")
            
            # Add to session
            print("📝 Adding user to database session...")
            db.session.add(user)
            print("✅ User added to session")
            
            # Commit to database
            print("💾 Committing to database...")
            db.session.commit()
            print("✅ User committed to database successfully")
            
            # VERIFICATION STEP: Confirm data is actually saved
            print("🔍 VERIFYING DATA SAVED TO DATABASE...")
            
            # Query the database to confirm the user exists
            saved_user = User.query.filter_by(username=data['username']).first()
            if saved_user:
                print(f"✅ VERIFICATION SUCCESSFUL: User found in database with ID: {saved_user.id}")
                print(f"✅ Username: {saved_user.username}")
                print(f"✅ Email: {saved_user.email}")
                print(f"✅ First Name: {saved_user.first_name}")
                print(f"✅ Last Name: {saved_user.last_name}")
                print(f"✅ Role: {saved_user.role}")
                print(f"✅ Created At: {saved_user.created_at}")
                
                # Also verify password hash was created
                if saved_user.password_hash:
                    print(f"✅ Password Hash: {saved_user.password_hash[:20]}... (truncated)")
                else:
                    print("❌ PASSWORD HASH MISSING!")
                    
            else:
                print("❌ VERIFICATION FAILED: User not found in database after commit!")
                return jsonify({'error': 'User was not saved to database'}), 500
            
        except Exception as user_error:
            print(f"❌ Error creating user object: {str(user_error)}")
            print(f"❌ Error type: {type(user_error).__name__}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            db.session.rollback()
            return jsonify({'error': f'User creation failed: {str(user_error)}'}), 500
        
        # Generate tokens
        try:
            print("🔑 Generating JWT tokens...")
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            print("✅ Tokens generated successfully")
        except Exception as token_error:
            print(f"❌ Error generating tokens: {str(token_error)}")
            return jsonify({'error': f'Token generation failed: {str(token_error)}'}), 500
        
        print("🎉 REGISTRATION COMPLETED SUCCESSFULLY")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'verification': {
                'database_id': saved_user.id,
                'saved_at': saved_user.created_at.isoformat() if saved_user.created_at else None,
                'password_hashed': bool(saved_user.password_hash)
            }
        }), 201
        
    except Exception as e:
        print(f"❌ REGISTRATION ERROR: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and issue JWT token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'phone']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Validate phone if updated
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users for admin management"""
    try:
        # Get current user to check if admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get all users with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = User.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        user_list = []
        for user in users.items:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                'total_patients': len(user.patients) if user.patients else 0
            }
            user_list.append(user_data)
        
        return jsonify({
            'users': user_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user information (admin only)"""
    try:
        # Check if current user is admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get user to update
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'phone', 'role', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {str(e)}")
        return jsonify({'error': 'Failed to update user'}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        # Check if current user is admin
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Prevent admin from deleting themselves
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Get user to delete
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Soft delete - just deactivate
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'User deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check for database connectivity"""
    try:
        # Test database connection
        user_count = User.query.count()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'user_count': user_count,
            'message': 'Database connection is working'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'message': 'Database connection failed'
        }), 500

@auth_bp.route('/test-db', methods=['GET'])
def test_database():
    """Test database connectivity and user creation"""
    try:
        print("🧪 Testing database connectivity...")
        
        # Test 1: Count existing users
        user_count = User.query.count()
        print(f"✅ Current user count: {user_count}")
        
        # Test 2: Try to create a test user
        print("🧪 Creating test user...")
        test_user = User(
            username='test_db_user',
            email='testdb@example.com',
            password='Test123!',
            first_name='Test',
            last_name='DB',
            role='user'
        )
        
        print(f"✅ Test user object created: {test_user.username}")
        print(f"🔐 Password hash: {test_user.password_hash[:20] if test_user.password_hash else 'None'}...")
        
        # Test 3: Add to session
        db.session.add(test_user)
        print("✅ Test user added to session")
        
        # Test 4: Commit
        db.session.commit()
        print("✅ Test user committed to database")
        
        # Test 5: Verify it was saved
        saved_user = User.query.filter_by(username='test_db_user').first()
        if saved_user:
            print(f"✅ Test user verified in database with ID: {saved_user.id}")
            
            # Test 6: Clean up - delete test user
            db.session.delete(saved_user)
            db.session.commit()
            print("✅ Test user cleaned up")
            
            return jsonify({
                'status': 'success',
                'message': 'Database test completed successfully',
                'user_count': user_count,
                'test_user_created': True,
                'test_user_id': saved_user.id
            }), 200
        else:
            print("❌ Test user not found after commit!")
            return jsonify({
                'status': 'error',
                'message': 'Test user was not saved to database',
                'user_count': user_count
            }), 500
            
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Database test failed: {str(e)}',
            'error_type': type(e).__name__
        }), 500

@auth_bp.route('/verify-users', methods=['GET'])
def verify_users():
    """Verify all users in database (for debugging)"""
    try:
        # Get all users
        users = User.query.all()
        
        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'password_hash_exists': bool(user.password_hash),
                'password_hash_preview': user.password_hash[:20] + '...' if user.password_hash else 'None'
            }
            user_list.append(user_data)
        
        return jsonify({
            'message': f'Found {len(users)} users in database',
            'users': user_list,
            'total_count': len(users)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"User verification error: {str(e)}")
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client should discard tokens)"""
    try:
        # In a real application, you might want to blacklist the token
        # For now, we'll just return a success message
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500 