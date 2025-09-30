import yaml
import json

TEMPLATE_HEADER = '''from locust import HttpUser, task, between, events
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import urllib3
import json

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Prometheus metrics - Cleaner structure
REQUEST_COUNT = Counter('locust_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('locust_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'], buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
ACTIVE_USERS = Gauge('locust_active_users', 'Number of active users')
REQUEST_RATE = Gauge('locust_request_rate', 'Requests per second')
ERROR_RATE = Gauge('locust_error_rate', 'Error rate percentage')

# Start Prometheus metrics server on port 8002
start_http_server(8002)

# Custom metrics tracking
@events.request.add_listener
def track_request_metrics(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track custom metrics for Prometheus with cleaner endpoint names"""
    status = 'success' if exception is None else 'failure'
    method = request_type.upper() if request_type else 'UNKNOWN'

    # Clean up endpoint names - remove query parameters and cache IDs for cleaner metrics
    endpoint = name or 'unknown'
    if '?' in endpoint:
        endpoint = endpoint.split('?')[0]
    if '.dot.html' in endpoint:
        endpoint = endpoint.replace('.dot.html', '')
    if 'cacheId=' in endpoint:
        endpoint = endpoint.split('cacheId=')[0].rstrip('?&')

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(response_time / 1000.0)

    # Update active users count
    if hasattr(context, 'environment') and hasattr(context.environment, 'runner'):
        ACTIVE_USERS.set(context.environment.runner.user_count)

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize metrics on test start"""
    ACTIVE_USERS.set(0)

class RecordedUser(HttpUser):
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable SSL verification for self-signed certificates
        self.client.verify = False
        # Initialize session context
        self._context = {}
        self._authenticated = False

    def on_start(self):
        """Authentication runs before any tasks - proper flow"""
        # Test initial connection
        self._test_connection()
        
        # Perform authentication if needed
        self._authenticate()
    
    def _test_connection(self):
        """Test initial connection to provide early feedback"""
        try:
            with self.client.get("/", catch_response=True) as response:
                if response.status_code == 0:
                    print("WARNING: Cannot connect to the target server. Please ensure the application is running and accessible.")
                elif response.status_code >= 400:
                    print(f"WARNING  WARNING: Server returned status {response.status_code}. Check if the application is properly configured.")
                else:
                    print("SUCCESS Successfully connected to the target server.")
                response.success()
        except Exception as e:
            print(f"WARNING  WARNING: Connection test failed - {str(e)}")
    
    def _authenticate(self):
        """Handle authentication flow - runs once per user"""
        # This will be populated with actual authentication logic
        # based on the flows that contain authentication requests
        pass
    
    def _extract_auth_token(self, response):
        """Extract authentication token from response"""
        try:
            if response.status_code == 200:
                data = response.json()
                # Common token field names
                token_fields = ['token', 'access_token', 'auth_token', 'jwt', 'bearer_token', 'session_token']
                for field in token_fields:
                    if field in data:
                        self._context[f'auth_{field}'] = data[field]
                        print(f"SUCCESS Extracted {field} from authentication response")
                        return data[field]
                
                # Check for nested token structures
                if 'data' in data and isinstance(data['data'], dict):
                    for field in token_fields:
                        if field in data['data']:
                            self._context[f'auth_{field}'] = data['data'][field]
                            print(f"SUCCESS Extracted {field} from nested data")
                            return data['data'][field]
        except Exception as e:
            print(f"WARNING  Could not extract token: {str(e)}")
        return None
    
    def _add_auth_headers(self, headers):
        """Add authentication headers if token is available"""
        auth_headers = {}
        for key, value in headers.items():
            auth_headers[key] = value
        
        # Add Authorization header if token is available
        for token_key in ['auth_token', 'auth_access_token', 'auth_jwt', 'auth_bearer_token']:
            if token_key in self._context:
                token = self._context[token_key]
                if token_key == 'auth_jwt':
                    auth_headers['Authorization'] = f'Bearer {token}'
                else:
                    auth_headers['Authorization'] = f'Bearer {token}'
                break
        
        return auth_headers
    
    def _extract_context_from_response(self, response, flow_name):
        """Extract context values from response for use in subsequent requests"""
        try:
            if response.status_code == 200:
                data = response.json()
                
                # Extract common context values
                context_extractions = {
                    'participationId': ['participationId', 'id', 'participation_id'],
                    'applicationId': ['applicationId', 'appId', 'application_id'],
                    'eventId': ['eventId', 'event_id'],
                    'userId': ['userId', 'user_id', 'id'],
                    'sessionId': ['sessionId', 'session_id'],
                    'companyId': ['companyId', 'company_id'],
                    'language': ['language', 'lang'],
                    'application': ['application', 'app']
                }
                
                for context_key, possible_keys in context_extractions.items():
                    for key in possible_keys:
                        if key in data:
                            self._context[context_key] = data[key]
                            print(f"SUCCESS Extracted {context_key}={data[key]} from {flow_name}")
                            break
                        # Check nested structures
                        elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
                            if key in data['data']:
                                self._context[context_key] = data['data'][key]
                                print(f"SUCCESS Extracted {context_key}={data['data'][key]} from nested data in {flow_name}")
                                break
                
                # Extract arrays of IDs
                if 'participations' in data and isinstance(data['participations'], list) and len(data['participations']) > 0:
                    first_participation = data['participations'][0]
                    if 'id' in first_participation:
                        self._context['participationId'] = first_participation['id']
                        print(f"SUCCESS Extracted participationId={first_participation['id']} from participations array in {flow_name}")
                
        except Exception as e:
            print(f"WARNING  Could not extract context from {flow_name}: {str(e)}")
    
    def _substitute_context_values(self, text):
        """Substitute context values in text/URLs"""
        if not text or not isinstance(text, str):
            return text
            
        # Replace context variables in the text
        for key, value in self._context.items():
            placeholder = f"{{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
                print(f"🔄 Substituted {placeholder} with {value}")
        
        return text
    
    def context(self):
        """Return shared context for correlation"""
        return self._context
'''

STEP_TEMPLATE = """
    @task
    def step_{idx}(self):
        \"\"\"{name} - {method} request (Permission: {permission_level})\"\"\"
        # Check if user has required permissions
        if "{requires_permissions}" == "true" and not self._authenticated:
            print(f"WARNING  Skipping {name} - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values({url})
        substituted_body = {body}
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({headers})
        
        with self.client.{method}(
            substituted_url,
            headers=auth_headers,
            {data_param}=substituted_body,
            catch_response=True,
            name="{name}"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "{is_auth_endpoint}":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "{name}")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for {permission_level} level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {{resp.status_code}}")
            else:
                resp.failure(f"Request failed: {{resp.status_code}}")
{set_context_code}
"""

BROWSER_TEMPLATE = """
    @task
    def browser_step_{idx}(self):
        from selenium import webdriver
        import time
        driver = webdriver.Chrome()
        driver.get("{url}")
        time.sleep({wait_time})
        driver.quit()
"""

def generate_step_code(idx, flow, target_host=None):
    # Extract relative path from full URL
    full_url = flow["url"]
    if "://" in full_url:
        # Extract path from full URL (e.g., "http://localhost/path" -> "/path")
        url_parts = full_url.split("://", 1)[1].split("/", 1)
        if len(url_parts) > 1:
            relative_url = "/" + url_parts[1]
        else:
            relative_url = "/"
    else:
        relative_url = full_url
    
    # Keep URL as string for template substitution
    # The template will handle the context substitution
    
    # Extract method early for use in header processing
    method = flow["method"].lower()
    
    # Process headers for BTS Pulse API - proper headers
    headers = flow.get("headers", {})
    
    # BTS Pulse API specific headers - filter out HTTP/2 pseudo-headers
    filtered_headers = {}
    pseudo_headers = [':authority', ':method', ':path', ':scheme', ':status']
    
    for key, value in headers.items():
        # Skip HTTP/2 pseudo-headers
        if key.lower() in pseudo_headers:
            continue
            
        if isinstance(value, str):
            # Handle host-specific headers
            if "localhost" in value.lower() and target_host:
                if key.lower() in ['host', 'origin', 'referer']:
                    # Replace localhost with target host for specific headers
                    target_domain = target_host.replace("https://", "").replace("http://", "")
                    filtered_headers[key] = value.replace("localhost", target_domain)
                elif key.lower() in ['content-type', 'accept', 'user-agent', 'x-requested-with', 'authorization']:
                    # Keep important API headers as-is
                    filtered_headers[key] = value
                else:
                    # For other headers with localhost, try to replace or skip
                    if "localhost" in value:
                        target_domain = target_host.replace("https://", "").replace("http://", "")
                        filtered_headers[key] = value.replace("localhost", target_domain)
                    else:
                        filtered_headers[key] = value
            else:
                # Keep all other headers as-is
                filtered_headers[key] = value
        else:
            filtered_headers[key] = value
    
    # Ensure proper BTS Pulse API headers
    if not any(key.lower() == 'content-type' for key in filtered_headers.keys()):
        if method in ['post', 'put']:
            filtered_headers['Content-Type'] = 'application/json'
    
    if not any(key.lower() == 'accept' for key in filtered_headers.keys()):
        filtered_headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
    
    if not any(key.lower() == 'x-requested-with' for key in filtered_headers.keys()):
        filtered_headers['X-Requested-With'] = 'XMLHttpRequest'
    
    headers_code = str(filtered_headers)
    
    # Enhanced JSON handling for all APIs - check content-type to determine parameter
    data_param = "data"  # Default to 'data' parameter
    body_code = "None"
    
    # Check content-type header to determine the correct parameter
    content_type = None
    for key, value in filtered_headers.items():
        if key.lower() == 'content-type':
            content_type = value.lower()
            break
    
    if flow.get("body"):
        try:
            # Try to parse as JSON to validate and re-serialize properly
            body_data = json.loads(flow.get("body"))
            
            # For PUT/POST requests with JSON data, check content-type to determine parameter
            if method in ['put', 'post'] and isinstance(body_data, dict):
                # Use json parameter only if content-type is application/json
                if content_type and 'application/json' in content_type:
                    data_param = "json"
                    # Use Python dictionary directly for json parameter
                    body_code = repr(body_data)
                else:
                    # Use data parameter for form-encoded or other content types
                    data_param = "data"
                    # For form-encoded data, convert dict to form string
                    if content_type and 'application/x-www-form-urlencoded' in content_type:
                        form_data = '&'.join([f'{k}={v}' for k, v in body_data.items()])
                        body_code = repr(form_data)
                    else:
                        # For other content types, use the dict as-is
                        body_code = repr(body_data)
            else:
                # For other cases, use 'data' parameter with JSON string
                body_code = f'json.dumps({repr(body_data)})'
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, use as raw data with context substitution
            body_code = f'self._substitute_context_values({repr(flow.get("body"))})'
    else:
        body_code = "None"
    
    cookies_code = "{" + ", ".join([f'"{k.replace("cookie_","")}": self._context.get("{k}", "")' for k in flow.get("use_context", []) if k.startswith("cookie_")]) + "}" if any(k.startswith("cookie_") for k in flow.get("use_context", [])) else "None"

    set_context_code = ""
    for k in flow.get("set_context", []):
        if k.startswith("cookie_"):
            cname = k.replace("cookie_", "")
            set_context_code += f'                        if "{cname}" in resp.cookies:\n'
            set_context_code += f'                            self._context["{k}"] = resp.cookies["{cname}"]\n'
        else:
            set_context_code += f'                        if "{k}" in data:\n'
            set_context_code += f'                            self._context["{k}"] = data.get("{k}")\n'

    # Create cleaner task name
    task_name = relative_url.split("/")[-1] or f"Step{idx}"
    if '?' in task_name:
        task_name = task_name.split('?')[0]
    if '.dot.html' in task_name:
        task_name = task_name.replace('.dot.html', '')
    if 'cacheId=' in task_name:
        task_name = task_name.split('cacheId=')[0].rstrip('?&')
    
    # Check if this is an authentication endpoint
    is_auth_endpoint = is_authentication_flow(flow)
    
    # Check permission requirements
    needs_permissions = requires_permissions(flow)
    permission_level = get_permission_level(flow)
    
    return STEP_TEMPLATE.format(
        idx=idx,
        method=flow["method"].lower(),
        url=repr(relative_url),
        headers=headers_code,
        data_param=data_param,
        body=body_code,
        cookies=cookies_code,
        name=task_name,
        is_auth_endpoint=str(is_auth_endpoint).lower(),
        requires_permissions=str(needs_permissions).lower(),
        permission_level=permission_level,
        set_context_code=set_context_code
    )

def is_authentication_flow(flow):
    """Detect if a flow is an authentication request"""
    url = flow.get("url", "").lower()
    method = flow.get("method", "").lower()
    
    # Check for common authentication endpoints
    auth_keywords = [
        "authenticate", "login", "auth", "signin", "token", 
        "session", "credential", "password", "oauth"
    ]
    
    return (
        method in ["post", "put"] and 
        any(keyword in url for keyword in auth_keywords)
    )

def requires_permissions(flow):
    """Detect if a flow requires specific permissions"""
    url = flow.get("url", "").lower()
    
    # Common permission-based endpoints
    permission_keywords = [
        "admin", "useradmin", "management", "eventadmin", 
        "company", "privileges", "roles", "permissions"
    ]
    
    return any(keyword in url for keyword in permission_keywords)

def get_permission_level(flow):
    """Determine the permission level required for this endpoint"""
    url = flow.get("url", "").lower()
    
    if any(keyword in url for keyword in ["admin", "useradmin", "management"]):
        return "admin"
    elif any(keyword in url for keyword in ["eventadmin", "company"]):
        return "manager"
    elif any(keyword in url for keyword in ["privileges", "roles"]):
        return "user"
    else:
        return "public"

def generate_authentication_code(auth_flows, target_host):
    """Generate authentication code for on_start method"""
    if not auth_flows:
        return ""
    
    # Use the first authentication flow
    idx, flow = auth_flows[0]
    
    # Extract relative path from full URL
    full_url = flow["url"]
    if "://" in full_url:
        url_parts = full_url.split("://", 1)[1].split("/", 1)
        if len(url_parts) > 1:
            relative_url = "/" + url_parts[1]
        else:
            relative_url = "/"
    else:
        relative_url = full_url
    
    # Keep URL as string for template substitution
    # The template will handle the context substitution
    
    # Process headers for authentication - filter out HTTP/2 pseudo-headers
    headers = flow.get("headers", {})
    filtered_headers = {}
    pseudo_headers = [':authority', ':method', ':path', ':scheme', ':status']
    
    for key, value in headers.items():
        # Skip HTTP/2 pseudo-headers
        if key.lower() in pseudo_headers:
            continue
            
        if isinstance(value, str):
            if "localhost" in value.lower() and target_host:
                if key.lower() in ['host', 'origin', 'referer']:
                    target_domain = target_host.replace("https://", "").replace("http://", "")
                    filtered_headers[key] = value.replace("localhost", target_domain)
                else:
                    filtered_headers[key] = value
            else:
                filtered_headers[key] = value
        else:
            filtered_headers[key] = value
    
    # Ensure proper headers for authentication
    if not any(key.lower() == 'content-type' for key in filtered_headers.keys()):
        filtered_headers['Content-Type'] = 'application/json'
    
    # Process authentication body - check content-type to determine parameter
    method = flow["method"].lower()
    data_param = "data"
    body_code = "None"
    
    # Check content-type header to determine the correct parameter
    content_type = None
    for key, value in filtered_headers.items():
        if key.lower() == 'content-type':
            content_type = value.lower()
            break
    
    if flow.get("body"):
        try:
            body_data = json.loads(flow.get("body"))
            if method in ['put', 'post'] and isinstance(body_data, dict):
                # Use json parameter only if content-type is application/json
                if content_type and 'application/json' in content_type:
                    data_param = "json"
                    body_code = repr(body_data)
                else:
                    # Use data parameter for form-encoded or other content types
                    data_param = "data"
                    # For form-encoded data, convert dict to form string
                    if content_type and 'application/x-www-form-urlencoded' in content_type:
                        form_data = '&'.join([f'{k}={v}' for k, v in body_data.items()])
                        body_code = repr(form_data)
                    else:
                        # For other content types, use the dict as-is
                        body_code = repr(body_data)
            else:
                body_code = f'json.dumps({repr(body_data)})'
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, use as raw data
            body_code = repr(flow.get("body"))
    
    auth_code = f'''
    def _authenticate(self):
        """Handle authentication flow - runs once per user"""
        try:
            with self.client.{method}(
                {repr(relative_url)},
                headers={str(filtered_headers)},
                {data_param}={body_code},
                catch_response=True,
                name="Authentication"
            ) as resp:
                if resp.status_code == 200:
                    resp.success()
                    self._authenticated = True
                    print("SUCCESS Authentication successful")
                    
                    # Extract and store authentication token
                    token = self._extract_auth_token(resp)
                    if token:
                        print(f"SUCCESS Authentication token extracted and stored")
                    else:
                        print("WARNING  No authentication token found in response")
                    
                    # Extract context values for subsequent requests
                    self._extract_context_from_response(resp, "Authentication")
                else:
                    resp.failure(f"Authentication failed: {{resp.status_code}}")
                    print(f"ERROR Authentication failed: {{resp.status_code}}")
        except Exception as e:
            print(f"ERROR Authentication error: {{str(e)}}")
'''
    
    return auth_code

def generate_locust(input_path, out_path, target_host=None):
    # Check if input is HAR or YAML
    if input_path.endswith('.har'):
        # Process HAR file directly
        import json
        with open(input_path, "r", encoding="utf-8") as f:
            har_data = json.load(f)
        
        # Convert HAR to flows (simplified version)
        flows = []
        for entry in har_data.get("log", {}).get("entries", []):
            request = entry.get("request", {})
            response = entry.get("response", {})
            
            # Extract headers
            headers = {}
            for header in request.get("headers", []):
                headers[header["name"]] = header["value"]
            
            # Extract body
            body = ""
            if request.get("postData"):
                body = request["postData"].get("text", "")
            
            flow = {
                "method": request.get("method", "GET"),
                "url": request.get("url", ""),
                "headers": headers,
                "body": body,
                "status_code": response.get("status", 200)
            }
            flows.append(flow)
    else:
        # Process YAML file
        with open(input_path, "r", encoding="utf-8") as f:
            flows = yaml.safe_load(f)

    code = TEMPLATE_HEADER
    json_apis_count = 0
    auth_flows = []
    
    # Identify authentication flows
    for i, flow in enumerate(flows, 1):
        if is_authentication_flow(flow):
            auth_flows.append((i, flow))
    
    # Generate authentication code if found
    if auth_flows:
        code += generate_authentication_code(auth_flows, target_host)
    
    # Generate regular task flows
    for i, flow in enumerate(flows, 1):
        if not is_authentication_flow(flow):
            code += generate_step_code(i, flow, target_host)
        
        # Count APIs that will use enhanced JSON handling
        if flow.get("body") and flow["method"].lower() in ['put', 'post']:
            try:
                json.loads(flow.get("body"))
                json_apis_count += 1
            except (json.JSONDecodeError, TypeError):
                pass
                
        # Skip browser tasks for load testing - only generate HTTP tasks
        # if flow.get("frontend_task"):
        #     code += BROWSER_TEMPLATE.format(idx=i, url=flow["url"], wait_time=2)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"SUCCESS Observability-ready Locust script generated at {out_path}")
    if json_apis_count > 0:
        print(f"🔧 Enhanced JSON handling applied to {json_apis_count} PUT/POST API(s)")
        print("   - Using 'json' parameter for proper JSON serialization")
        print("   - Enhanced response validation for all APIs")
        print("   - Better error detection and reporting")
    
    # Print token management features
    print("🔐 Token Management Features:")
    print("   - Automatic token extraction from authentication responses")
    print("   - Token storage in user context for subsequent requests")
    print("   - Authorization header injection for protected endpoints")
    print("   - Permission-based access control (admin, manager, user, public)")
    print("   - Authentication state tracking per user")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python locust_generator.py <yaml_file> <output_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    output_file = sys.argv[2]
    generate_locust(yaml_file, output_file)
