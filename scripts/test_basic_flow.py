"""
Generated Locust script from flow data
Generated at: 2025-09-27T13:16:18.086230
Total requests: 3
Base URL: api.example.com
"""

from locust import HttpUser, task, between
import json
import random
import time


class TestUser(HttpUser):
    """
    Generated Locust user class from flow data.
    
    This class simulates user behavior based on the provided flow data.
    """
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Called when a user starts."""
        self.client.verify = False  # Disable SSL verification for testing
        print(f"Starting {self.__class__.__name__} user session...")
    
    def on_stop(self):
        """Called when a user stops."""
        print(f"Ending {self.__class__.__name__} user session...")
    

    @task(9)  # Higher priority for earlier requests
    def task_1_get(self):
        """GET / - Get Homepage"""
        url = "/"
        headers = {
        "Accept": "text/html",
        "User-Agent": "Mozilla/5.0"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(8)  # Higher priority for earlier requests
    def task_2_get(self):
        """GET /data - Get API Data"""
        url = "/data"
        headers = {
        "Accept": "application/json",
        "Authorization": "Bearer token123"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(7)  # Higher priority for earlier requests
    def task_3_post(self):
        """POST /resources - Create Resource"""
        url = "/resources"
        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer token123"
}
        
        data = {
        "name": "Test Resource",
        "description": "A test resource",
        "active": true
}
        
        with self.client.post(url, headers=headers, json=data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Expected status 201, got {response.status_code}")

# Usage Instructions:
# 1. Install Locust: pip install locust
# 2. Run the script: locust -f scripts/test_basic_flow.py --host=api.example.com
# 3. Open web UI: http://localhost:8089
# 4. Configure users and spawn rate in the web interface
# 5. Start the test and monitor results

# Alternative command line usage:
# locust -f scripts/test_basic_flow.py --host=api.example.com --users 10 --spawn-rate 2 --run-time 30s
