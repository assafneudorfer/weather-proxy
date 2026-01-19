# Weather Proxy API

A production-ready REST API that proxies weather data from the Open-Meteo API with Redis caching, structured logging, and resilience patterns.

## Features

- **Weather Endpoint**: `GET /weather?city={city_name}` - Returns current weather data
- **Health Check**: `GET /health` - Service health status with Redis connectivity
- **Caching**: Redis-based caching with configurable TTL (default 5 minutes)
- **Resilience**: Circuit breaker and retry logic for external API calls
- **Observability**: Structured JSON logging with correlation IDs and request timing
- **API Documentation**: Auto-generated OpenAPI docs at `/docs` and `/redoc`

## Quick Start

### Using Docker Compose (Recommended)

Start the application and Redis with a single command:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -e ".[dev,test]"
   ```

2. **Start Redis** (required):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Run tests**:
   ```bash
   pytest --cov=app
   ```

5. **Run linter**:
   ```bash
   ruff check .
   ruff format .
   ```

## API Usage

### Get Weather

```bash
curl "http://localhost:8000/weather?city=London"
```

Response:
```json
{
  "city": "London",
  "country": "United Kingdom",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "temperature": 15.0,
  "humidity": 80,
  "weather_code": 3,
  "wind_speed": 10.5,
  "timezone": "Europe/London",
  "timestamp": "2024-01-15T14:00",
  "cached": false
}
```

### Health Check

```bash
curl "http://localhost:8000/health"
```

Response:
```json
{
  "status": "healthy",
  "redis_connected": true
}
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_TTL_SECONDS` | `300` | Cache TTL in seconds (5 minutes) |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (`json` for production, `console` for dev) |
| `HTTP_TIMEOUT_SECONDS` | `10.0` | External API request timeout |
| `CIRCUIT_BREAKER_FAIL_MAX` | `5` | Failures before circuit opens |
| `CIRCUIT_BREAKER_RESET_TIMEOUT` | `60` | Seconds before circuit resets |

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client    │────▶│  Weather Proxy  │────▶│  Open-Meteo API │
└─────────────┘     │    (FastAPI)    │     └─────────────────┘
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │      Redis      │
                    │     Cache       │
                    └─────────────────┘
```

### Key Components

- **FastAPI**: Modern async web framework with automatic OpenAPI documentation
- **httpx**: Async HTTP client for external API calls
- **Redis**: Distributed cache for weather data
- **aiobreaker**: Circuit breaker for fault tolerance
- **tenacity**: Retry logic with exponential backoff
- **structlog**: Structured logging with JSON output
- **asgi-correlation-id**: Request tracing with correlation IDs

### Request Flow

1. Client sends request to `/weather?city=London`
2. Middleware assigns correlation ID and logs request start
3. Service checks Redis cache for city
4. On cache miss:
   - Geocoding API converts city name to coordinates
   - Weather API fetches current weather for coordinates
   - Result cached in Redis with TTL
5. Response returned with correlation ID header
6. Middleware logs request duration and status code

### Resilience Patterns

- **Circuit Breaker**: Opens after 5 consecutive failures, resets after 60 seconds
- **Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s) for transient failures
- **Timeout**: 10 second timeout for external API calls
- **Graceful Degradation**: Returns cached data when available, even if stale

## Project Structure

```
qbiq/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── health.py        # Health check endpoint
│   │   ├── router.py        # API router
│   │   └── weather.py       # Weather endpoint
│   ├── core/                # Core modules
│   │   ├── exceptions.py    # Exception handlers
│   │   ├── logging.py       # Structlog configuration
│   │   └── middleware.py    # Request logging middleware
│   ├── schemas/             # Pydantic models
│   │   ├── health.py        # Health response schema
│   │   └── weather.py       # Weather schemas
│   ├── services/            # Business logic
│   │   ├── cache_service.py # Redis caching
│   │   ├── open_meteo_client.py  # External API client
│   │   └── weather_service.py    # Weather orchestration
│   ├── config.py            # Settings
│   ├── dependencies.py      # FastAPI dependencies
│   └── main.py              # Application factory
├── tests/
│   ├── integration/         # API integration tests
│   └── unit/                # Unit tests
├── .github/workflows/       # CI/CD
│   └── ci.yml
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Docker Compose setup
├── pyproject.toml           # Dependencies and config
└── README.md
```

## CI/CD

The GitHub Actions pipeline runs on push to main and pull requests:

1. **Lint**: Ruff linter and formatter checks
2. **Test**: pytest with coverage report
3. **Build**: Docker image build

## Deployment to AWS

This project includes Terraform configurations and a Helm chart to deploy the application to AWS EKS.

### Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) (>= 1.0)
- [Helm](https://helm.sh/docs/intro/install/) (>= 3.0)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (configured with credentials)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

### 1. Provision Infrastructure

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Plan and apply the changes:
   ```bash
   terraform apply
   ```
   Confirm the action by typing `yes`. This will create a VPC, EKS Cluster, and ECR repository.

4. Retrieve the outputs:
   ```bash
   terraform output
   ```
   Note the `ecr_repository_url` and the `configure_kubectl` command.

5. Configure `kubectl` to communicate with the new cluster (use the command from the output):
   ```bash
   aws eks --region us-east-1 update-kubeconfig --name weather-proxy-cluster
   ```

### 2. Build and Push Docker Image

1. Authenticate Docker to your ECR registry:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
   ```

2. Build the Docker image:
   ```bash
   docker build -t weather-proxy .
   ```

3. Tag the image:
   ```bash
   docker tag weather-proxy:latest <ECR_REPOSITORY_URL>:latest
   ```

4. Push the image:
   ```bash
   docker push <ECR_REPOSITORY_URL>:latest
   ```

### 3. Deploy Application with Helm

1. Navigate to the project root.

2. Install the Helm chart:
   ```bash
   helm install weather-proxy ./charts/weather-proxy \
     --set image.repository=<ECR_REPOSITORY_URL> \
     --set image.tag=latest
   ```

### 4. Verify Deployment

1. Check the status of the pods:
   ```bash
   kubectl get pods
   ```

2. Get the Public URL (Load Balancer DNS):
   ```bash
   kubectl get svc weather-proxy
   ```
   Wait for the `EXTERNAL-IP` field to be populated (it may take a few minutes). It will look like `xxx.us-east-1.elb.amazonaws.com`.

3. Test the public endpoint:
   - Weather: `curl "http://<EXTERNAL-IP>/weather?city=Paris"`
   - Health: `curl "http://<EXTERNAL-IP>/health"`
   - Metrics: `curl "http://<EXTERNAL-IP>/metrics"`

### 5. Cleanup

To destroy the infrastructure:
```bash
helm uninstall weather-proxy
cd terraform
terraform destroy
```

## Future Improvements

Given more time, the following enhancements could be made:

### Features
- **Weather Forecast**: Add endpoints for multi-day forecasts
- **Multiple Providers**: Add fallback weather providers for higher availability
- **Rate Limiting**: Implement per-client rate limiting
- **API Key Authentication**: Add optional API key authentication

### Operations
- **Kubernetes Manifests**: Helm charts for Kubernetes deployment
- **Metrics**: Prometheus metrics endpoint for monitoring
- **Distributed Tracing**: OpenTelemetry integration
- **Redis Sentinel/Cluster**: High availability Redis setup

### Code Quality
- **Property-Based Testing**: Hypothesis for edge case testing
- **Load Testing**: Locust or k6 performance tests
- **API Versioning**: `/v1/weather` endpoint versioning
- **Database**: Store historical weather data for analytics

## License

MIT
