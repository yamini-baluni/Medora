# Medora - Medical Records Management System

Medora is a comprehensive web application for managing medical records, patient information, and appointments. Built with Flask backend, HTML/CSS/JavaScript frontend, and MySQL database.

## Features

- **User Authentication**: Secure login/register system with JWT tokens
- **Patient Management**: Create, read, update, and delete patient records
- **Dashboard**: Comprehensive overview with statistics and recent data
- **Search & Filter**: Advanced patient search and filtering capabilities
- **Responsive Design**: Mobile-friendly interface
- **Role-based Access**: Support for different user roles (user, doctor, admin)
- **Data Validation**: Comprehensive input validation and error handling

## Technology Stack

### Backend
- **Flask**: Python web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-JWT-Extended**: JWT authentication
- **Flask-CORS**: Cross-origin resource sharing
- **PyMySQL**: MySQL database connector
- **bcrypt**: Password hashing

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with Flexbox and Grid
- **JavaScript (ES6+)**: Vanilla JavaScript with async/await
- **Font Awesome**: Icons

### Database
- **MySQL**: Relational database
- **SQLAlchemy**: Database abstraction layer

## Prerequisites

- Python 3.8+
- MySQL 5.7+ or MySQL 8.0+
- pip (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd medora2.0
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Option A: Using the SQL Script
1. Open MySQL command line or MySQL Workbench
2. Run the `database_setup.sql` script:
```bash
mysql -u root -p < database_setup.sql
```

#### Option B: Manual Setup
1. Create a new MySQL database:
```sql
CREATE DATABASE medora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Create a MySQL user (optional but recommended):
```sql
CREATE USER 'medora_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON medora_db.* TO 'medora_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=medora_db
DB_PORT=3306

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here_change_in_production

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_flask_secret_key_here_change_in_production

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

**Important**: Change the default passwords and secret keys in production!

### 6. Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Default Login

After setup, you can log in with the default admin account:
- **Username**: admin
- **Password**: Admin123!

**Important**: Change this password immediately in production!

## Project Structure

```
medora2.0/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── auth.py              # Authentication routes
│   ├── patients.py          # Patient management routes
│   ├── dashboard.py         # Dashboard routes
│   ├── middleware.py        # Custom middleware
│   └── static/
│       ├── index.html       # Main HTML page
│       ├── styles.css       # CSS styles
│       └── script.js        # JavaScript functionality
├── config.py                # Configuration settings
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── database_setup.sql       # Database setup script
└── README.md               # This file
```

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/refresh` - Refresh JWT token
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile

### Patients
- `GET /api/patients` - Get all patients (with pagination and filters)
- `POST /api/patients` - Create new patient
- `GET /api/patients/<id>` - Get specific patient
- `PUT /api/patients/<id>` - Update patient
- `DELETE /api/patients/<id>` - Delete patient (soft delete)
- `GET /api/patients/search?q=<term>` - Search patients
- `GET /api/patients/<id>/appointments` - Get patient appointments

### Dashboard
- `GET /api/dashboard` - Get dashboard data and statistics
- `GET /api/dashboard/quick-stats` - Get quick statistics
- `GET /api/dashboard/notifications` - Get user notifications

## Usage

### 1. User Registration/Login
- Navigate to the application
- Use the login/register tabs to create an account or sign in
- JWT tokens are automatically managed

### 2. Dashboard
- View overall statistics
- See recent patients and upcoming appointments
- Quick overview of your medical practice

### 3. Patient Management
- Add new patients with comprehensive information
- Search and filter existing patients
- Edit patient details
- View patient history

### 4. Profile Management
- Update personal information
- Change contact details

## Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS Protection**: Configurable cross-origin settings
- **Role-based Access Control**: Different permissions for different user types

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python run.py
```

### Database Migrations

The application uses Flask-Migrate for database migrations:

```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Testing

```bash
# Run tests (if test suite is implemented)
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

## Production Deployment

### 1. Environment Variables
- Set `FLASK_ENV=production`
- Set `FLASK_DEBUG=False`
- Use strong, unique secret keys
- Configure production database credentials

### 2. Database
- Use production MySQL instance
- Configure connection pooling
- Set up regular backups
- Monitor performance

### 3. Web Server
- Use Gunicorn or uWSGI with Flask
- Configure Nginx as reverse proxy
- Set up SSL/TLS certificates
- Configure logging

### 4. Security
- Change default passwords
- Use environment variables for secrets
- Enable HTTPS
- Configure firewall rules
- Regular security updates

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify MySQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Import Errors**
   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **JWT Token Issues**
   - Check JWT_SECRET_KEY in `.env`
   - Clear browser localStorage
   - Verify token expiration settings

4. **CORS Issues**
   - Check CORS configuration in `config.py`
   - Verify frontend URL in CORS settings

### Logs

Check Flask application logs for detailed error information:

```bash
# Enable debug logging
export FLASK_DEBUG=True
python run.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## Changelog

### Version 1.0.0
- Initial release
- User authentication system
- Patient management
- Dashboard with statistics
- Responsive web interface

## Acknowledgments

- Flask community for the excellent web framework
- SQLAlchemy for robust database ORM
- Font Awesome for beautiful icons
- Open source community for various libraries and tools 