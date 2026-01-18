# BHV Platform

A FastAPI-based web application for image gallery and narrative management.

## Features

- User authentication with Google OAuth
- Image upload and gallery management
- Admin dashboard
- Fuzzy emotion analysis
- Secure API with JWT tokens

## Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements/base.in`
5. Copy `.env.example` to `.env` and fill in your secrets
6. Run the application: `python main.py`

## Docker Support

### Prerequisites

- Docker and Docker Compose installed

### Quick Start

1. Copy `.env.example` to `.env` and fill in your secrets
2. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Access the application at http://localhost:8000

### Docker Commands

- Build the image: `docker build -t bhv-app .`
- Run the container: `docker run -p 8000:8000 --env-file .env bhv-app`
- Stop containers: `docker-compose down`
- View logs: `docker-compose logs`

### Security Features

- Non-root user in container
- Multi-stage build for minimal image size
- Environment variables for secrets management
- Health checks for container monitoring

### Volumes

- `users.db`: SQLite database persistence
- `static/uploads`: User uploaded images
- `cleaned_data.json`: Processed data file

## Testing

Run tests with: `pytest`

## License

See LICENSE file for details.
