from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Alternative frontend port
        "http://127.0.0.1:8080",
        "http://localhost:8001",  # Main API server
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create scripts directory if it doesn't exist
SCRIPTS_DIR = Path("scripts")
SCRIPTS_DIR.mkdir(exist_ok=True)

# Store running Locust processes
running_processes = {}
used_ports = set()  # Track used ports to prevent conflicts

def find_available_port(start_port=8089):
    """Find an available port starting from start_port"""
    import socket
    port = start_port
    while port in used_ports:
        port += 1
    
    # Test if port is actually available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        used_ports.add(port)
        return port
    except OSError:
        # Port is in use, try next one
        port += 1
        while port < start_port + 100:  # Don't go too far
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', port))
                sock.close()
                used_ports.add(port)
                return port
            except OSError:
                port += 1
        raise Exception(f"No available ports found starting from {start_port}")

def cleanup_process(process_id):
    """Clean up a process and free its port"""
    if process_id in running_processes:
        process_info = running_processes[process_id]
        process = process_info["process"]
        port = process_info.get("port")
        
        # Terminate the process
        try:
            process.terminate()
            process.wait(timeout=5)  # Wait up to 5 seconds
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate
        except:
            pass  # Process might already be dead
        
        # Free the port
        if port:
            used_ports.discard(port)
        
        # Remove from tracking
        del running_processes[process_id]

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
            "POST /convert-timestamp": "Convert HAR files to flow format using timestamp",
            "POST /generate": "Generate Locust script from flow data (supports filename and replace_existing parameters)",
            "GET /generate-examples": "Get usage examples for the generate endpoint",
            "GET /scripts": "List available Locust scripts",
            "GET /run": "Run Locust script and get UI URL (GET with query parameters)",
            "POST /run": "Run Locust script and get UI URL (POST with JSON body)",
            "GET /stop": "Stop Locust processes by script name (or all if no script specified)",
            "GET /stop-all": "Stop all running Locust processes",
            "GET /stop/{process_id}": "Stop specific Locust process by process ID",
            "GET /status": "Get status of all processes",
            "GET /": "API information",
            "GET /health": "Health check"
        }
    }

@app.post("/convert")
async def convert_har_to_flow(request: Request):
    """
    Convert a HAR file to flow format.
    Supports both file upload and JSON data with timestamp.
    
    Returns:
        JSON response with converted flow data
    """
    content_type = request.headers.get("content-type", "")
    
    if "multipart/form-data" in content_type:
        # File upload mode
        form = await request.form()
        file = form.get("file")
        
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file provided"
            )
        
        if not file.filename.lower().endswith('.har'):
            raise HTTPException(
                status_code=400, 
                detail="Only HAR files are allowed. Please upload a file with .har extension."
            )
        
        try:
            # Read the HAR file content
            content = await file.read()
            har_data = json.loads(content.decode('utf-8'))
            filename = file.filename
            timestamp = datetime.now().isoformat()
            
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid HAR file format. Please ensure the file is a valid JSON HAR file."
            )
    
    elif "application/json" in content_type:
        # JSON data mode
        try:
            data = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON data"
            )
        
        timestamp = data.get('timestamp')
        filename = data.get('filename', 'recording.har')
        
        if not timestamp:
            raise HTTPException(
                status_code=400,
                detail="Timestamp is required in the request body"
            )
        
        # Check if the HAR file exists (with .har extension if not provided)
        if not filename.lower().endswith('.har'):
            filename = f"{filename}.har"
        
        file_path = UPLOAD_DIR / filename
        
        # If file doesn't exist, try to find a similar file with different naming convention
        if not file_path.exists():
            # Try alternative filename formats
            alternative_filenames = [
                filename.replace('_', '.'),  # Convert underscores to dots
                filename.replace('.', '_'),  # Convert dots to underscores
                filename.replace('_', '-'),  # Convert underscores to dashes
                filename.replace('.', '-'),  # Convert dots to dashes
            ]
            
            found_file = None
            for alt_filename in alternative_filenames:
                alt_path = UPLOAD_DIR / alt_filename
                if alt_path.exists():
                    found_file = alt_filename
                    file_path = alt_path
                    break
            
            if not found_file:
                # List available files for better error message
                available_files = [f.name for f in UPLOAD_DIR.glob("*.har")]
                raise HTTPException(
                    status_code=404,
                    detail=f"HAR file '{filename}' not found in uploads directory. Available files: {available_files}"
                )
        
        try:
            # Read the HAR file content
            with open(file_path, 'r', encoding='utf-8') as f:
                har_data = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid HAR file format. Please ensure the file is a valid JSON HAR file."
            )
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Content-Type must be either multipart/form-data or application/json"
        )
    
    try:
        # Extract basic information from HAR
        log = har_data.get('log', {})
        entries = log.get('entries', [])
        print(f"DEBUG: Found {len(entries)} entries in HAR file")
        
        # Convert HAR entries to flow format
        flows = []
        for i, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            if i < 3:  # Debug first 3 entries
                print(f"DEBUG: Entry {i}: method={request.get('method')}, url={request.get('url', '')[:50]}...")
            
            # Create a flow entry with better data preservation
            flow_entry = {
                "id": f"flow_{i+1}",
                "name": f"Request {i+1}",
                "method": request.get('method', 'GET'),
                "url": request.get('url', ''),
                "status_code": response.get('status', 200),
                "response_time": entry.get('time', 0),
                "request_headers": request.get('headers', []),
                "response_headers": response.get('headers', []),
                "request_body": request.get('postData', {}),  # This contains the actual JSON data
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
                "converted_at": timestamp,
                "requested_at": timestamp
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
                "filename": filename,
                "timestamp": timestamp,
                "flow_data": flow_data
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error converting HAR file: {str(e)}"
        )

@app.post("/convert-timestamp")
async def convert_with_timestamp(data: Dict[str, Any]):
    """
    Convert HAR file to flow format using a timestamp parameter.
    
    Args:
        data: JSON data containing timestamp and optional filename
        
    Returns:
        JSON response with converted flow data
    """
    try:
        timestamp = data.get('timestamp')
        filename = data.get('filename', 'recording.har')
        
        if not timestamp:
            raise HTTPException(
                status_code=400,
                detail="Timestamp is required in the request body"
            )
        
        # Check if the HAR file exists (with .har extension if not provided)
        if not filename.lower().endswith('.har'):
            filename = f"{filename}.har"
        
        file_path = UPLOAD_DIR / filename
        
        # If file doesn't exist, try to find a similar file with different naming convention
        if not file_path.exists():
            # Try alternative filename formats
            alternative_filenames = [
                filename.replace('_', '.'),  # Convert underscores to dots
                filename.replace('.', '_'),  # Convert dots to underscores
                filename.replace('_', '-'),  # Convert underscores to dashes
                filename.replace('.', '-'),  # Convert dots to dashes
            ]
            
            found_file = None
            for alt_filename in alternative_filenames:
                alt_path = UPLOAD_DIR / alt_filename
                if alt_path.exists():
                    found_file = alt_filename
                    file_path = alt_path
                    break
            
            if not found_file:
                # List available files for better error message
                available_files = [f.name for f in UPLOAD_DIR.glob("*.har")]
                raise HTTPException(
                    status_code=404,
                    detail=f"HAR file '{filename}' not found in uploads directory. Available files: {available_files}"
                )
        
        # Read the HAR file content
        with open(file_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        # Extract basic information from HAR
        log = har_data.get('log', {})
        entries = log.get('entries', [])
        
        # Convert HAR entries to flow format
        flows = []
        for i, entry in enumerate(entries):
            request = entry.get('request', {})
            response = entry.get('response', {})
            
            # Create a flow entry with better data preservation
            flow_entry = {
                "id": f"flow_{i+1}",
                "name": f"Request {i+1}",
                "method": request.get('method', 'GET'),
                "url": request.get('url', ''),
                "status_code": response.get('status', 200),
                "response_time": entry.get('time', 0),
                "request_headers": request.get('headers', []),
                "response_headers": response.get('headers', []),
                "request_body": request.get('postData', {}),  # This contains the actual JSON data
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
                "converted_at": timestamp,
                "requested_at": timestamp
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
                "filename": filename,
                "timestamp": timestamp,
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
        - flows: Array of flow data (required)
        - filename: Custom filename without extension (optional, defaults to auto-generated)
        - replace_existing: Whether to replace existing files (optional, defaults to false)
        - target_host: Target host URL for the script (optional, will be extracted from flows if not provided)
        - metadata: Additional metadata (optional)
        
    Returns:
        JSON response with generated script information
    """
    try:
        # Extract flows from the input data
        flows = flow_data.get('flows', [])
        custom_filename = flow_data.get('filename')
        replace_existing = flow_data.get('replace_existing', False)
        target_host = flow_data.get('target_host')
        
        print(f"DEBUG: Processing {len(flows)} flows")
        print(f"DEBUG: Custom filename: {custom_filename}")
        print(f"DEBUG: Replace existing: {replace_existing}")
        print(f"DEBUG: Flow data keys: {list(flow_data.keys())}")
        print(f"DEBUG: First few flows: {flows[:3] if isinstance(flows, list) and flows else 'No flows found'}")
        
        if not flows:
            raise HTTPException(
                status_code=400,
                detail="No flows found in the provided data. Please ensure 'flows' array is present."
            )
        
        # Determine filename
        if custom_filename:
            # Use provided filename + .py extension
            script_filename = f"{custom_filename}.py"
        else:
            # Generate timestamp for unique filename (fallback)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_filename = f"locust_script_{timestamp}.py"
        
        script_path = SCRIPTS_DIR / script_filename
        
        # Check if file exists and handle replacement
        if script_path.exists():
            if replace_existing:
                print(f"INFO: Replacing existing file: {script_filename}")
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"File '{script_filename}' already exists. Set 'replace_existing': true to overwrite."
                )
        else:
            print(f"INFO: Creating new file: {script_filename}")
        
        # Generate Locust script content
        locust_script = generate_locust_script_content(flows, flow_data.get('metadata', {}), script_filename, target_host)
        
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
                "replaced_existing": script_path.exists() and replace_existing,
                "script_preview": locust_script[:500] + "..." if len(locust_script) > 500 else locust_script
            }
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in generate_locust_script: {error_details}")  # Debug print
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Locust script: {str(e)}"
        )

def generate_locust_script_content(flows: list, metadata: dict, script_filename: str, target_host: str = None) -> str:
    """Generate Locust script content from flows using the improved generator."""
    
    # Extract target host from flows if not provided
    if not target_host and flows:
        # Try to extract host from the first flow's URL
        first_flow = flows[0] if flows else {}
        first_url = first_flow.get('url', '')
        if '://' in first_url:
            # Extract host from URL (e.g., "https://example.com/path" -> "https://example.com")
            target_host = first_url.split('://')[0] + '://' + first_url.split('://')[1].split('/')[0]
            print(f"DEBUG: Extracted target host from flows: {target_host}")
    
    # Convert flows to the format expected by the improved generator
    converted_flows = []
    for i, flow in enumerate(flows):
        # Check if flow is a dictionary, if not skip it
        if not isinstance(flow, dict):
            print(f"WARNING: Skipping non-dict flow: {type(flow)} - {flow}")
            continue
        
        # Convert headers from list format to dict format
        headers_dict = {}
        for header in flow.get('request_headers', []):
            if isinstance(header, dict) and 'name' in header and 'value' in header:
                headers_dict[header['name']] = header['value']
        
        # Convert request body - handle both dict and string formats
        body_data = flow.get('request_body', {})
        if isinstance(body_data, dict) and body_data:
            # If it's a dict, convert to JSON string
            body_str = json.dumps(body_data)
        elif isinstance(body_data, str) and body_data:
            # If it's already a string, use it as-is
            body_str = body_data
        else:
            body_str = None
        
        # Create converted flow
        converted_flow = {
            "method": flow.get('method', 'GET'),
            "url": flow.get('url', ''),
            "headers": headers_dict,
            "body": body_str,
            "set_context": [],  # No context setting for now
            "use_context": []   # No context usage for now
        }
        converted_flows.append(converted_flow)
    
    # Use the improved template from locust_generator.py
    from locust_generator import TEMPLATE_HEADER, generate_step_code, is_authentication_flow, generate_authentication_code, requires_permissions, get_permission_level
    
    # Generate script using the improved template
    script_content = f'''
"""
Generated Locust script from HAR file
Generated at: {datetime.now().isoformat()}
Total requests: {len(converted_flows)}
"""

{TEMPLATE_HEADER}
'''
    
    # Identify authentication flows
    auth_flows = []
    for i, flow in enumerate(converted_flows):
        if is_authentication_flow(flow):
            auth_flows.append((i+1, flow))
    
    # Generate authentication code if found
    if auth_flows:
        print(f"DEBUG: Found {len(auth_flows)} authentication flow(s)")
        auth_code = generate_authentication_code(auth_flows, target_host)
        script_content += auth_code
    
    # Generate task methods for each flow using the improved template
    print(f"DEBUG: Generating tasks for {len(converted_flows)} converted flows")
    for i, flow in enumerate(converted_flows):
        if not is_authentication_flow(flow):
            print(f"DEBUG: Processing flow {i+1}: {flow.get('method', 'UNKNOWN')} {flow.get('url', 'UNKNOWN')[:50]}...")
            
            # Use the generate_step_code function from locust_generator.py
            task_method = generate_step_code(i+1, flow, target_host)
            script_content += task_method
    
    # Add footer with target host information
    host_info = f"# Target host: {target_host}" if target_host else "# Target host: Will be set via --host parameter"
    script_content += f'''

# Configuration for running the script
{host_info}
# Command to run: locust -f {script_filename} --host=<target_host>
# Web UI: http://localhost:8089
# Prometheus metrics: http://localhost:8001/metrics
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

async def run_locust_script_internal(script: Optional[str], host: str, port: int, users: int, spawn_rate: int, run_time: Optional[str]):
    """
    Internal function to run a Locust script.
    
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
            subprocess.run(["python", "-m", "locust", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise HTTPException(
                status_code=500,
                detail="Locust is not installed. Please install it with: pip install locust"
            )
        
        # Find an available port
        actual_port = find_available_port(port)
        
        # Build Locust command
        cmd = [
            "python", "-m", "locust",
            "-f", str(script_path),
            "--host", host,
            "--web-host", "0.0.0.0",
            "--web-port", str(actual_port),
            "--users", str(users),
            "--spawn-rate", str(spawn_rate)
        ]
        
        # Add headless mode only if run_time is specified (for automatic completion)
        if run_time:
            cmd.append("--headless")  # Run in headless mode when run_time is specified
        
        # If no run_time specified, add a default 30 second run time to prevent hanging
        if run_time:
            cmd.extend(["--run-time", run_time])
        else:
            cmd.extend(["--run-time", "30s"])
        
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
            "port": actual_port,  # Use the actual port that was assigned
            "users": users,
            "spawn_rate": spawn_rate,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        
        # Wait a moment for Locust to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            ui_url = f"http://localhost:{actual_port}"
            mode = "headless mode" if run_time else "web UI mode"
            note = "Test is running in headless mode. Check the process status endpoint for results." if run_time else f"Test is running with web UI. Access the interface at {ui_url}"
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Locust script started successfully in {mode}",
                    "process_id": process_id,
                    "script": script,
                    "ui_url": ui_url,
                    "host": host,
                    "port": port,
                    "users": users,
                    "spawn_rate": spawn_rate,
                    "run_time": run_time or "unlimited",
                    "status": "running",
                    "started_at": running_processes[process_id]["started_at"],
                    "note": note
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

@app.post("/run")
async def run_locust_script_post(request_data: Dict[str, Any]):
    """
    Run a Locust script via POST request.
    
    Args:
        request_data: JSON data containing script parameters
        
    Returns:
        JSON response with Locust UI URL and process information
    """
    try:
        script = request_data.get('script')
        host = request_data.get('host', 'http://localhost')
        port = request_data.get('port', 8089)
        users = request_data.get('users', 1)
        spawn_rate = request_data.get('spawn_rate', 1)
        run_time = request_data.get('run_time')
        
        return await run_locust_script_internal(script, host, port, users, spawn_rate, run_time)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running Locust script: {str(e)}"
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
        return await run_locust_script_internal(script, host, port, users, spawn_rate, run_time)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running Locust script: {str(e)}"
        )

@app.get("/stop-all")
async def stop_all_locust_processes():
    """
    Stop all running Locust processes.
    
    Returns:
        JSON response with stop status for all processes
    """
    try:
        stopped_processes = []
        failed_processes = []
        
        for process_id in list(running_processes.keys()):
            try:
                cleanup_process(process_id)
                stopped_processes.append(process_id)
            except Exception as e:
                failed_processes.append({
                    "process_id": process_id,
                    "error": str(e)
                })
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Stopped {len(stopped_processes)} processes",
                "stopped_processes": stopped_processes,
                "failed_processes": failed_processes,
                "total_stopped": len(stopped_processes),
                "total_failed": len(failed_processes)
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping processes: {str(e)}"
        )

@app.get("/stop")
async def stop_locust_by_script(script: Optional[str] = Query(None, description="Script name to stop")):
    """
    Stop Locust processes by script name or all if no script specified.
    
    Args:
        script: Script name to stop (if not provided, stops all)
        
    Returns:
        JSON response with stop status
    """
    try:
        if script:
            # Stop processes for specific script
            stopped_processes = []
            for process_id, process_info in list(running_processes.items()):
                if process_info["script"] == script:
                    process = process_info["process"]
                    if process.poll() is None:  # Process is still running
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                            process_info["status"] = "stopped"
                            process_info["stopped_at"] = datetime.now().isoformat()
                            stopped_processes.append(process_id)
                        except Exception as e:
                            pass  # Continue with other processes
            
            if not stopped_processes:
                raise HTTPException(
                    status_code=404,
                    detail=f"No running processes found for script '{script}'"
                )
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Stopped {len(stopped_processes)} processes for script '{script}'",
                    "script": script,
                    "stopped_processes": stopped_processes,
                    "total_stopped": len(stopped_processes)
                }
            )
        else:
            # Stop all processes
            return await stop_all_locust_processes()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping processes: {str(e)}"
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
        
        # Use the cleanup function for proper process termination
        cleanup_process(process_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Locust process stopped successfully",
                "process_id": process_id,
                "status": "stopped",
                "stopped_at": datetime.now().isoformat()
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
            poll_result = process.poll()
            print(f"DEBUG: Process {process_id} poll result: {poll_result}")
            if poll_result is None:  # Still running
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

def cleanup_dead_processes():
    """Clean up processes that have died but are still in our tracking"""
    dead_processes = []
    for process_id, process_info in list(running_processes.items()):
        process = process_info["process"]
        if process.poll() is not None:  # Process has died
            dead_processes.append(process_id)
            # Free the port
            port = process_info.get("port")
            if port:
                used_ports.discard(port)
    
    # Remove dead processes from tracking
    for process_id in dead_processes:
        del running_processes[process_id]
    
    return len(dead_processes)

@app.get("/generate-examples")
async def generate_examples():
    """Get examples of how to use the generate endpoint with new parameters."""
    return {
        "message": "Generate endpoint usage examples",
        "examples": {
            "basic_usage": {
                "description": "Basic usage with auto-generated filename",
                "request": {
                    "flows": [
                        {
                            "url": "http://localhost/api/test",
                            "method": "GET",
                            "headers": {"Accept": "application/json"}
                        }
                    ]
                }
            },
            "custom_filename": {
                "description": "Using custom filename without extension",
                "request": {
                    "flows": [
                        {
                            "url": "http://localhost/api/test",
                            "method": "GET",
                            "headers": {"Accept": "application/json"}
                        }
                    ],
                    "filename": "my_custom_test"
                },
                "result": "Creates file: my_custom_test.py"
            },
            "replace_existing": {
                "description": "Replace existing file if it exists",
                "request": {
                    "flows": [
                        {
                            "url": "http://localhost/api/test",
                            "method": "GET",
                            "headers": {"Accept": "application/json"}
                        }
                    ],
                    "filename": "existing_script",
                    "replace_existing": True
                },
                "result": "Overwrites existing_script.py if it exists"
            },
            "prevent_overwrite": {
                "description": "Prevent overwriting existing files (default behavior)",
                "request": {
                    "flows": [
                        {
                            "url": "http://localhost/api/test",
                            "method": "GET",
                            "headers": {"Accept": "application/json"}
                        }
                    ],
                    "filename": "existing_script",
                    "replace_existing": False
                },
                "result": "Returns 409 error if existing_script.py already exists"
            },
            "with_metadata": {
                "description": "Include metadata in the request",
                "request": {
                    "flows": [
                        {
                            "url": "http://localhost/api/test",
                            "method": "GET",
                            "headers": {"Accept": "application/json"}
                        }
                    ],
                    "filename": "test_with_metadata",
                    "replace_existing": True,
                    "metadata": {
                        "description": "Test script for API validation",
                        "version": "1.0.0"
                    }
                }
            }
        },
        "parameters": {
            "flows": "Array of flow data (required)",
            "filename": "Custom filename without .py extension (optional)",
            "replace_existing": "Boolean to allow overwriting existing files (optional, default: false)",
            "metadata": "Additional metadata object (optional)"
        },
        "response_codes": {
            "200": "Script generated successfully",
            "400": "No flows provided or invalid data",
            "409": "File already exists and replace_existing is false"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with process cleanup."""
    cleaned = cleanup_dead_processes()
    return {
        "status": "healthy",
        "active_processes": len(running_processes),
        "cleaned_dead_processes": cleaned
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
