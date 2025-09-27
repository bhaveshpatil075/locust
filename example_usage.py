"""
Example usage of the Locust generator utility.
"""

from locust_generator import generate_locust_script_from_flow

# Example flow data (typically from /convert endpoint)
flow_data = {
    "metadata": {
        "version": "1.2",
        "total_entries": 4,
        "converted_at": "2024-01-01T12:00:00Z"
    },
    "flows": [
        {
            "id": "flow_1",
            "name": "Homepage Load",
            "method": "GET",
            "url": "https://example.com/",
            "status_code": 200,
            "request_headers": [
                {"name": "Accept", "value": "text/html,application/xhtml+xml"},
                {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ],
            "response_time": 120
        },
        {
            "id": "flow_2",
            "name": "API Health Check",
            "method": "GET",
            "url": "https://api.example.com/health",
            "status_code": 200,
            "request_headers": [
                {"name": "Accept", "value": "application/json"}
            ],
            "response_time": 50
        },
        {
            "id": "flow_3",
            "name": "User Login",
            "method": "POST",
            "url": "https://api.example.com/auth/login",
            "status_code": 200,
            "request_headers": [
                {"name": "Content-Type", "value": "application/json"},
                {"name": "Accept", "value": "application/json"}
            ],
            "request_body": {
                "username": "testuser",
                "password": "testpass"
            },
            "response_time": 300
        },
        {
            "id": "flow_4",
            "name": "Get User Profile",
            "method": "GET",
            "url": "https://api.example.com/user/profile",
            "status_code": 200,
            "request_headers": [
                {"name": "Accept", "value": "application/json"},
                {"name": "Authorization", "value": "Bearer {{token}}"}
            ],
            "response_time": 150
        }
    ]
}

def main():
    print("🚀 Generating Locust script from flow data...")
    
    # Generate the script
    script_path = generate_locust_script_from_flow(
        flow_data,
        output_file="example_generated_script.py",
        class_name="ExampleUser",
        wait_time_min=1.0,
        wait_time_max=3.0
    )
    
    print(f"✅ Generated script: {script_path}")
    print(f"\n🏃 To run the script:")
    print(f"   locust -f {script_path} --host=https://example.com")
    print(f"\n🌐 Web UI will be available at: http://localhost:8089")
    
    # Show a preview of the generated script
    print(f"\n📄 Script preview:")
    with open(script_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:30]):
            print(f"{i+1:2d}: {line.rstrip()}")
        if len(lines) > 30:
            print("    ...")

if __name__ == "__main__":
    main()
