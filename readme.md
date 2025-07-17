# Interior Designer Automation Service

A FastAPI-based automation service that streamlines interior designer workflows by processing client form data, generating AI-powered client profiles, and delivering comprehensive reports via email.

## 🏗️ Architecture Overview

This service is built using modern cloud-native architecture:

- **FastAPI** - High-performance async web framework
- **Google Cloud Run** - Serverless container deployment
- **Google Pub/Sub** - Message queue for client data processing
- **Google Vertex AI** - AI-powered client profile generation
- **Google Cloud Logging** - Centralized logging and monitoring
- **Google Cloud SDK** - For cloud resource management

## 📋 Features

- **Flexible Data Processing**: Accepts any client form structure and adapts dynamically
- **AI-Powered Analysis**: Uses Google Vertex AI to generate detailed client profiles
- **Automated Email Reports**: Sends formatted reports to interior designers
- **Scalable Architecture**: Serverless deployment with automatic scaling
- **Comprehensive Monitoring**: Full observability with health checks and logging

## 🚀 Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **Python 3.11+**
- **uv** - Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Google Cloud SDK** - For authentication and deployment
- **Google Cloud SDK** - For cloud resource management
- **Docker** - For containerization

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd automate-interior-ai-service
   ```

2. **Install dependencies**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync
   ```

3. **Set up Google Cloud authentication**
   ```bash
   # Install Google Cloud SDK if not already installed
   gcloud auth application-default login
   
   # Set your project ID
   gcloud config set project YOUR_PROJECT_ID
   ```

4. **Configure environment variables**
   ```bash
   # Copy example environment file
   cp .env.example .env.local
   
   # Edit .env.local with your configuration
   # Add your Google Cloud project ID, email settings, etc.
   ```

5. **Run the application locally**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

6. **Test the service**
   ```bash
   # Health check
   curl http://localhost:8080/health
   
   # Readiness check
   curl http://localhost:8080/health/readiness
   ```

## 🏗️ Infrastructure Deployment

### Initial Setup

1. **Create Google Cloud resources**
   ```bash
   # Create service account
   gcloud iam service-accounts create interior-ai-service \
     --display-name="Interior AI Service"
   
   # Create Artifact Registry repository
   gcloud artifacts repositories create interior-ai-service \
     --repository-format=docker \
     --location=us-central1
   
   # Create Pub/Sub topic and subscription
   gcloud pubsub topics create client-form-data
   gcloud pubsub subscriptions create client-form-processor \
     --topic=client-form-data
   ```

2. **Set up service account permissions**
   ```bash
   # Add required IAM roles
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:interior-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:interior-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/pubsub.subscriber"
   ```

### Application Deployment

The service automatically deploys via Google Cloud Build when code is pushed to the main branch.

**Manual deployment:**
```bash
# Build and push Docker image
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/interior-ai-service/interior-ai-service:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/interior-ai-service/interior-ai-service:latest

# Deploy to Cloud Run
gcloud run deploy interior-ai-service \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/interior-ai-service/interior-ai-service:latest \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated
```

## 📁 Project Structure

```
automate-interior-ai-service/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   └── middleware/        # FastAPI middleware


├── tests/                 # Test suite
├── dev_docs/             # Development documentation
└── pyproject.toml        # Project configuration
```

## 🧪 Development Workflow

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_services/test_genai_service.py
```

### Local Development Commands

```bash
# Start development server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Run in development mode with debugging
uv run uvicorn app.main:app --reload --log-level debug

# Check application health
curl http://localhost:8080/health/readiness
```

## 🔧 Configuration

### Environment Variables

Key environment variables for local development:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
GENAI_MODEL=gemini-1.5-pro

# Pub/Sub Configuration
PUBSUB_TOPIC=client-form-data
PUBSUB_SUBSCRIPTION=client-form-processor

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DESIGNER_EMAIL=designer@example.com

# Application Configuration
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Environment Variables

Configure environment-specific variables in your `.env.local` file:

- `GOOGLE_CLOUD_PROJECT` - Your Google Cloud project ID
- `VERTEX_AI_LOCATION` - Vertex AI location (e.g., us-central1)
- `PUBSUB_TOPIC` - Pub/Sub topic name
- `PUBSUB_SUBSCRIPTION` - Pub/Sub subscription name

## 📊 Monitoring & Observability

### Health Checks

- **Basic Health**: `GET /health` - Service availability
- **Readiness**: `GET /health/readiness` - Dependencies status

### Logging

- **Local Development**: Console logging with structured format
- **Production**: Google Cloud Logging with JSON format
- **Request Tracing**: Automatic request/response logging

### Metrics

- API response times
- GenAI processing duration
- Email delivery success rates
- Error rates and types

## 🔒 Security

### Authentication

- **Local Development**: Personal Google Cloud credentials
- **Production**: Service account with minimal required permissions

### Data Protection

- Client data is processed in-memory only
- No persistent storage of sensitive information
- Secure email transmission with SMTP authentication

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Error**
   ```bash
   # Re-authenticate with Google Cloud
   gcloud auth application-default login
   ```

2. **Module Import Error**
   ```bash
   # Reinstall dependencies
   uv sync --reinstall
   ```

3. **Port Already in Use**
   ```bash
   # Use different port
   uv run uvicorn app.main:app --reload --port 8081
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
uv run uvicorn app.main:app --reload --log-level debug
```

## 📚 Documentation

- **Implementation Plan**: `dev_docs/implementation_plan.md`
- **Phase Documentation**: `dev_docs/phase-*.md`
- **API Documentation**: Available at `http://localhost:8080/docs` when running

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

### Development Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive tests
- Document public APIs
- Follow functional programming principles

## 📜 License

This project is licensed under the MIT License.

## 🔗 Links

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Google Cloud Run**: https://cloud.google.com/run/docs
- **Google Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Google Cloud SDK**: https://cloud.google.com/sdk/docs
