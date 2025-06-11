# Human Rights Management Information System (MIS)

A comprehensive system for documenting, managing, and analyzing human rights violations. This system provides secure case management, incident reporting, victim/witness protection, and analytical tools for human rights organizations.



## 👥 Development Team

- **1211577** - Aziza Abed
- **1212950** - Fatema Ireqat  
- **1223166** - Abdalkarim Abusalama


## 🚀 Features

### Core Functionality
- **Case Management**: Create, track, and manage human rights violation cases
- **Incident Reporting**: Submit and process incident reports with evidence
- **Victim/Witness Protection**: Secure management of victim and witness information with encryption
- **Analytics & Reporting**: Generate insights and visualizations from collected data
- **Evidence Management**: Secure file upload and storage for case evidence
- **Geographic Mapping**: Location-based visualization of incidents and cases

### Security Features
- **Role-Based Access Control**: Admin, Case Manager, Analyst, and Viewer roles
- **Data Encryption**: Sensitive contact information is encrypted at rest
- **JWT Authentication**: Secure API access with token-based authentication
- **Anonymous Reporting**: Support for anonymous incident reporting

## 🏗️ System Architecture

### Backend (FastAPI)
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **Database**: MongoDB for flexible document storage
- **Authentication**: JWT tokens with role-based permissions
- **File Storage**: Local file system for evidence storage
- **Encryption**: Fernet encryption for sensitive data

### Frontend (Streamlit)
- **Web Interface**: Streamlit-based dashboard and forms
- **Visualizations**: Charts, maps, and analytics dashboards
- **File Upload**: Secure evidence and document upload

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB (local or remote instance)
- Git (for version control)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd human-rights-mis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up MongoDB
Ensure MongoDB is running on your system:
- **Local MongoDB**: Install MongoDB and start the service
- **MongoDB Atlas**: Create a cloud database and get connection string

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=human_rights_mis
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your-encryption-key-here
```

**Important**: Generate secure keys for production:
```python
# Generate SECRET_KEY
import secrets
print(secrets.token_urlsafe(64))

# Generate ENCRYPTION_KEY
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 5. Initialize Database Collections
The system will automatically create necessary collections on first run:
- `cases` - Case management
- `incident_reports` - Incident reports
- `individuals` - Victim/witness records
- `users` - User authentication
- `case_status_history` - Case status tracking
- `report_evidence` - Evidence metadata
- `victim_risk_assessments` - Risk assessment logs

## 🚀 Running the Application

### Option 1: Run Both Services Together
```bash
python run_all.py
```
This will start both the FastAPI backend and Streamlit frontend simultaneously.

### Option 2: Run Services Separately

**Backend Only:**
```bash
uvicorn main:app --reload
```
API will be available at: http://localhost:8000

**Frontend Only:**
```bash
streamlit run streamlit_app.py
```
Web interface will be available at: http://localhost:8501

## 📚 API Documentation

Once the backend is running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 User Roles & Permissions

### Admin
- Full system access
- User management
- Data encryption/decryption
- System configuration

### Case Manager
- Create and manage cases
- Access victim/witness information
- Update case statuses
- Manage evidence

### Analyst
- View cases and reports
- Generate analytics
- Access aggregated data
- Limited victim information access

### Viewer
- Read-only access to public information
- Basic analytics viewing
- No sensitive data access

## 📊 Key Endpoints

### Authentication
- `POST /auth/login` - User login

### Case Management
- `POST /cases/` - Create new case
- `GET /cases/` - List cases with filters
- `GET /cases/{case_id}` - Get specific case
- `PATCH /cases/{case_id}` - Update case status
- `DELETE /cases/{case_id}` - Archive case

### Incident Reporting
- `POST /reports/` - Submit incident report
- `GET /reports/` - List reports with filters
- `PATCH /reports/{report_id}` - Update report status
- `DELETE /reports/{report_id}` - Delete report

### Victim/Witness Management
- `POST /victims/` - Create victim/witness record
- `GET /victims/` - List victims with filters
- `GET /victims/{victim_id}` - Get specific victim
- `PATCH /victims/{victim_id}` - Update victim information

### Analytics
- `GET /analytics/violations` - Violation type statistics
- `GET /analytics/timeline` - Temporal analysis
- `GET /analytics/geodata` - Geographic data for mapping
- `GET /analytics/summary` - System summary statistics

## 📁 Project Structure

```
human-rights-mis/
├── models/
│   ├── user.py          # User authentication models
│   └── victim.py        # Victim/witness data models
├── routers/
│   ├── auth.py          # Authentication endpoints
│   ├── cases.py         # Case management endpoints
│   ├── reports.py       # Incident reporting endpoints
│   ├── victims.py       # Victim/witness endpoints
│   └── analytics.py     # Analytics endpoints
├── security/
│   ├── auth.py          # JWT authentication
│   └── encryption.py    # Data encryption utilities
├── media/               # File storage directory
├── main.py              # FastAPI application
├── db.py                # Database configuration
├── streamlit_app.py     # Frontend application
├── run_all.py           # Launch script
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

## 🔒 Security Considerations

### Data Protection
- All sensitive contact information is encrypted using Fernet encryption
- Passwords are hashed using bcrypt
- JWT tokens for secure API access
- Role-based access control for data protection

### Privacy Features
- Anonymous reporting support
- Pseudonym support for victim protection
- Configurable data visibility based on user roles
- Secure file upload and storage

### Production Recommendations
- Use HTTPS in production
- Implement rate limiting
- Regular security audits
- Backup encryption keys securely
- Use environment variables for all secrets

## 📈 Analytics Features

### Violation Statistics
- Count violations by type
- Temporal trend analysis
- Geographic distribution
- Status tracking

### Visualizations
- Time series charts
- Geographic heat maps
- Violation type breakdowns
- Case status summaries

## 🛠️ Development

### Adding New Features
1. Create new models in `models/`
2. Add endpoints in appropriate router files
3. Update database collections in `db.py`
4. Add frontend components in Streamlit app

### Database Schema
The system uses MongoDB's flexible document structure:
- Cases include location, evidence, and violation details
- Reports contain incident information and evidence
- Victims have encrypted contact info and risk assessments
- Users have role-based permissions

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Error:**
- Verify MongoDB is running
- Check connection string in `.env`
- Ensure database permissions

**Encryption Errors:**
- Verify `ENCRYPTION_KEY` is properly formatted
- Check key generation method
- Ensure consistent key usage

**File Upload Issues:**
- Verify `media/` directory exists
- Check file permissions
- Ensure sufficient disk space

**Authentication Problems:**
- Verify `SECRET_KEY` configuration
- Check JWT token expiration
- Ensure user exists in database

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request



---
