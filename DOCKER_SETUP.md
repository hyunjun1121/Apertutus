# Docker Setup Guide for Apertutus

This guide provides comprehensive instructions for running Apertutus using Docker, designed to make it easy for jury members and evaluators to run the project.

## 🚀 Quick Start (TL;DR)

```bash
# 1. Clone the repository
git clone <repository-url>
cd Apertutus

# 2. Set up configuration
cp config_example.json config.json
# Edit config.json with your API keys

# 3. Run everything with Docker
docker-compose up --build

# 4. Access the dashboard at http://localhost:3000
```

## 📋 Prerequisites

- **Docker Desktop**: [Download here](https://docs.docker.com/get-docker/)
- **Git**: For cloning the repository
- **API Keys**: Apertus API keys for testing (see Configuration section)

### System Requirements
- **RAM**: At least 4GB available
- **Storage**: At least 2GB free space
- **OS**: Windows 10+, macOS 10.14+, or Linux

## 🏗️ Architecture Overview

The Docker setup includes two main services:

1. **Backend Container** (`apertutus-backend`):
   - Python 3.11 environment
   - All ML dependencies (transformers, torch, etc.)
   - Multilingual translation and safety testing scripts
   - Data processing and evaluation tools

2. **Frontend Container** (`apertutus-frontend`):
   - Next.js dashboard application
   - Interactive data visualization
   - Real-time testing interface
   - Results analysis tools

## 📁 Project Structure

```
Apertutus/
├── Dockerfile.backend          # Python backend container
├── Dockerfile.frontend         # Next.js frontend container
├── docker-compose.yml          # Orchestration configuration
├── .dockerignore              # Files to exclude from containers
├── config_example.json        # Configuration template
├── config.json               # Your API configuration (create this)
├── main.py                   # Main orchestration script
├── requirements_complete.txt  # Python dependencies
├── frontend/                 # Next.js dashboard
│   ├── package.json
│   ├── src/
│   └── ...
├── multilingual_datasets/    # Translation outputs
├── final_results/           # Testing results
└── ...
```

## ⚙️ Configuration

### 1. API Keys Setup

Create your configuration file:
```bash
cp config_example.json config.json
```

Edit `config.json`:
```json
{
  "api_keys": [
    "your-apertus-api-key-1",
    "your-apertus-api-key-2",
    "your-apertus-api-key-3"
  ],
  "api_base_url": "https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b/v1",
  "model_name": "swiss-ai/Apertus-70B",
  "rate_limit": {
    "requests_per_second": 5,
    "tokens_per_minute": 100000
  },
  "languages": [
    {"code": "rus.Cyrl", "name": "Russian"},
    {"code": "cmn.Hani", "name": "Mandarin Chinese"},
    {"code": "deu.Latn", "name": "German"}
  ]
}
```

### 2. Environment Variables (Optional)

You can also set environment variables:
```bash
export APERTUS_API_KEY="your-api-key"
export APERTUS_API_BASE="https://api.swisscom.com/layer/swiss-ai-weeks/apertus-70b/v1"
```

## 🚀 Running the Application

### Method 1: Full Stack (Recommended)

Start both backend and frontend:
```bash
docker-compose up --build
```

This will:
- Build both containers
- Start the backend service
- Start the frontend on http://localhost:3000
- Set up networking between services

### Method 2: Individual Services

Start only the backend:
```bash
docker-compose up backend --build
```

Start only the frontend:
```bash
docker-compose up frontend --build
```

### Method 3: Background Mode

Run in background (detached):
```bash
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f
```

## 🔧 Usage Examples

### Interactive Backend Commands

Execute commands in the running backend container:

```bash
# Get help
docker-compose exec backend python main.py --help

# Run full pipeline (translation + testing)
docker-compose exec backend python main.py

# Translation only
docker-compose exec backend python main.py --translate

# Testing only (requires translated datasets)
docker-compose exec backend python main.py --test

# Test specific languages
docker-compose exec backend python main.py --test --languages kor.Hang fra.Latn deu.Latn

# Sequential processing (single API key)
docker-compose exec backend python main.py --test --no-parallel

# Run specific evaluation scripts
docker-compose exec backend python strongreject_evaluator.py
docker-compose exec backend python multilingual_translator.py
```

### Frontend Dashboard

Access the dashboard at http://localhost:3000 to:
- View real-time testing progress
- Analyze safety evaluation results
- Upload and process custom datasets
- Generate reports and visualizations

### File Access and Data Persistence

Data is persisted using Docker volumes:
```bash
# View generated datasets
docker-compose exec backend ls -la multilingual_datasets/

# Check evaluation results
docker-compose exec backend ls -la final_results/

# Copy files from container to host
docker cp apertutus-backend:/app/final_results ./results_backup
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port already in use (3000)**:
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "3001:3000"  # Use port 3001 instead
   ```

2. **Out of memory**:
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or run with memory limit
   docker-compose up --build --memory=4g
   ```

3. **API key errors**:
   ```bash
   # Check your config.json file
   docker-compose exec backend cat config.json
   
   # Test API connection
   docker-compose exec backend python test_api_connection.py
   ```

4. **Permission issues**:
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Debugging Commands

```bash
# View container logs
docker-compose logs backend
docker-compose logs frontend

# Enter container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Check container status
docker-compose ps

# Rebuild containers
docker-compose build --no-cache

# Clean up
docker-compose down --volumes --rmi all
```

### Performance Optimization

```bash
# Use more API keys for parallel processing
# Edit config.json to add more keys

# Allocate more memory to Docker
# Docker Desktop -> Settings -> Resources -> Memory

# Use SSD storage for better I/O performance
```

## 🧪 Testing the Setup

### Quick Health Check

```bash
# 1. Check if services are running
docker-compose ps

# 2. Test backend
docker-compose exec backend python -c "print('Backend OK')"

# 3. Test frontend (should return HTTP 200)
curl http://localhost:3000

# 4. Test API configuration
docker-compose exec backend python test_api_connection.py
```

### Sample Workflow

```bash
# 1. Start services
docker-compose up -d --build

# 2. Run a small test
docker-compose exec backend python main.py --test --languages kor.Hang

# 3. Check results
docker-compose exec backend ls -la final_results/

# 4. View in dashboard
# Open http://localhost:3000 in browser
```

## 📊 Monitoring and Logs

### Real-time Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# View resource usage
docker stats
```

### Log Files

Logs are stored in the `logs/` directory:
```bash
# View application logs
docker-compose exec backend tail -f logs/translation.log
docker-compose exec backend tail -f logs/evaluation.log
```

## 🔒 Security Considerations

1. **API Keys**: Never commit `config.json` to version control
2. **Network**: Services communicate only within Docker network
3. **Volumes**: Data persists only in designated volumes
4. **Ports**: Only frontend port (3000) is exposed to host

## 📦 Cleanup

### Stop Services
```bash
docker-compose down
```

### Remove All Data
```bash
# WARNING: This removes all data
docker-compose down --volumes
```

### Complete Cleanup
```bash
# Remove containers, networks, images, and volumes
docker-compose down --rmi all --volumes --remove-orphans

# Clean up Docker system
docker system prune -a
```

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review container logs: `docker-compose logs`
3. Ensure Docker Desktop is running and updated
4. Verify your `config.json` file is properly formatted
5. Check system requirements and available resources

## 📝 Notes for Jury/Evaluators

- **No complex setup required**: Just Docker and API keys
- **Consistent environment**: Works the same on any system
- **Easy testing**: Use the web dashboard for quick evaluation
- **Reproducible results**: All dependencies are containerized
- **Data persistence**: Results are saved between runs
- **Scalable**: Add more API keys for faster processing
