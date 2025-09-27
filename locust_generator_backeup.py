"""
Locust Script Generator Utility

This module provides utilities to convert flow JSON data into executable Locust scripts.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class LocustGenerator:
    """Generates Locust scripts from flow JSON data."""
    
    def __init__(self, scripts_dir: str = "scripts"):
        """
        Initialize the Locust generator.
        
        Args:
            scripts_dir: Directory to save generated scripts
        """
        self.scripts_dir = Path(scripts_dir)
        self.scripts_dir.mkdir(exist_ok=True)
    
    def generate_locust_script(
        self, 
        flow_data: Dict[str, Any], 
        filename: Optional[str] = None,
        class_name: str = "GeneratedUser",
        wait_time_min: float = 1.0,
        wait_time_max: float = 3.0,
        base_url: Optional[str] = None
    ) -> str:
        """
        Generate a Locust script from flow data.
        
        Args:
            flow_data: Flow data containing requests to convert
            filename: Output filename (auto-generated if None)
            class_name: Name of the HttpUser class
            wait_time_min: Minimum wait time between requests
            wait_time_max: Maximum wait time between requests
            base_url: Base URL for requests (auto-detected if None)
            
        Returns:
            Path to the generated script file
        """
        flows = flow_data.get('flows', [])
        if not flows:
            raise ValueError("No flows found in the provided data")
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"locustfile_{timestamp}.py"
        
        # Ensure .py extension
        if not filename.endswith('.py'):
            filename += '.py'
        
        script_path = self.scripts_dir / filename
        
        # Extract base URL if not provided
        if not base_url:
            base_url = self._extract_base_url(flows)
        
        # Generate script content
        script_content = self._generate_script_content(
            flows, 
            flow_data.get('metadata', {}),
            class_name,
            wait_time_min,
            wait_time_max,
            base_url,
            filename
        )
        
        # Write script to file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def _extract_base_url(self, flows: List[Dict[str, Any]]) -> str:
        """Extract base URL from flows."""
        domains = set()
        for flow in flows:
            url = flow.get('url', '')
            if '://' in url:
                domain = url.split('/')[2]
                domains.add(domain)
        
        return list(domains)[0] if domains else "http://localhost"
    
    def _generate_script_content(
        self,
        flows: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        class_name: str,
        wait_time_min: float,
        wait_time_max: float,
        base_url: str,
        filename: str
    ) -> str:
        """Generate the complete Locust script content."""
        
        # Generate script header
        script_content = f'''"""
Generated Locust script from flow data
Generated at: {datetime.now().isoformat()}
Total requests: {len(flows)}
Base URL: {base_url}
"""

from locust import HttpUser, task, between
import json
import random
import time


class {class_name}(HttpUser):
    """
    Generated Locust user class from flow data.
    
    This class simulates user behavior based on the provided flow data.
    """
    wait_time = between({wait_time_min}, {wait_time_max})
    
    def on_start(self):
        """Called when a user starts."""
        self.client.verify = False  # Disable SSL verification for testing
        print(f"Starting {{self.__class__.__name__}} user session...")
    
    def on_stop(self):
        """Called when a user stops."""
        print(f"Ending {{self.__class__.__name__}} user session...")
    
'''
        
        # Generate task methods for each flow
        for i, flow in enumerate(flows):
            task_method = self._generate_task_method(flow, i + 1)
            script_content += task_method
        
        # Add footer with usage instructions
        script_content += f'''
# Usage Instructions:
# 1. Install Locust: pip install locust
# 2. Run the script: locust -f {self.scripts_dir.name}/{filename} --host={base_url}
# 3. Open web UI: http://localhost:8089
# 4. Configure users and spawn rate in the web interface
# 5. Start the test and monitor results

# Alternative command line usage:
# locust -f {self.scripts_dir.name}/{filename} --host={base_url} --users 10 --spawn-rate 2 --run-time 30s
'''
        
        return script_content
    
    def _generate_task_method(self, flow: Dict[str, Any], task_number: int) -> str:
        """Generate a task method for a single flow."""
        method = flow.get('method', 'GET').upper()
        url = flow.get('url', '')
        headers = flow.get('request_headers', [])
        body = flow.get('request_body', {})
        expected_status = flow.get('status_code', 200)
        
        # Convert headers to dict
        headers_dict = self._convert_headers_to_dict(headers)
        
        # Extract path from URL
        path = self._extract_path_from_url(url)
        
        # Generate task method name
        task_name = f"task_{task_number}_{method.lower()}"
        
        # Generate method docstring
        docstring = f'        """{method} {path} - {flow.get("name", f"Request {task_number}")}"""'
        
        # Generate task method
        task_method = f'''
    @task({max(1, 10 - task_number)})  # Higher priority for earlier requests
    def {task_name}(self):
{docstring}
        url = "{path}"
        headers = {json.dumps(headers_dict, indent=8)}
        
'''
        
        # Add request body handling for POST/PUT/PATCH requests
        if body and method in ['POST', 'PUT', 'PATCH']:
            if isinstance(body, dict):
                task_method += f'''        data = {json.dumps(body, indent=8)}
        
        with self.client.{method.lower()}(url, headers=headers, json=data, catch_response=True) as response:
            if response.status_code == {expected_status}:
                response.success()
            else:
                response.failure(f"Expected status {expected_status}, got {{response.status_code}}")
'''
            else:
                task_method += f'''        data = {json.dumps(str(body), indent=8)}
        
        with self.client.{method.lower()}(url, headers=headers, data=data, catch_response=True) as response:
            if response.status_code == {expected_status}:
                response.success()
            else:
                response.failure(f"Expected status {expected_status}, got {{response.status_code}}")
'''
        else:
            task_method += f'''        with self.client.{method.lower()}(url, headers=headers, catch_response=True) as response:
            if response.status_code == {expected_status}:
                response.success()
            else:
                response.failure(f"Expected status {expected_status}, got {{response.status_code}}")
'''
        
        return task_method
    
    def _convert_headers_to_dict(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Convert headers list to dictionary."""
        headers_dict = {}
        for header in headers:
            if isinstance(header, dict) and 'name' in header and 'value' in header:
                headers_dict[header['name']] = header['value']
        return headers_dict
    
    def _extract_path_from_url(self, url: str) -> str:
        """Extract path from full URL."""
        if '://' in url:
            parts = url.split('/')
            if len(parts) > 3:
                return '/' + '/'.join(parts[3:])
            else:
                return '/'
        return url


def generate_locust_script_from_flow(
    flow_data: Dict[str, Any],
    output_file: Optional[str] = None,
    scripts_dir: str = "scripts",
    **kwargs
) -> str:
    """
    Convenience function to generate a Locust script from flow data.
    
    Args:
        flow_data: Flow data containing requests to convert
        output_file: Output filename (auto-generated if None)
        scripts_dir: Directory to save the script
        **kwargs: Additional arguments passed to LocustGenerator
        
    Returns:
        Path to the generated script file
        
    Example:
        >>> flow_data = {
        ...     "flows": [
        ...         {
        ...             "method": "GET",
        ...             "url": "https://api.example.com/users",
        ...             "status_code": 200,
        ...             "request_headers": [{"name": "Accept", "value": "application/json"}]
        ...         }
        ...     ]
        ... }
        >>> script_path = generate_locust_script_from_flow(flow_data)
        >>> print(f"Generated script: {script_path}")
    """
    generator = LocustGenerator(scripts_dir)
    return generator.generate_locust_script(flow_data, output_file, **kwargs)


if __name__ == "__main__":
    # Example usage
    example_flow_data = {
        "metadata": {
            "version": "1.2",
            "total_entries": 2
        },
        "flows": [
            {
                "id": "flow_1",
                "name": "Get Users",
                "method": "GET",
                "url": "https://api.example.com/users",
                "status_code": 200,
                "request_headers": [
                    {"name": "Accept", "value": "application/json"},
                    {"name": "User-Agent", "value": "Locust/1.0"}
                ],
                "response_time": 150
            },
            {
                "id": "flow_2",
                "name": "Create User",
                "method": "POST",
                "url": "https://api.example.com/users",
                "status_code": 201,
                "request_headers": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Accept", "value": "application/json"}
                ],
                "request_body": {
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "response_time": 200
            }
        ]
    }
    
    # Generate script
    script_path = generate_locust_script_from_flow(example_flow_data)
    print(f"Generated Locust script: {script_path}")
    print(f"Run with: locust -f {script_path} --host=https://api.example.com")
