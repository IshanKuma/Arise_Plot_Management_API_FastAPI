"""
Performance and load testing for the API endpoints.
Uses locust for load testing.

Run with:
    pip install locust
    locust -f tests/test_performance.py --host=http://localhost:8000
"""
import random
import json
from locust import HttpUser, task, between


class AriseAPIUser(HttpUser):
    """Simulated user for load testing the Arise API."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup method called when user starts."""
        # Get authentication tokens for different roles
        self.tokens = {}
        self.get_auth_tokens()
    
    def get_auth_tokens(self):
        """Get JWT tokens for different user roles."""
        roles = [
            ("super_admin", "GSEZ"),
            ("zone_admin", "OSEZ"), 
            ("normal_user", "GABON")
        ]
        
        for i, (role, zone) in enumerate(roles):
            response = self.client.post("/api/v1/auth/token", json={
                "userId": f"load_test_{role}_{i}",
                "role": role,
                "zone": zone
            })
            
            if response.status_code == 200:
                self.tokens[role] = response.json()["access_token"]
    
    def get_auth_headers(self, role="super_admin"):
        """Get authorization headers for given role."""
        token = self.tokens.get(role, "")
        return {"Authorization": f"Bearer {token}"}
    
    @task(10)
    def get_available_plots(self):
        """Test getting available plots (high frequency)."""
        headers = self.get_auth_headers("normal_user")
        self.client.get("/api/v1/plots/available", headers=headers)
    
    @task(5)
    def get_available_plots_with_filters(self):
        """Test getting plots with filters."""
        headers = self.get_auth_headers("zone_admin")
        params = "?country=Gabon&zoneCode=GSEZ"
        self.client.get(f"/api/v1/plots/available{params}", headers=headers)
    
    @task(3)
    def generate_auth_token(self):
        """Test token generation."""
        roles = ["super_admin", "zone_admin", "normal_user"]
        zones = ["GSEZ", "OSEZ", "GABON", "TEST"]
        
        self.client.post("/api/v1/auth/token", json={
            "userId": f"perf_test_{random.randint(1, 1000)}",
            "role": random.choice(roles),
            "zone": random.choice(zones)
        })
    
    @task(2)
    def update_plot(self):
        """Test plot updates (moderate frequency)."""
        headers = self.get_auth_headers("super_admin")
        
        self.client.put("/api/v1/plots/update-plot", 
            headers=headers,
            json={
                "country": "Gabon",
                "zoneCode": "GSEZ", 
                "phase": random.randint(1, 3),
                "plotName": f"PERF-TEST-{random.randint(1, 100)}",
                "companyName": f"Load Test Company {random.randint(1, 50)}",
                "sector": random.choice(["Technology", "Manufacturing", "Services"]),
                "plotStatus": random.choice(["Allocated", "Reserved"]),
                "activity": "Performance Testing",
                "investmentAmount": random.uniform(10000, 1000000),
                "employmentGenerated": random.randint(1, 100)
            }
        )
    
    @task(1)
    def create_user(self):
        """Test user creation (low frequency)."""
        headers = self.get_auth_headers("super_admin")
        
        self.client.post("/api/v1/users/create_user",
            headers=headers,
            json={
                "email": f"loadtest{random.randint(1, 10000)}@example.com",
                "role": random.choice(["zone_admin", "normal_user"]),
                "zone": random.choice(["GSEZ", "OSEZ", "GABON"])
            }
        )
    
    @task(1)
    def list_users(self):
        """Test listing users (low frequency)."""
        headers = self.get_auth_headers("super_admin")
        self.client.get("/api/v1/users/list_users", headers=headers)
    
    @task(2)
    def get_plot_details(self):
        """Test getting plot details."""
        headers = self.get_auth_headers("zone_admin")
        params = "?country=Gabon&zoneCode=GSEZ"
        self.client.get(f"/api/v1/plots/plot-details{params}", headers=headers)
    
    @task(1)
    def create_zone(self):
        """Test zone creation (low frequency)."""
        headers = self.get_auth_headers("super_admin")
        
        self.client.post("/api/v1/country/zones",
            headers=headers,
            json={
                "country": "Gabon",
                "zoneCode": f"PERF{random.randint(1, 1000)}",
                "phase": random.randint(1, 5),
                "landArea": random.uniform(10.0, 500.0),
                "zoneName": f"Performance Test Zone {random.randint(1, 100)}",
                "zoneType": random.choice(["SEZ", "Industrial", "Commercial"])
            }
        )
    
    @task(20)
    def health_check(self):
        """Test health check endpoint (very high frequency)."""
        self.client.get("/health")
    
    @task(5)
    def root_endpoint(self):
        """Test root endpoint."""
        self.client.get("/")


class AdminUser(HttpUser):
    """Simulated admin user with heavy operations."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight = fewer instances
    
    def on_start(self):
        """Get super admin token."""
        response = self.client.post("/api/v1/auth/token", json={
            "userId": "admin_load_test",
            "role": "super_admin",
            "zone": "GSEZ"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def admin_operations(self):
        """Perform admin-heavy operations."""
        # Create user
        self.client.post("/api/v1/users/create_user",
            headers=self.headers,
            json={
                "email": f"admin_test_{random.randint(1, 5000)}@example.com",
                "role": "zone_admin",
                "zone": "GSEZ"
            }
        )
        
        # List users
        self.client.get("/api/v1/users/list_users", headers=self.headers)
        
        # Update multiple plots
        for i in range(3):
            self.client.put("/api/v1/plots/update-plot",
                headers=self.headers,
                json={
                    "country": "Gabon",
                    "zoneCode": "GSEZ",
                    "phase": 1,
                    "plotName": f"ADMIN-{i}-{random.randint(1, 1000)}",
                    "plotStatus": "Allocated"
                }
            )


class ReadOnlyUser(HttpUser):
    """Simulated read-only user (normal_user role)."""
    
    wait_time = between(0.5, 2)
    weight = 5  # Higher weight = more instances
    
    def on_start(self):
        """Get normal user token."""
        response = self.client.post("/api/v1/auth/token", json={
            "userId": f"readonly_{random.randint(1, 1000)}",
            "role": "normal_user",
            "zone": "GABON"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def browse_plots(self):
        """Browse available plots."""
        self.client.get("/api/v1/plots/available", headers=self.headers)
    
    @task(5)
    def filtered_plot_search(self):
        """Search plots with filters."""
        filters = [
            "?country=Gabon",
            "?zoneCode=GSEZ",
            "?category=Residential",
            "?category=Commercial&phase=1",
            "?country=Gabon&zoneCode=OSEZ"
        ]
        
        filter_param = random.choice(filters)
        self.client.get(f"/api/v1/plots/available{filter_param}", headers=self.headers)
    
    @task(3)
    def get_plot_details(self):
        """Get detailed plot information."""
        params = "?country=Gabon&zoneCode=GSEZ"
        self.client.get(f"/api/v1/plots/plot-details{params}", headers=self.headers)
    
    @task(1)
    def try_forbidden_action(self):
        """Try to perform forbidden action (should get 403)."""
        # Normal user trying to create user (should fail)
        self.client.post("/api/v1/users/create_user",
            headers=self.headers,
            json={
                "email": "forbidden@example.com",
                "role": "normal_user",
                "zone": "GABON"
            }
        )


# Custom locust configuration
if __name__ == "__main__":
    print("""
    Performance Testing Instructions:
    
    1. Start your FastAPI server:
       uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    2. Install locust:
       pip install locust
    
    3. Run load tests:
       locust -f tests/test_performance.py --host=http://localhost:8000
    
    4. Open web UI:
       http://localhost:8089
    
    5. Recommended test parameters:
       - Users: 10-50 (start small)
       - Spawn rate: 1-5 users/second
       - Duration: 1-5 minutes
    
    Test Scenarios:
    - AriseAPIUser: Mixed operations (default weight=3)
    - AdminUser: Heavy admin operations (weight=1) 
    - ReadOnlyUser: Read-only browsing (weight=5)
    
    Metrics to Monitor:
    - Response times (P50, P95, P99)
    - Requests per second
    - Failure rate
    - Memory usage on server
    """)
