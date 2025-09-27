"""
Test script for the Locust generator utility.
"""

import json
from locust_generator import generate_locust_script_from_flow, LocustGenerator


def test_basic_flow():
    """Test basic flow conversion."""
    flow_data = {
        "metadata": {
            "version": "1.2",
            "total_entries": 3
        },
        "flows": [
            {
                "id": "flow_1",
                "name": "Get Homepage",
                "method": "GET",
                "url": "https://example.com/",
                "status_code": 200,
                "request_headers": [
                    {"name": "Accept", "value": "text/html"},
                    {"name": "User-Agent", "value": "Mozilla/5.0"}
                ],
                "response_time": 100
            },
            {
                "id": "flow_2",
                "name": "Get API Data",
                "method": "GET",
                "url": "https://api.example.com/data",
                "status_code": 200,
                "request_headers": [
                    {"name": "Accept", "value": "application/json"},
                    {"name": "Authorization", "value": "Bearer token123"}
                ],
                "response_time": 150
            },
            {
                "id": "flow_3",
                "name": "Create Resource",
                "method": "POST",
                "url": "https://api.example.com/resources",
                "status_code": 201,
                "request_headers": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Accept", "value": "application/json"},
                    {"name": "Authorization", "value": "Bearer token123"}
                ],
                "request_body": {
                    "name": "Test Resource",
                    "description": "A test resource",
                    "active": True
                },
                "response_time": 200
            }
        ]
    }
    
    # Generate script
    script_path = generate_locust_script_from_flow(
        flow_data,
        output_file="test_basic_flow.py",
        class_name="TestUser",
        wait_time_min=0.5,
        wait_time_max=2.0
    )
    
    print(f"✅ Generated script: {script_path}")
    
    # Read and display first few lines
    with open(script_path, 'r') as f:
        lines = f.readlines()
        print("\n📄 Script preview (first 20 lines):")
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line.rstrip()}")
        if len(lines) > 20:
            print("    ...")
    
    return script_path


def test_complex_flow():
    """Test complex flow with multiple methods and headers."""
    flow_data = {
        "metadata": {
            "version": "1.2",
            "total_entries": 5
        },
        "flows": [
            {
                "id": "flow_1",
                "name": "Login",
                "method": "POST",
                "url": "https://auth.example.com/login",
                "status_code": 200,
                "request_headers": [
                    {"name": "Content-Type", "value": "application/x-www-form-urlencoded"},
                    {"name": "Accept", "value": "application/json"}
                ],
                "request_body": {
                    "username": "testuser",
                    "password": "testpass"
                },
                "response_time": 300
            },
            {
                "id": "flow_2",
                "name": "Get Profile",
                "method": "GET",
                "url": "https://api.example.com/profile",
                "status_code": 200,
                "request_headers": [
                    {"name": "Accept", "value": "application/json"},
                    {"name": "Authorization", "value": "Bearer {{token}}"}
                ],
                "response_time": 120
            },
            {
                "id": "flow_3",
                "name": "Update Profile",
                "method": "PUT",
                "url": "https://api.example.com/profile",
                "status_code": 200,
                "request_headers": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Accept", "value": "application/json"},
                    {"name": "Authorization", "value": "Bearer {{token}}"}
                ],
                "request_body": {
                    "name": "Updated Name",
                    "email": "updated@example.com"
                },
                "response_time": 180
            },
            {
                "id": "flow_4",
                "name": "Get Dashboard",
                "method": "GET",
                "url": "https://app.example.com/dashboard",
                "status_code": 200,
                "request_headers": [
                    {"name": "Accept", "value": "text/html"},
                    {"name": "Authorization", "value": "Bearer {{token}}"}
                ],
                "response_time": 250
            },
            {
                "id": "flow_5",
                "name": "Logout",
                "method": "POST",
                "url": "https://auth.example.com/logout",
                "status_code": 200,
                "request_headers": [
                    {"name": "Content-Type", "value": "application/json"},
                    {"name": "Authorization", "value": "Bearer {{token}}"}
                ],
                "request_body": {},
                "response_time": 100
            }
        ]
    }
    
    # Generate script
    script_path = generate_locust_script_from_flow(
        flow_data,
        output_file="test_complex_flow.py",
        class_name="ComplexTestUser",
        wait_time_min=1.0,
        wait_time_max=5.0
    )
    
    print(f"✅ Generated complex script: {script_path}")
    return script_path


def test_validation():
    """Test error handling and validation."""
    print("\n🧪 Testing validation...")
    
    # Test empty flows
    try:
        empty_flow = {"flows": []}
        generate_locust_script_from_flow(empty_flow)
        print("❌ Should have failed with empty flows")
    except ValueError as e:
        print(f"✅ Correctly caught empty flows error: {e}")
    
    # Test missing flows key
    try:
        invalid_flow = {"metadata": {}}
        generate_locust_script_from_flow(invalid_flow)
        print("❌ Should have failed with missing flows")
    except ValueError as e:
        print(f"✅ Correctly caught missing flows error: {e}")


if __name__ == "__main__":
    print("🚀 Testing Locust Generator Utility")
    print("=" * 50)
    
    # Test basic flow
    print("\n1. Testing basic flow conversion...")
    basic_script = test_basic_flow()
    
    # Test complex flow
    print("\n2. Testing complex flow conversion...")
    complex_script = test_complex_flow()
    
    # Test validation
    print("\n3. Testing validation...")
    test_validation()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print(f"\n📁 Generated scripts:")
    print(f"   - {basic_script}")
    print(f"   - {complex_script}")
    print(f"\n🏃 To run a script:")
    print(f"   locust -f {basic_script} --host=https://example.com")
    print(f"   locust -f {complex_script} --host=https://api.example.com")
