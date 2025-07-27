# Interior Designer Automation Service

A FastAPI-based automation service that streamlines interior designer workflows by processing client form data, generating AI-powered client profiles, and delivering comprehensive reports via email.

## 🏗️ Architecture Overview

This service is built using modern cloud-native architecture:

- **FastAPI** - High-performance async web framework
- **Google Cloud Run** - Serverless container deployment
- **Google Pub/Sub** - Message queue for client data processing
- **Google Vertex AI** - AI-powered client profile generation
- **Google Cloud Logging** - Centralized logging and monitoring
- **Google Cloud Build** - CI/CD pipeline for automated deployment
- **Google Artifact Registry** - Container image storage
- **Google Secret Manager** - Secure secret management

## 📋 Features

- **Flexible Data Processing**: Accepts any client form structure and adapts dynamically
- **AI-Powered Analysis**: Uses Google Vertex AI to generate detailed client profiles
- **Automated Email Reports**: Sends formatted reports to interior designers
- **Scalable Architecture**: Serverless deployment with automatic scaling
- **Comprehensive Monitoring**: Full observability with health checks and logging
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Security First**: All sensitive data stored in Google Secret Manager

## 🚀 Quick Start

### Prerequisites

Before getting started, ensure you have the following installed:

- **Python 3.11+**
- **uv** - Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Google Cloud SDK** - For authentication and deployment
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

4. **Run the application locally**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

5. **Test the service**
   ```bash
   # Health check
   curl http://localhost:8080/health
   
   # Readiness check
   curl http://localhost:8080/health/readiness
   
   # Test webhook endpoint
   curl -X POST http://localhost:8080/webhooks/test \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

## 🏗️ Infrastructure Deployment

### Automated Setup (Recommended)

The project includes an automated setup script that creates all necessary Google Cloud resources:

```bash
# Make the script executable
chmod +x setup-cloudbuild.sh

# Run the setup script
./setup-cloudbuild.sh
```

This script will create:
- ✅ Service accounts with proper permissions
- ✅ Artifact Registry repository
- ✅ Cloud Storage bucket for build artifacts
- ✅ Secret Manager secrets
- ✅ All required IAM roles

### Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

1. **Create Google Cloud resources**
   ```bash
   # Create service accounts
   gcloud iam service-accounts create interior-ai-service \
     --display-name="Interior AI Service"
   
   gcloud iam service-accounts create cloud-build-deployer \
     --display-name="Cloud Build Deployer"
   
   # Create Artifact Registry repository
   gcloud artifacts repositories create interior-ai-service \
     --repository-format=docker \
     --location=europe-north1
   
   # Create Pub/Sub topic
   gcloud pubsub topics create form-submissions-topic
   ```

2. **Set up service account permissions**
   ```bash
   # Add required IAM roles for Interior AI Service
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:interior-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:interior-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/pubsub.publisher"
   
   # Add required IAM roles for Cloud Build
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:cloud-build-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   ```

3. **Create secrets in Secret Manager**
   ```bash
   # Create service account key
   gcloud iam service-accounts keys create interior-ai-service-key.json \
     --iam-account=interior-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
   
   # Store in Secret Manager
   gcloud secrets create interior-ai-service-credentials \
     --replication-policy=automatic
   
   cat interior-ai-service-key.json | gcloud secrets versions add interior-ai-service-credentials \
     --data-file=-
   
   # Create designer email secret
   echo "YOUR_DESIGNER_EMAIL@example.com" | gcloud secrets versions add designer-email \
     --data-file=-
   
   # Clean up key file
   rm interior-ai-service-key.json
   ```

### CI/CD Setup

1. **Connect your GitHub repository to Cloud Build**
   - Go to Google Cloud Console → Cloud Build → Triggers
   - Click "Connect Repository"
   - Select your GitHub repository

2. **Create Cloud Build trigger**
   - Name: `interior-ai-service`
   - Repository: Your connected repository
   - Branch: `master` (or your default branch)
   - Build configuration: `cloudbuild.yaml`
   - Service account: `cloud-build-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com`

3. **Test the pipeline**
   ```bash
   git push origin master
   ```

## 📁 Project Structure

```
automate-interior-ai-service/
├── app/                    # Main application code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── routers/           # API endpoints
│   │   ├── health.py      # Health check endpoints
│   │   └── webhooks.py    # Pub/Sub webhook handler
│   ├── services/          # Business logic
│   │   ├── genai_service.py    # Google Vertex AI integration
│   │   ├── email_service.py    # Email delivery service
│   │   └── pubsub_service.py   # Pub/Sub message processing
│   ├── models/            # Data models
│   │   ├── client_data.py      # Client form data models
│   │   ├── client_profile.py   # AI-generated profile models
│   │   └── email_models.py     # Email content models
│   ├── utils/             # Utility functions
│   │   ├── errors.py      # Error handling utilities
│   │   ├── logging.py     # Structured logging
│   │   └── validators.py  # Data validation
│   └── middleware/        # FastAPI middleware
│       ├── error_handler.py    # Global error handling
│       └── logging_middleware.py # Request/response logging
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── dev_docs/             # Development documentation
├── cloudbuild.yaml       # CI/CD configuration
├── setup-cloudbuild.sh   # Infrastructure setup script
├── Dockerfile            # Container configuration
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

# Security scanning
uv run bandit -r app/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_genai_service.py

# Run integration tests
uv run pytest tests/integration/
```

### Local Testing

```bash
# Test Pub/Sub webhook locally
./test_pubsub.sh

# Test simple webhook locally
./test_simple.sh
```

## 🔧 Configuration

### Environment Variables

The application uses Google Cloud's built-in environment variable resolution and Secret Manager integration.

**Local Development:**
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=europe-north1
GENAI_MODEL=gemini-2.5-pro

# Pub/Sub Configuration
PUBSUB_TOPIC=form-submissions-topic

# Application Configuration
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

**Production (via Cloud Run):**
- All sensitive data is stored in Google Secret Manager
- Environment variables are set via Cloud Build
- Service account credentials are automatically managed

## 📊 Monitoring & Observability

### Health Checks

- **Basic Health**: `GET /health` - Service availability
- **Readiness**: `GET /health/readiness` - Dependencies status
- **Services**: `GET /health/services` - Detailed service status

### Logging

- **Local Development**: Console logging with structured format
- **Production**: Google Cloud Logging with JSON format
- **Request Tracing**: Automatic request/response logging
- **Performance Monitoring**: Built-in timing and metrics

### Metrics

- API response times
- GenAI processing duration
- Email delivery success rates
- Error rates and types
- Pub/Sub message processing metrics

## 🔒 Security

### Authentication & Authorization

- **Local Development**: Personal Google Cloud credentials
- **Production**: Service account with minimal required permissions
- **Secret Management**: All sensitive data in Google Secret Manager

### Data Protection

- Client data is processed in-memory only
- No persistent storage of sensitive information
- Secure email transmission with SMTP authentication
- All secrets encrypted at rest

### Repository Security

- ✅ No hardcoded credentials in code
- ✅ No sensitive data in configuration files
- ✅ All secrets managed via Google Secret Manager
- ✅ Safe for public repository

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

4. **Cloud Build Trigger Issues**
   ```bash
   # Check trigger status
   gcloud builds triggers list
   
   # Check build history
   gcloud builds list
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
- Keep secrets out of code

## 📜 License

This project is licensed under the MIT License.

## 🔗 Links

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Google Cloud Run**: https://cloud.google.com/run/docs
- **Google Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Google Cloud Build**: https://cloud.google.com/build/docs
- **Google Secret Manager**: https://cloud.google.com/secret-manager/docs
