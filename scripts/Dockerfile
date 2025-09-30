# Use Python slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies including Locust and required packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir locust prometheus-client requests urllib3

# Copy the scripts directory (current directory)
COPY . ./scripts/

# Create results directory
RUN mkdir -p /app/results

# Expose ports for Locust web UI, master communication, and Prometheus metrics
EXPOSE 8089 5557 8002

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8089/', timeout=5)" || exit 1

# Default entrypoint is locust, so we can pass args at runtime
ENTRYPOINT ["locust"]
