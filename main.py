from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import shutil
import json
from pathlib import Path
import uvicorn
from typing import Dict, Any, Optional
from datetime import datetime
import subprocess
import threading
import time

app = FastAPI(title="HAR File Upload API", version="1.0.0")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create scripts directory if it doesn't exist
SCRIPTS_DIR = Path("scripts")
SCRIPTS_DIR.mkdir(exist_ok=True)

# Store running Locust processes
running_processes = {}

@app.post("/upload")
async def upload_har_file(file: UploadFile = File(...)):
    """
    Upload a HAR file and save it to the /uploads directory.
    
    Args:
        file: The HAR file to upload
        
    Returns:
        JSON response with upload status and file information
    """
    # Check if file has .har extension
    if not file.filename.lower().endswith('.har'):
        raise HTTPException(
            status_code=400, 
            detail="Only HAR files are allowed. Please upload a file with .har extension."
        )
    
    try:
        # Create file path
        file_path = UPLOAD_DIR / file.filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "filename": file.filename,
                "file_size": file_size,
                "file_path": str(file_path)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "HAR File Upload API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload HAR files",
            "POST /convert": "Convert HAR files to flow format",
            "POST /generate": "Generate Locust script from flow data",
            "GET /scripts": "List available Locust scripts",
            "GET /run": "Run Locust script and get UI URL",
            "GET /stop/{process_id}": "Stop running Locust process",
            "GET /status": "Get status of all processes",
            "GET /": "API information",
            "GET /health": "Health check"
        }
    }

@app.post("/convert")
async def convert_har_to_flow(file: UploadFile = File(...)):
    """
    Convert a HAR file to flow format.
    
    Args:
        file: The HAR file to convert
        
    Returns:
        JSON response with converted flow data
    """
    # Check if file has .har extension
    if not file.filename.lower().endswith('.har'):
        raise HTTPException(
            status_code=400, 
            detail="Only HAR files are allowed. Please upload a file with .har extension."
        )
    
    try:
        # Read the HAR file content
        content = await file.read()
        har_data = json.loads(content.decode('utf-8'))
        
        # Extract basic information from HAR
        log = har_data.get('log', {})
        entries = log.get('entries', [])
        
        # Convert HAR entries to flow format (mock implementation)
        flows = []
        for i, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            # Create a mock flow entry
            flow_entry = {
                "id": f"flow_{i+1}",
                "name": f"Request {i+1}",
                "method": request.get('method', 'GET'),
                "url": request.get('url', ''),
                "status_code": response.get('status', 200),
                "response_time": entry.get('time', 0),
                "request_headers": request.get('headers', []),
                "response_headers": response.get('headers', []),
                "request_body": request.get('postData', {}),
                "response_body": response.get('content', {}),
                "timestamp": entry.get('startedDateTime', ''),
                "flow_type": "http_request"
            }
            flows.append(flow_entry)
        
        # Create the flow structure
        flow_data = {
            "metadata": {
                "version": log.get('version', '1.2'),
                "creator": log.get('creator', {}),
                "browser": log.get('browser', {}),
                "pages": log.get('pages', []),
                "total_entries": len(entries),
                "converted_at": "2024-01-01T00:00:00Z"
            },
            "flows": flows,
            "summary": {
                "total_requests": len(flows),
                "unique_domains": len(set(flow['url'].split('/')[2] if '://' in flow['url'] else '' for flow in flows)),
                "methods": list(set(flow['method'] for flow in flows)),
                "status_codes": list(set(flow['status_code'] for flow in flows))
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "HAR file converted to flow successfully",
                "filename": file.filename,
                "flow_data": flow_data
            }
        )
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid HAR file format. Please ensure the file is a valid JSON HAR file."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error converting HAR file: {str(e)}"
        )

@app.post("/generate")
async def generate_locust_script(flow_data: Dict[str, Any]):
    """
    Generate a Locust script from flow data.
    
    Args:
        flow_data: The flow data containing requests to convert to Locust script
        
    Returns:
        JSON response with generated script information
    """
    try:
        # Extract flows from the input data
        flows = flow_data.get('flows', [])
        if not flows:
            raise HTTPException(
                status_code=400,
                detail="No flows found in the provided data. Please ensure 'flows' array is present."
            )
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_filename = f"locust_script_{timestamp}.py"
        script_path = SCRIPTS_DIR / script_filename
        
        # Generate Locust script content
        locust_script = generate_locust_script_content(flows, flow_data.get('metadata', {}))
        
        # Write script to file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(locust_script)
        
        # Get file size
        file_size = script_path.stat().st_size
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Locust script generated successfully",
                "filename": script_filename,
                "file_path": str(script_path),
                "file_size": file_size,
                "total_requests": len(flows),
                "script_preview": locust_script[:500] + "..." if len(locust_script) > 500 else locust_script
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Locust script: {str(e)}"
        )

def generate_locust_script_content(flows: list, metadata: dict) -> str:
    """Generate Locust script content from flows."""
    
    # Extract unique domains for base URL
    domains = set()
    for flow in flows:
        url = flow.get('url', '')
        if '://' in url:
            domain = url.split('/')[2]
            domains.add(domain)
    
    base_url = list(domains)[0] if domains else "http://localhost"
    
    # Generate script header
    script_content = f'''"""
Generated Locust script from HAR file
Generated at: {datetime.now().isoformat()}
Total requests: {len(flows)}
"""

from locust import HttpUser, task, between
import json
import random


class GeneratedUser(HttpUser):
    wait_time = between(1, 3)  # Wait between 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts."""
        self.client.verify = False  # Disable SSL verification for testing
        print("Starting user session...")
    
    def on_stop(self):
        """Called when a user stops."""
        print("Ending user session...")
    
'''
    
    # Generate task methods for each flow
    for i, flow in enumerate(flows):
        method = flow.get('method', 'GET').upper()
        url = flow.get('url', '')
        headers = flow.get('request_headers', [])
        body = flow.get('request_body', {})
        
        # Convert headers to dict
        headers_dict = {}
        for header in headers:
            if isinstance(header, dict) and 'name' in header and 'value' in header:
                headers_dict[header['name']] = header['value']
        
        # Extract path from URL
        if '://' in url:
            path = '/' + '/'.join(url.split('/')[3:])
        else:
            path = url
        
        # Generate task method
        task_name = f"task_{i+1}_{method.lower()}"
        script_content += f'''
    @task({max(1, 10 - i)})  # Higher priority for earlier requests
    def {task_name}(self):
        """{method} {path}"""
        url = "{path}"
        headers = {json.dumps(headers_dict, indent=8)}
        
'''
        
        # Add request body if present
        if body and method in ['POST', 'PUT', 'PATCH']:
            if isinstance(body, dict):
                script_content += f'''        data = {json.dumps(body, indent=8)}
        
        with self.client.{method.lower()}(url, headers=headers, json=data, catch_response=True) as response:
            if response.status_code == {flow.get('status_code', 200)}:
                response.success()
            else:
                response.failure(f"Expected status {flow.get('status_code', 200)}, got {{response.status_code}}")
'''
        else:
            script_content += f'''        with self.client.{method.lower()}(url, headers=headers, catch_response=True) as response:
            if response.status_code == {flow.get('status_code', 200)}:
                response.success()
            else:
                response.failure(f"Expected status {flow.get('status_code', 200)}, got {{response.status_code}}")
'''
    
    # Add footer
    script_content += f'''

# Configuration for running the script
# Command to run: locust -f {script_filename} --host={base_url}
# Web UI: http://localhost:8089
'''
    
    return script_content

@app.get("/scripts")
async def list_scripts():
    """List all available Locust scripts."""
    try:
        script_files = []
        for script_file in SCRIPTS_DIR.glob("*.py"):
            if script_file.is_file():
                stat = script_file.stat()
                script_files.append({
                    "filename": script_file.name,
                    "file_path": str(script_file),
                    "file_size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Scripts listed successfully",
                "total_scripts": len(script_files),
                "scripts": sorted(script_files, key=lambda x: x['modified_at'], reverse=True)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing scripts: {str(e)}"
        )

@app.get("/run")
async def run_locust_script(
    script: Optional[str] = Query(None, description="Script filename to run"),
    host: Optional[str] = Query("http://localhost", description="Target host URL"),
    port: int = Query(8089, description="Locust web UI port"),
    users: int = Query(1, description="Number of concurrent users"),
    spawn_rate: int = Query(1, description="User spawn rate"),
    run_time: Optional[str] = Query(None, description="Run time (e.g., '30s', '5m', '1h')")
):
    """
    Run a Locust script and return the UI URL.
    
    Args:
        script: Script filename to run (if not provided, uses the most recent script)
        host: Target host URL
        port: Locust web UI port
        users: Number of concurrent users
        spawn_rate: User spawn rate
        run_time: Run time duration
        
    Returns:
        JSON response with Locust UI URL and process information
    """
    try:
        # If no script specified, find the most recent one
        if not script:
            script_files = list(SCRIPTS_DIR.glob("*.py"))
            if not script_files:
                raise HTTPException(
                    status_code=404,
                    detail="No Locust scripts found. Please generate a script first using POST /generate."
                )
            script = max(script_files, key=lambda x: x.stat().st_mtime).name
        
        script_path = SCRIPTS_DIR / script
        if not script_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Script '{script}' not found in scripts directory."
            )
        
        # Check if Locust is installed
        try:
            subprocess.run(["locust", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise HTTPException(
                status_code=500,
                detail="Locust is not installed. Please install it with: pip install locust"
            )
        
        # Build Locust command
        cmd = [
            "locust",
            "-f", str(script_path),
            "--host", host,
            "--web-host", "0.0.0.0",
            "--web-port", str(port),
            "--users", str(users),
            "--spawn-rate", str(spawn_rate)
        ]
        
        if run_time:
            cmd.extend(["--run-time", run_time])
        
        # Start Locust process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Store process info
        process_id = f"{script}_{int(time.time())}"
        running_processes[process_id] = {
            "process": process,
            "script": script,
            "host": host,
            "port": port,
            "users": users,
            "spawn_rate": spawn_rate,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Wait a moment for Locust to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            ui_url = f"http://localhost:{port}"
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Locust script started successfully",
                    "process_id": process_id,
                    "script": script,
                    "ui_url": ui_url,
                    "host": host,
                    "port": port,
                    "users": users,
                    "spawn_rate": spawn_rate,
                    "run_time": run_time,
                    "status": "running",
                    "started_at": running_processes[process_id]["started_at"]
                }
            )
        else:
            # Process failed to start
            stdout, stderr = process.communicate()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start Locust: {stderr or stdout}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running Locust script: {str(e)}"
        )

@app.get("/stop/{process_id}")
async def stop_locust_process(process_id: str):
    """
    Stop a running Locust process.
    
    Args:
        process_id: The process ID returned by /run endpoint
        
    Returns:
        JSON response with stop status
    """
    try:
        if process_id not in running_processes:
            raise HTTPException(
                status_code=404,
                detail=f"Process '{process_id}' not found or already stopped."
            )
        
        process_info = running_processes[process_id]
        process = process_info["process"]
        
        if process.poll() is None:  # Process is still running
            process.terminate()
            process.wait(timeout=5)
            process_info["status"] = "stopped"
            process_info["stopped_at"] = datetime.now().isoformat()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Locust process stopped successfully",
                "process_id": process_id,
                "status": "stopped",
                "stopped_at": process_info.get("stopped_at")
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping Locust process: {str(e)}"
        )

@app.get("/status")
async def get_process_status():
    """Get status of all running Locust processes."""
    try:
        active_processes = []
        for process_id, process_info in running_processes.items():
            process = process_info["process"]
            if process.poll() is None:  # Still running
                process_info["status"] = "running"
            else:
                process_info["status"] = "stopped"
                if "stopped_at" not in process_info:
                    process_info["stopped_at"] = datetime.now().isoformat()
            
            active_processes.append({
                "process_id": process_id,
                "script": process_info["script"],
                "host": process_info["host"],
                "port": process_info["port"],
                "users": process_info["users"],
                "spawn_rate": process_info["spawn_rate"],
                "status": process_info["status"],
                "started_at": process_info["started_at"],
                "stopped_at": process_info.get("stopped_at")
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Process status retrieved successfully",
                "total_processes": len(active_processes),
                "processes": active_processes
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting process status: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
