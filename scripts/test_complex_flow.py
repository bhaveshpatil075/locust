"""
Generated Locust script from flow data
Generated at: 2025-09-27T13:16:18.122415
Total requests: 5
Base URL: auth.example.com
"""

from locust import HttpUser, task, between
import json
import random
import time


class ComplexTestUser(HttpUser):
    """
    Generated Locust user class from flow data.
    
    This class simulates user behavior based on the provided flow data.
    """
    wait_time = between(1.0, 5.0)
    
    def on_start(self):
        """Called when a user starts."""
        self.client.verify = False  # Disable SSL verification for testing
        print(f"Starting {self.__class__.__name__} user session...")
    
    def on_stop(self):
        """Called when a user stops."""
        print(f"Ending {self.__class__.__name__} user session...")
    

    @task(9)  # Higher priority for earlier requests
    def task_1_post(self):
        """POST /login - Login"""
        url = "/login"
        headers = {
        "Content-Type": "application/x-www-form-urlencoded",
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

    @task(8)  # Higher priority for earlier requests
    def task_2_get(self):
        """GET /profile - Get Profile"""
        url = "/profile"
        headers = {
        "Accept": "application/json",
        "Authorization": "Bearer {{token}}"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(7)  # Higher priority for earlier requests
    def task_3_put(self):
        """PUT /profile - Update Profile"""
        url = "/profile"
        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer {{token}}"
}
        
        data = {
        "name": "Updated Name",
        "email": "updated@example.com"
}
        
        with self.client.put(url, headers=headers, json=data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(6)  # Higher priority for earlier requests
    def task_4_get(self):
        """GET /dashboard - Get Dashboard"""
        url = "/dashboard"
        headers = {
        "Accept": "text/html",
        "Authorization": "Bearer {{token}}"
}
        
        with self.client.get(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

    @task(5)  # Higher priority for earlier requests
    def task_5_post(self):
        """POST /logout - Logout"""
        url = "/logout"
        headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {{token}}"
}
        
        with self.client.post(url, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Expected status 200, got {response.status_code}")

# Usage Instructions:
# 1. Install Locust: pip install locust
# 2. Run the script: locust -f scripts/test_complex_flow.py --host=auth.example.com
# 3. Open web UI: http://localhost:8089
# 4. Configure users and spawn rate in the web interface
# 5. Start the test and monitor results

# Alternative command line usage:
# locust -f scripts/test_complex_flow.py --host=auth.example.com --users 10 --spawn-rate 2 --run-time 30s
