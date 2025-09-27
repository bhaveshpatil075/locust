
"""
Generated Locust script from HAR file
Generated at: 2025-09-27T18:12:35.732135
Total requests: 135
"""

from locust import HttpUser, task, between, events
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


    @task
    def step_1(self):
        try:
            with self.client.post(
                "/Wizer/Authentication/Authenticate",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '37', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=json.dumps({'mimeType': 'application/x-www-form-urlencoded; charset=UTF-8', 'text': 'email=admin&pass=wizer&language=en-US', 'params': [{'name': 'email', 'value': 'admin'}, {'name': 'pass', 'value': 'wizer'}, {'name': 'language', 'value': 'en-US'}]}),
                cookies=None,
                catch_response=True,
                name="Authenticate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="post",
                name="Authenticate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_2(self):
        try:
            with self.client.post(
                "/Wizer/Authentication/GetParticipations",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '0', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetParticipations"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="post",
                name="GetParticipations",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_3(self):
        try:
            with self.client.post(
                "/Wizer/Authentication/GetApplications",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '0', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetApplications"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="post",
                name="GetApplications",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_4(self):
        try:
            with self.client.post(
                "/Wizer/Authentication/SelectParticipation",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '55', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=json.dumps({'mimeType': 'application/x-www-form-urlencoded; charset=UTF-8', 'text': 'participationId=176282&application=Management&language=', 'params': [{'name': 'participationId', 'value': '176282'}, {'name': 'application', 'value': 'Management'}, {'name': 'language', 'value': ''}]}),
                cookies=None,
                catch_response=True,
                name="SelectParticipation"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="post",
                name="SelectParticipation",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_5(self):
        try:
            with self.client.get(
                "/Wizer/Application?fromGateway=false",
                headers={'Accept': 'text/html, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="Application"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="Application",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_6(self):
        try:
            with self.client.post(
                "/Wizer/VoteAPI/GetOfflineInfo",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '0', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetOfflineInfo"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="post",
                name="GetOfflineInfo",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_7(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/layout.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="layout.html"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="layout.html",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_8(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/validator/validator.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="validator.html"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="validator.html",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_9(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/management/management.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="management"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="management",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_10(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/eventSelector.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="eventSelector"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="eventSelector",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_11(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/phonebank/phonebankHomePage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="phonebankHomePage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="phonebankHomePage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_12(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/phonebank/phonebankHomePageList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="phonebankHomePageList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="phonebankHomePageList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_13(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/sideBySidePageModal.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sideBySidePageModal"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sideBySidePageModal",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_14(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessorHomePage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessorHomePage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessorHomePage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_15(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessorAgendaView.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessorAgendaView"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessorAgendaView",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_16(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/createEvent.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="createEvent"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="createEvent",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_17(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/collections/encodingSelector.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="encodingSelector"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="encodingSelector",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_18(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationHomePage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationHomePage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationHomePage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_19(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/timezoneList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="timezoneList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="timezoneList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_20(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationSessionList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationSessionList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationSessionList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_21(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationSessionUsers.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationSessionUsers"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationSessionUsers",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_22(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationBatchTemplates.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationBatchTemplates"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationBatchTemplates",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_23(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationBatchSessionTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationBatchSessionTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationBatchSessionTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_24(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationModal.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationModal"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationModal",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_25(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/registrationFilters.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="registrationFilters"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="registrationFilters",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_26(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/RegistrationBatchSessionListTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="RegistrationBatchSessionListTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="RegistrationBatchSessionListTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_27(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/operator/operatorHomePage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="operatorHomePage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="operatorHomePage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_28(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/operator/actionXmlTextbox.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="actionXmlTextbox"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="actionXmlTextbox",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_29(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/operator/fullScreenModalTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="fullScreenModalTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="fullScreenModalTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_30(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/sessions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sessions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sessions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_31(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/sessionList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sessionList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sessionList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_32(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/adminOverview/adminOverviewSessionDetails.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="adminOverviewSessionDetails"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="adminOverviewSessionDetails",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_33(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/adminOverview/adminOverviewPage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="adminOverviewPage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="adminOverviewPage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_34(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/adminOverview/adminOverviewUserList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="adminOverviewUserList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="adminOverviewUserList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_35(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/adminOverview/adminOverviewFilter.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="adminOverviewFilter"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="adminOverviewFilter",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_36(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/cloudFront/cloudFrontPage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="cloudFrontPage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="cloudFrontPage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_37(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/cloudFront/cloudFrontUrls.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="cloudFrontUrls"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="cloudFrontUrls",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_38(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/template/templatePage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="templatePage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="templatePage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_39(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/company/company.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="company"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="company",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_40(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/header/leftMenu.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="leftMenu"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="leftMenu",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_41(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/management/importFile.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="importFile"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="importFile",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_42(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/management/confirmPage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="confirmPage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="confirmPage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_43(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/management/loadingPage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="loadingPage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="loadingPage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_44(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/editCohort.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="editCohort"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="editCohort",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_45(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/cohortParticipant.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="cohortParticipant"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="cohortParticipant",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_46(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/cohortParticipantTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="cohortParticipantTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="cohortParticipantTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_47(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/company/companySelector.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="companySelector"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="companySelector",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_48(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/addSession.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addSession"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addSession",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_49(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/additionalInfoTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="additionalInfoTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="additionalInfoTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_50(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/leadAssessorTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="leadAssessorTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="leadAssessorTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_51(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/editSession.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="editSession"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="editSession",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_52(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/assessmentPhone.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentPhone"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentPhone",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_53(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/editDelivery.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="editDelivery"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="editDelivery",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_54(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/deliveryParticipant.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="deliveryParticipant"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="deliveryParticipant",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_55(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/deliveryFacilitator.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="deliveryFacilitator"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="deliveryFacilitator",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_56(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/registration/deliveryParticipantTemplate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="deliveryParticipantTemplate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="deliveryParticipantTemplate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_57(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/user.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="user"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="user",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_58(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/permissionListInSessions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="permissionListInSessions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="permissionListInSessions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_59(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/userCreate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="userCreate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="userCreate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_60(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/operator/sectionList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sectionList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sectionList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_61(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/collections/sectionListPage.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sectionListPage"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sectionListPage",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_62(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/sessionDetails.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="sessionDetails"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="sessionDetails",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_63(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/userProfile.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="userProfile"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="userProfile",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_64(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/groupSelector.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="groupSelector"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="groupSelector",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_65(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/questionListInProfile.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="questionListInProfile"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="questionListInProfile",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_66(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/permissionListInProfile.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="permissionListInProfile"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="permissionListInProfile",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_67(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/userNotifications.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="userNotifications"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="userNotifications",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_68(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/models/company.tr.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="company.tr"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="company.tr",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_69(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/company/companyCreate.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="companyCreate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="companyCreate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_70(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTeam.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTeam"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTeam",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_71(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTeamAddUsers.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTeamAddUsers"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTeamAddUsers",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_72(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTeamAddQuestions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTeamAddQuestions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTeamAddQuestions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_73(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTestUsers.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTestUsers"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTestUsers",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_74(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/testUsers.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="testUsers"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="testUsers",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_75(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTestAddUsers.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTestAddUsers"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTestAddUsers",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_76(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/users/addTestAddQuestions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="addTestAddQuestions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="addTestAddQuestions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_77(self):
        try:
            with self.client.get(
                "/Wizer/EventAdmin/GetAllEventsWithPrivileges",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetAllEventsWithPrivileges"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="GetAllEventsWithPrivileges",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_78(self):
        try:
            with self.client.get(
                "/Wizer/EventAdmin/ExistsActionXml?actionName=managementhome&eventName={1}",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="ExistsActionXml"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="ExistsActionXml",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_79(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/footer/footer.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="footer.html"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="footer.html",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_80(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/header/managementMenu.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="managementMenu"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="managementMenu",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_81(self):
        try:
            with self.client.get(
                "/Wizer/Management/LoggedInUser",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="LoggedInUser"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="LoggedInUser",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_82(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/experienceManagement.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="experienceManagement"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="experienceManagement",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_83(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/collections/experienceManagementEvents.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="experienceManagementEvents"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="experienceManagementEvents",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_84(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/importZipDialog.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="importZipDialog"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="importZipDialog",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_85(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/updateZipDialog.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="updateZipDialog"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="updateZipDialog",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_86(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/events/simpleAlertPopup.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="simpleAlertPopup"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="simpleAlertPopup",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_87(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/copyEvent.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="copyEvent"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="copyEvent",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_88(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/exportZipDialog.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="exportZipDialog"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="exportZipDialog",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_89(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/reporting.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="reporting"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="reporting",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_90(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/reportingList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="reportingList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="reportingList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_91(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/Language.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="Language"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="Language",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_92(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/LanguageConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="LanguageConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="LanguageConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_93(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/languageList.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="languageList"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="languageList",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_94(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notifications.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notifications"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notifications",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_95(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationReports.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationReports"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationReports",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_96(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_97(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationOverview.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationOverview"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationOverview",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_98(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationRecipients.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationRecipients"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationRecipients",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_99(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationDistributionRules.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationDistributionRules"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationDistributionRules",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_100(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationDistributionCondition.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationDistributionCondition"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationDistributionCondition",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_101(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationReportsData.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationReportsData"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationReportsData",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_102(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/notificationTimeBasedVote.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="notificationTimeBasedVote"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="notificationTimeBasedVote",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_103(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExport.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExport"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExport",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_104(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExportConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExportConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExportConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_105(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExportComposeNew.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExportComposeNew"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExportComposeNew",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_106(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExportAddQuestions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExportAddQuestions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExportAddQuestions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_107(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExportAddNewQuestions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExportAddNewQuestions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExportAddNewQuestions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_108(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/dataExportEventData.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="dataExportEventData"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="dataExportEventData",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_109(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/previewdataexport.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="previewdataexport"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="previewdataexport",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_110(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_111(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentBasicData.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentBasicData"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentBasicData",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_112(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessmentCapabilities.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentCapabilities"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentCapabilities",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_113(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessmentbehaviour.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentbehaviour"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentbehaviour",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_114(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessmentCapabilityMatrixOptions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentCapabilityMatrixOptions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentCapabilityMatrixOptions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_115(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/assessment/assessmentBehaviourOptions.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentBehaviourOptions"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentBehaviourOptions",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_116(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentAssessors.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentAssessors"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentAssessors",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_117(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentAssessorsOneAssessor.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentAssessorsOneAssessor"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentAssessorsOneAssessor",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_118(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentModuleExercise.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentModuleExercise"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentModuleExercise",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_119(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentModuleGroups.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentModuleGroups"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentModuleGroups",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_120(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentModuleGroup.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentModuleGroup"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentModuleGroup",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_121(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentModules.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentModules"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentModules",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_122(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/assessmentModule.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="assessmentModule"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="assessmentModule",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_123(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/batchTemplates.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="batchTemplates"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="batchTemplates",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_124(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/batchTemplatesConfig.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="batchTemplatesConfig"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="batchTemplatesConfig",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_125(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/batchTemplatesPattern.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="batchTemplatesPattern"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="batchTemplatesPattern",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_126(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/experienceConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="experienceConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="experienceConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_127(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/experienceSubsystemConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="experienceSubsystemConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="experienceSubsystemConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_128(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/userExpiry.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="userExpiry"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="userExpiry",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_129(self):
        try:
            with self.client.get(
                "/Wizer/Authoring/templates/experienceManagement/experienceOtherConfiguration.dot.html?cacheId=23209",
                headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="experienceOtherConfiguration"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="experienceOtherConfiguration",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_130(self):
        try:
            with self.client.get(
                "/Wizer/EventAdmin/GetlLoggedinEvent",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetlLoggedinEvent"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="GetlLoggedinEvent",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_131(self):
        try:
            with self.client.get(
                "/Wizer/signalr/negotiate?clientProtocol=1.5&connectionData=%5B%7B%22name%22%3A%22wizerproxy%22%7D%5D&_=1758965782681",
                headers={'Accept': 'text/plain, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Type': 'application/json; charset=UTF-8', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="negotiate"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="negotiate",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_132(self):
        try:
            with self.client.get(
                "/Wizer/signalr/start?transport=webSockets&clientProtocol=1.5&connectionToken=3EM%2F%2FZHXEb68gaJzQrwLtc0tXV%2BDRIxtf5t%2F0QR1TM9a4f4ogBYcLsyOOKWmgEsfW9VVG6VnC%2Biy5dABHPWfw60dMVLSt%2FPC8qKQtSXYfiYr9RRv7RO%2F8aCjvvCP5Smh&connectionData=%5B%7B%22name%22%3A%22wizerproxy%22%7D%5D&_=1758965782873",
                headers={'Accept': 'text/plain, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Type': 'application/json; charset=UTF-8', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="start"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="start",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_133(self):
        try:
            with self.client.get(
                "/Wizer/Company/Company?start=0&total=20&filterBy=&sortBy=UpdatedOn&sortOrder=desc",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="Company"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="Company",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_134(self):
        try:
            with self.client.put(
                "/Wizer/Company/UpdateCompany",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Content-Length': '202', 'Content-Type': 'application/json', 'Host': 'localhost', 'Origin': 'http://localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=json.dumps({'mimeType': 'application/json', 'text': '{"id":122,"pId":0,"name":"Bhavesh Patil updated","description":"A company known for its innovative products and iconic branding in cartoons and media.","enabled":true,"UpdatedOn":"2025-09-23T13:51:33Z"}'}),
                cookies=None,
                catch_response=True,
                name="UpdateCompany"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="put",
                name="UpdateCompany",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )

    @task
    def step_135(self):
        try:
            with self.client.get(
                "/Wizer/EventAdmin/GetlLoggedinEvent",
                headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Accept-Encoding': 'gzip, deflate, br, zstd', 'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7', 'Connection': 'keep-alive', 'Host': 'localhost', 'Referer': 'http://localhost/Wizer/Authoring/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest', 'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"'},
                data=None,
                cookies=None,
                catch_response=True,
                name="GetlLoggedinEvent"
            ) as resp:
                # Handle different response scenarios with meaningful error messages
                if resp.status_code == 0:
                    resp.failure("Connection failed - Server may be down or unreachable. Check if the target application is running and accessible.")
                elif resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            data = resp.json()

                            resp.success()
                        except Exception as e:
                            resp.failure(f"Failed to parse JSON response: {str(e)}")
                    else:
                        resp.success()
                elif resp.status_code == 404:
                    resp.failure(f"Endpoint not found (404) - The URL '{resp.url}' does not exist on the server.")
                elif resp.status_code == 500:
                    resp.failure(f"Internal server error (500) - The server encountered an error processing the request to '{resp.url}'.")
                elif resp.status_code == 401:
                    resp.failure(f"Unauthorized (401) - Authentication required for '{resp.url}'. Check credentials or session.")
                elif resp.status_code == 403:
                    resp.failure(f"Forbidden (403) - Access denied for '{resp.url}'. Check permissions.")
                elif resp.status_code == 400:
                    resp.failure(f"Bad request (400) - Invalid request to '{resp.url}'. Check request parameters.")
                elif resp.status_code >= 500:
                    resp.failure(f"Server error ({resp.status_code}) - The server is experiencing issues with '{resp.url}'.")
                elif resp.status_code >= 400:
                    resp.failure(f"Client error ({resp.status_code}) - Request failed for '{resp.url}'.")
                else:
                    resp.failure(f"Unexpected response status {resp.status_code} for '{resp.url}'.")
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
                error_msg = f"Unexpected error: {str(e)}"
            
            # Use Locust's events to report the failure
            events.request.fire(
                request_type="get",
                name="GetlLoggedinEvent",
                response_time=0,
                response_length=0,
                response=None,
                context=self,
                exception=e
            )


# Configuration for running the script
# Command to run: locust -f locust_script_20250927_181235.py --host=<target_host>
# Web UI: http://localhost:8089
# Prometheus metrics: http://localhost:8001/metrics
