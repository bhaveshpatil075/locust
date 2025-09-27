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

# Start Prometheus metrics server on port 8001
start_http_server(8001)

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

    def on_start(self):
        # Shared context for correlation
        self._context = {}
        
        # Test initial connection to provide early feedback
        try:
            with self.client.get("/", catch_response=True) as response:
                if response.status_code == 0:
                    print("⚠️  WARNING: Cannot connect to the target server. Please ensure the application is running and accessible.")
                elif response.status_code >= 400:
                    print(f"⚠️  WARNING: Server returned status {response.status_code}. Check if the application is properly configured.")
                else:
                    print("✅ Successfully connected to the target server.")
                response.success()  # Mark the test response as successful
        except Exception as e:
            print(f"⚠️  WARNING: Connection test failed - {str(e)}")
    
    def context(self):
        return self._context
'''

STEP_TEMPLATE = """
    @task
    def step_{idx}(self):
        try:
            with self.client.{method}(
                "{url}",
                headers={headers},
                data={body},
                cookies={cookies},
                catch_response=True,
                name="{name}"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()
{set_context_code}
                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {{str(e)}}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{{resp.url}}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{{resp.url}}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{{resp.url}}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{{resp.url}}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{{resp.url}}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({{resp.status_code}}) - The server is experiencing issues with '{{resp.url}}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({{resp.status_code}}) - Request failed for '{{resp.url}}'.")
                else:
                    resp.failure(f"Unexpected response status {{resp.status_code}} for '{{resp.url}}'.")
        except Exception as e:
            # Handle connection errors and other exceptions
            error_msg = ""
            if "ConnectionError" in str(type(e).__name__):
                error_msg = "Connection error - Unable to connect to the server. Check if the target application is running."
            elif "Timeout" in str(type(e).__name__):
                error_msg = "Request timeout - The server took too long to respond. Check server performance."
            elif "SSLError" in str(type(e).__name__):
                error_msg = "SSL error - Certificate or SSL configuration issue."
            else:
                error_msg = f"Unexpected error: {{str(e)}}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="{method}",
                name="{name}",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )
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

def generate_step_code(idx, flow):
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
    
    headers_code = str(flow.get("headers", {}))
    
    # Properly escape JSON body data to avoid syntax errors
    if flow.get("body"):
        try:
            # Try to parse as JSON to validate and re-serialize properly
            body_data = json.loads(flow.get("body"))
            body_code = f'json.dumps({repr(body_data)})'
        except (json.JSONDecodeError, TypeError):
            # If not valid JSON, escape the string properly
            body_code = repr(flow.get("body"))
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
    
    return STEP_TEMPLATE.format(
        idx=idx,
        method=flow["method"].lower(),
        url=relative_url,
        headers=headers_code,
        body=body_code,
        cookies=cookies_code,
        name=task_name,
        set_context_code=set_context_code
    )

def generate_locust(yaml_path, out_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        flows = yaml.safe_load(f)

    code = TEMPLATE_HEADER
    for i, flow in enumerate(flows, 1):
        code += generate_step_code(i, flow)
        # Skip browser tasks for load testing - only generate HTTP tasks
        # if flow.get("frontend_task"):
        #     code += BROWSER_TEMPLATE.format(idx=i, url=flow["url"], wait_time=2)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✅ Observability-ready Locust script generated at {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python locust_generator.py <yaml_file> <output_file>")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    output_file = sys.argv[2]
    generate_locust(yaml_file, output_file)
