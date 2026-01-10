# Internal File Sharing System

A web-based internal file sharing system designed for 15 users to upload, download, browse, and manage GB-sized files with bidirectional sync to a Windows server.

## Features

- **User Authentication**: Secure login with password policies and account lockout
- **File Management**: Upload, download, browse, and manage GB-sized files
- **Chunked Upload**: Support for large file uploads with resume capability
- **Soft Delete**: 90-day retention period for deleted files
- **Bidirectional Sync**: Automatic sync with Windows server using Rclone
- **Scheduler Management**: Admin interface to manage scheduled tasks
- **Admin Dashboard**: Monitor storage, users, and system health
- **Audit Logging**: Complete audit trail of all user actions

## Tech Stack

- **Backend**: Python FastAPI 0.109+
- **Frontend**: Vue.js 3 (Composition API)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0 (Async)
- **Task Scheduler**: APScheduler
- **File Sync**: Rclone
- **Web Server**: Nginx (reverse proxy)

## Project Structure

```
internal-file-sharing/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # API routes
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Utilities
│   │   └── scheduler/   # APScheduler tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # Vue.js frontend
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/      # Pinia stores
│   │   └── services/    # API calls
│   ├── package.json
│   └── Dockerfile
├── data/                 # File storage (gitignored)
├── nginx/               # Nginx configuration
├── docker-compose.yml
└── .env.example

```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/manippoudel/internal-file-sharing.git
cd internal-file-sharing
```

2. Copy and configure environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL database:
```bash
# Install PostgreSQL 15+
# Create database: filedb
# Update DATABASE_URL in .env
```

4. Run the backend:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## Configuration

See `.env.example` for all configuration options. Key settings:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for JWT tokens (change in production!)
- `STORAGE_PATH`: Base path for file storage
- `MAX_UPLOAD_SIZE`: Maximum file upload size (default: 10GB)
- `CHUNK_SIZE`: Upload chunk size (default: 50MB)

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

## Security

- HTTPS/SSL encryption (configured via Nginx)
- Password hashing with bcrypt
- JWT-based session management
- Account lockout after failed login attempts
- Rate limiting
- CORS protection
- File path traversal prevention

## Development Status

This project is currently in initial development. See the requirements document for detailed specifications.

## Documentation

- [Requirements Document](./# Internal File Sharing System - Require.md)
- API Documentation: http://localhost:8000/docs (when running)

## License

Internal use only.

## Support

For issues or questions, please contact the development team.