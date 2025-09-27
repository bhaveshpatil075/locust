# HAR File Upload API

A simple FastAPI backend for uploading HAR (HTTP Archive) files.

## Features

- POST `/upload` - Upload HAR files and save them to the `/uploads` directory
- POST `/convert` - Convert HAR files to flow format with detailed analysis
- POST `/generate` - Generate Locust performance testing scripts from flow data
- GET `/scripts` - List all available Locust scripts
- GET `/run` - Execute Locust scripts and get UI URL
- GET `/stop/{process_id}` - Stop running Locust processes
- GET `/status` - Monitor running processes
- File validation to ensure only `.har` files are accepted
- Error handling and proper HTTP status codes
- Health check endpoint

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /upload
Upload a HAR file to the server.

**Request:**
- Content-Type: `multipart/form-data`
- Body: HAR file

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "example.har",
  "file_size": 12345,
  "file_path": "uploads/example.har"
}
```

### POST /convert
Convert a HAR file to flow format with detailed analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Body: HAR file

**Response:**
```json
{
  "message": "HAR file converted to flow successfully",
  "filename": "example.har",
  "flow_data": {
    "metadata": {
      "version": "1.2",
      "creator": {...},
      "browser": {...},
      "total_entries": 5,
      "converted_at": "2024-01-01T00:00:00Z"
    },
    "flows": [
      {
        "id": "flow_1",
        "name": "Request 1",
        "method": "GET",
        "url": "https://example.com/api/data",
        "status_code": 200,
        "response_time": 150,
        "request_headers": [...],
        "response_headers": [...],
        "timestamp": "2024-01-01T10:00:00.000Z",
        "flow_type": "http_request"
      }
    ],
    "summary": {
      "total_requests": 5,
      "unique_domains": 2,
      "methods": ["GET", "POST"],
      "status_codes": [200, 404]
    }
  }
}
```

### POST /generate
Generate a Locust performance testing script from flow data.

**Request:**
- Content-Type: `application/json`
- Body: Flow data (from /convert endpoint)

**Response:**
```json
{
  "message": "Locust script generated successfully",
  "filename": "locust_script_20240101_120000.py",
  "file_path": "scripts/locust_script_20240101_120000.py",
  "file_size": 2048,
  "total_requests": 5,
  "script_preview": "Generated Locust script from HAR file..."
}
```

### GET /scripts
List all available Locust scripts.

**Response:**
```json
{
  "message": "Scripts listed successfully",
  "total_scripts": 2,
  "scripts": [
    {
      "filename": "locust_script_20240101_120000.py",
      "file_path": "scripts/locust_script_20240101_120000.py",
      "file_size": 2048,
      "created_at": "2024-01-01T12:00:00",
      "modified_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### GET /run
Execute a Locust script and return the UI URL.

**Query Parameters:**
- `script` (optional): Script filename to run (uses most recent if not specified)
- `host` (optional): Target host URL (default: http://localhost)
- `port` (optional): Locust web UI port (default: 8089)
- `users` (optional): Number of concurrent users (default: 1)
- `spawn_rate` (optional): User spawn rate (default: 1)
- `run_time` (optional): Run time duration (e.g., '30s', '5m', '1h')

**Response:**
```json
{
  "message": "Locust script started successfully",
  "process_id": "locust_script_20240101_120000.py_1704110400",
  "script": "locust_script_20240101_120000.py",
  "ui_url": "http://localhost:8089",
  "host": "http://localhost",
  "port": 8089,
  "users": 1,
  "spawn_rate": 1,
  "run_time": null,
  "status": "running",
  "started_at": "2024-01-01T12:00:00"
}
```

### GET /stop/{process_id}
Stop a running Locust process.

**Response:**
```json
{
  "message": "Locust process stopped successfully",
  "process_id": "locust_script_20240101_120000.py_1704110400",
  "status": "stopped",
  "stopped_at": "2024-01-01T12:05:00"
}
```

### GET /status
Get status of all running Locust processes.

**Response:**
```json
{
  "message": "Process status retrieved successfully",
  "total_processes": 1,
  "processes": [
    {
      "process_id": "locust_script_20240101_120000.py_1704110400",
      "script": "locust_script_20240101_120000.py",
      "host": "http://localhost",
      "port": 8089,
      "users": 1,
      "spawn_rate": 1,
      "status": "running",
      "started_at": "2024-01-01T12:00:00",
      "stopped_at": null
    }
  ]
}
```

### GET /
Get API information and available endpoints.

### GET /health
Health check endpoint.

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## File Structure

```
.
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── uploads/            # Directory for uploaded HAR files
├── scripts/            # Directory for generated Locust scripts
└── README.md           # This file
```
