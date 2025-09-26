# Mony API

FastAPI-based REST API for intelligent receipt processing and expense management using OpenAI's vision capabilities.

## 🚀 Features

- **Receipt Upload & Analysis**: Upload receipt images and extract structured data
- **AI-Powered Processing**: Uses OpenAI GPT-4o-mini with vision for accurate receipt parsing
- **Multi-language Support**: Automatically detects receipt language and responds accordingly
- **Structured Data Extraction**: Extracts merchant, date, amounts, items, categories, and more
- **Smart Categorization**: Automatically categorizes expenses (groceries, dining, gas, etc.)
- **Currency Detection**: Supports multiple currencies with automatic detection
- **JSON Response Format**: Clean, structured JSON responses for easy integration

## 📋 Requirements

- Python 3.12+
- PostgreSQL database
- OpenAI API key
- Docker (optional, for containerized deployment)
- uv package manager

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mony-api
   ```

2. **Install dependencies using uv**
   ```bash
   # Install uv if you haven't already
   pip install uv

   # Install project dependencies
   uv sync
   ```

   Or install development dependencies:
   ```bash
   # Install with development dependencies
   uv sync --group dev
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` file with your configuration:
   ```env
   # Used by the backend to generate links in emails to the frontend
   FRONTEND_HOST=http://localhost:5173

   # Environment: local, staging, production
   ENVIRONMENT=local

   PROJECT_NAME="Mony API"

   # API
   BACKEND_CORS_ORIGINS="http://localhost,http://localhost:5173,https://localhost,https://localhost:5173"
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Postgres
   PG_SERVER=localhost
   PG_PORT=5432
   PG_DB=monywallet
   PG_USER=your-db-user
   PG_PASSWORD=your-db-password

   # OpenAI
   OPEN_AI_SECRET_KEY=your-openai-api-key-here
   OPEN_AI_MODEL=gpt-4o-mini

   # Azure Configuration (for production)
   AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
   AZURE_CONTAINER_NAME=receipts
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb monywallet
   ```

## 🚀 Usage

### Development

1. **Start the development server**
   ```bash
   uv run fastapi dev app/main.py
   ```

   Or use the startup script (cross-platform):
   ```bash
   ./startup.sh
   ```

### Production with Docker

1. **Build the Docker image**
   ```bash
   docker build -t mony-api .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env mony-api
   ```

2. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📡 API Endpoints

### Upload Receipt

**POST** `/api/receipts`

Upload an image file (PNG, JPEG) and extract receipt data.

**Request:**
- `receipt`: Image file (multipart/form-data)
- Max file size: 10MB
- Supported formats: PNG, JPEG, JPG

**Response:**
```json
{
  "receipt": {
    "merchant": "Store Name",
    "date": "2024-01-15",
    "total_amount": 25.99,
    "currency": "USD",
    "payment_method": "credit card",
    "category": "groceries",
    "description": "Purchase description",
    "receipt_number": "TXN-123456",
    "taxes": 2.34,
    "items": [
      {
        "name": "Product Name",
        "quantity": 1,
        "unit_price": 23.65,
        "total_price": 23.65
      }
    ]
  }
}
```

## 🏗️ Project Structure

```
mony-api/
├── app/
│   ├── api/
│   │   ├── main.py          # API router configuration
│   │   └── routes/
│   │       └── receipts.py  # Receipt processing endpoints
│   ├── main.py              # FastAPI application setup
│   └── settings.py          # Configuration settings
├── alembic/                 # Database migration scripts
│   ├── env.py               # Alembic configuration
│   └── script.py.mako       # Migration template
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_main.py         # Main application tests
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Environment variables template
├── alembic.ini              # Alembic configuration file
├── Dockerfile               # Multi-stage Docker build
├── pyproject.toml           # Project dependencies and configuration
├── startup.sh               # Cross-platform startup script
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── uv.lock                  # Dependency lock file
└── README.md                # This file
```

## 🔧 Configuration

The application uses Pydantic settings for configuration management. Key settings include:

- **Database**: PostgreSQL connection settings with Alembic migrations
- **OpenAI**: API key and model configuration (GPT-4o-mini with vision)
- **CORS**: Cross-origin request settings for frontend integration
- **JWT**: Authentication token configuration
- **File Upload**: Size limits and allowed file types
- **Azure Storage**: Optional cloud storage for production receipts
- **Environment**: Support for local, staging, and production environments

## 🧠 AI Processing

The receipt processing uses OpenAI's GPT-4o-mini model with vision capabilities to:

1. **Extract structured data** from receipt images
2. **Detect language** automatically and respond in the same language
3. **Categorize expenses** based on merchant recognition
4. **Parse financial information** including amounts, taxes, and payment methods
5. **Extract itemized details** with quantities and prices

## 🛡️ Error Handling

The API includes comprehensive error handling for:

- Invalid file types or sizes
- OpenAI API failures
- JSON parsing errors
- Missing or corrupted receipt data
- Database connection issues

## 🧪 Testing

Run tests using pytest:

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app
```

## 🚀 Database Migrations

The project uses Alembic for database schema management:

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Downgrade migrations
uv run alembic downgrade -1
```

## 🛠️ Development Tools

The project includes several development tools:

- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **pytest**: Testing framework

```bash
# Format code
uv run black app/

# Check linting
uv run flake8 app/

# Sort imports
uv run isort app/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Add tests if applicable
6. Submit a pull request

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 📞 Support

For questions or support, please open an issue in the repository.