# Docker Setup for Locust Load Testing

This directory contains Docker Compose configuration for running Locust load tests with different target hosts.

## Quick Start

1. **Set your target host** by creating a `.env` file:
   ```bash
   echo "LOCUST_HOST=https://your-target-host.com" > .env
   echo "LOCUST_SCRIPT_FILE=your_script.py" >> .env
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the Locust Web UI**:
   - Open http://localhost:8089 in your browser
   - Configure your test parameters
   - Start the load test

4. **Access the main API server**:
   - API server runs on http://localhost:9001
   - Health check: http://localhost:8001/health

## Configuration

### Environment Variables

Create a `.env` file in the `scripts` directory with the following variables:

- `LOCUST_HOST`: Target host URL for load testing (default: https://techdev.btspulse.com)
- `LOCUST_SCRIPT_FILE`: Locust script file to run (default: techdev_btspulse_com.py)

### Example .env file:
```
LOCUST_HOST=https://api.example.com
LOCUST_SCRIPT_FILE=my_load_test.py
```

## Services

- **locust-master**: Main Locust coordinator with web UI (port 8089)
- **locust-worker-1,2,3**: Worker nodes that execute the load tests
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Monitoring dashboards (port 3001)

## Running with Different Hosts

### Method 1: Using .env file
```bash
# Create .env file
echo "LOCUST_HOST=https://staging.example.com" > .env
echo "LOCUST_SCRIPT_FILE=staging_test.py" >> .env

# Start services
docker-compose up -d
```

### Method 2: Using environment variables
```bash
LOCUST_HOST=https://production.example.com LOCUST_SCRIPT_FILE=prod_test.py docker-compose up -d
```

### Method 3: Override specific services
```bash
# Run only master with custom host
docker-compose run -e LOCUST_HOST=https://test.example.com locust-master
```

## Troubleshooting

### Port Already in Use
If you get "port is already allocated" errors:
```bash
# Stop all containers
docker-compose down

# Remove any conflicting containers
docker ps -a | grep locust
docker rm <container_id>

# Start again
docker-compose up -d
```

### Script Not Found
Make sure your script file exists in the `scripts` directory:
```bash
ls -la scripts/*.py
```

### Host Connection Issues
- Verify the target host is accessible from Docker containers
- Check if the host requires specific headers or authentication
- Ensure SSL certificates are valid (or disable verification in the script)

## Monitoring

- **Locust Web UI**: http://localhost:8089
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
