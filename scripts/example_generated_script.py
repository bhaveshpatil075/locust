"""
Generated Locust script from flow data
Generated at: 2025-09-27T13:16:46.089260
Total requests: 4
Base URL: example.com
"""

from locust import HttpUser, task, between
import json
import random
import time


class ExampleUser(HttpUser):
    """
    Generated Locust user class from flow data.
    
    This class simulates user behavior based on the provided flow data.
    """
    wait_time = between(1.0, 3.0)
    
    def on_start(self):
        """Called when a user starts."""
        self.client.verify = False  # Disable SSL verification for testing
        print(f"Starting {self.__class__.__name__} user session...")
    
    def on_stop(self):
        """Called when a user stops."""
        print(f"Ending {self.__class__.__name__} user session...")
    

    @task(9)  # Higher priority for earlier requests
    def task_1_get(self):
        """GET / - Homepage Load"""
        url = "/"
        headers = {
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(8)  # Higher priority for earlier requests
    def task_2_get(self):
        """GET /health - API Health Check"""
        url = "/health"
        headers = {
        "Accept": "application/json"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(7)  # Higher priority for earlier requests
    def task_3_post(self):
        """POST /auth/login - User Login"""
        url = "/auth/login"
        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
}
        
        data = {
        "username": "testuser",
        "password": "testpass"
}
        
        with self.client.post(url, headers=headers, json=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(6)  # Higher priority for earlier requests
    def task_4_get(self):
        """GET /user/profile - Get User Profile"""
        url = "/user/profile"
        headers = {
        "Accept": "application/json",
        "Authorization": "Bearer {{token}}"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

# Usage Instructions:
# 1. Install Locust: pip install locust
# 2. Run the script: locust -f scripts/example_generated_script.py --host=example.com
# 3. Open web UI: http://localhost:8089
# 4. Configure users and spawn rate in the web interface
# 5. Start the test and monitor results

# Alternative command line usage:
# locust -f scripts/example_generated_script.py --host=example.com --users 10 --spawn-rate 2 --run-time 30s
