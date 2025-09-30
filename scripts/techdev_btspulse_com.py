
"""
Generated Locust script from HAR file
Generated at: 2025-09-30T20:32:10.262875
Total requests: 37
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


    def _authenticate(self):
        """Handle authentication flow - runs once per user"""
        try:
            with self.client.post(
                '/Wizer/Authentication/Authenticate',
                headers={'Content-Type': 'application/json'},
                data=None,
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
                    resp.failure(f"Authentication failed: {resp.status_code}")
                    print(f"ERROR Authentication failed: {resp.status_code}")
        except Exception as e:
            print(f"ERROR Authentication error: {str(e)}")

    @task
    def step_5(self):
        """Application - get request (Permission: public)"""
        # Check if user has required permissions
        if "false" == "true" and not self._authenticated:
            print(f"WARNING  Skipping Application - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Application?fromGateway=false')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="Application"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "Application")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for public level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_6(self):
        """GetOfflineInfo - post request (Permission: public)"""
        # Check if user has required permissions
        if "false" == "true" and not self._authenticated:
            print(f"WARNING  Skipping GetOfflineInfo - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/VoteAPI/GetOfflineInfo')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Content-Type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.post(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="GetOfflineInfo"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "GetOfflineInfo")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for public level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_7(self):
        """GetAllEventsWithPrivileges - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping GetAllEventsWithPrivileges - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/EventAdmin/GetAllEventsWithPrivileges')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="GetAllEventsWithPrivileges"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "GetAllEventsWithPrivileges")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_8(self):
        """LoggedInUser - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping LoggedInUser - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Management/LoggedInUser')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="LoggedInUser"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "LoggedInUser")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_9(self):
        """ExistsActionXml - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping ExistsActionXml - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/EventAdmin/ExistsActionXml?actionName=managementhome&eventName={1}')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="ExistsActionXml"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "ExistsActionXml")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_10(self):
        """GetlLoggedinEvent - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping GetlLoggedinEvent - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/EventAdmin/GetlLoggedinEvent')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="GetlLoggedinEvent"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "GetlLoggedinEvent")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_11(self):
        """negotiate - get request (Permission: public)"""
        # Check if user has required permissions
        if "false" == "true" and not self._authenticated:
            print(f"WARNING  Skipping negotiate - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/signalr/negotiate?clientProtocol=1.5&connectionData=%5B%7B%22name%22%3A%22wizerproxy%22%7D%5D&_=1759239051683')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="negotiate"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "negotiate")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for public level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_12(self):
        """start - get request (Permission: public)"""
        # Check if user has required permissions
        if "false" == "true" and not self._authenticated:
            print(f"WARNING  Skipping start - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/signalr/start?transport=serverSentEvents&clientProtocol=1.5&connectionToken=zFT5jcpm9aecOXBmNvEgoy8oyWoW4x6DO5RCg7axXJ5MDK65fr5276rzPWKjdyqJ1yWsucr8I55x%2BhsRHgNgglf8PYUCTt85HvOzlDplH68CgHYb1HkBDq7S8JxTd%2Bmi&connectionData=%5B%7B%22name%22%3A%22wizerproxy%22%7D%5D&_=1759239051956')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="start"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "start")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for public level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_14(self):
        """Company - get request (Permission: manager)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping Company - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Company/Company?start=0&total=20&filterBy=&sortBy=UpdatedOn&sortOrder=desc')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="Company"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "Company")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for manager level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_17(self):
        """UpdateCompany - put request (Permission: manager)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UpdateCompany - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Company/UpdateCompany')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Content-Type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.put(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UpdateCompany"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UpdateCompany")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for manager level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_18(self):
        """UpdateCompany - put request (Permission: manager)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UpdateCompany - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Company/UpdateCompany')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Content-Type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.put(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UpdateCompany"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UpdateCompany")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for manager level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_19(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_21(self):
        """GetAllCompanys - get request (Permission: manager)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping GetAllCompanys - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/Company/GetAllCompanys')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="GetAllCompanys"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "GetAllCompanys")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for manager level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_23(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bh&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_24(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bha&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_26(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bhav&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_28(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bhave&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_30(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bhavesh&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_33(self):
        """UserProfile - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserProfile - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserProfile?userId=22665')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserProfile"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserProfile")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_34(self):
        """UserProfile - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserProfile - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserProfile?userId=84469')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserProfile"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserProfile")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_35(self):
        """UserProfile - post request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserProfile - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserProfile')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Content-Type': 'application/json', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.post(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserProfile"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserProfile")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")


    @task
    def step_36(self):
        """UserAdmin - get request (Permission: admin)"""
        # Check if user has required permissions
        if "true" == "true" and not self._authenticated:
            print(f"WARNING  Skipping UserAdmin - authentication required")
            return
        
        # Substitute context values in URL and body
        substituted_url = self._substitute_context_values('/Wizer/UserAdmin/UserAdmin?start=0&total=20&filterBy=bhavesh&sortBy=&sortOrder=')
        substituted_body = None
        
        # Add authentication headers if available
        auth_headers = self._add_auth_headers({'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest'})
        
        with self.client.get(
            substituted_url,
            headers=auth_headers,
            data=substituted_body,
            catch_response=True,
            name="UserAdmin"
        ) as resp:
            # Simplified response handling - let real issues surface
            if resp.status_code == 200:
                resp.success()
                # Extract tokens if this is an authentication endpoint
                if "false":
                    self._extract_auth_token(resp)
                # Extract context values for subsequent requests
                self._extract_context_from_response(resp, "UserAdmin")
            elif resp.status_code == 401:
                resp.failure("Authentication required - check credentials or token")
            elif resp.status_code == 403:
                resp.failure("Access denied - check permissions or token scope for admin level")
            elif resp.status_code == 404:
                resp.failure("Endpoint not found")
            elif resp.status_code >= 500:
                resp.failure(f"Server error: {resp.status_code}")
            else:
                resp.failure(f"Request failed: {resp.status_code}")



# Configuration for running the script
# Target host: https://techdev.btspulse.com
# Command to run: locust -f techdev_btspulse_com.py --host=<target_host>
# Web UI: http://localhost:8089
# Prometheus metrics: http://localhost:8001/metrics
