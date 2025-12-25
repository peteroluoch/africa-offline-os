"""
Dashboard Button Functionality Test
Tests all interactive elements across the A-OS dashboard
"""
import requests
from typing import Dict, List

BASE_URL = "http://localhost:8000"

class DashboardTester:
    def __init__(self):
        self.session = requests.Session()
        self.results: List[Dict] = []
        
    def login(self):
        """Login to get authenticated session"""
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin", "password": "admin"},
            allow_redirects=False
        )
        return response.status_code in [200, 303]
    
    def test_endpoint(self, name: str, method: str, path: str, data: Dict = None):
        """Test a single endpoint"""
        try:
            if method == "GET":
                resp = self.session.get(f"{BASE_URL}{path}")
            elif method == "POST":
                resp = self.session.post(f"{BASE_URL}{path}", data=data or {})
            
            status = "✅ PASS" if resp.status_code in [200, 303, 307] else f"❌ FAIL ({resp.status_code})"
            self.results.append({
                "name": name,
                "method": method,
                "path": path,
                "status": status,
                "code": resp.status_code
            })
            print(f"{status} - {name} ({method} {path})")
            return resp.status_code in [200, 303, 307]
        except Exception as e:
            self.results.append({
                "name": name,
                "method": method,
                "path": path,
                "status": f"❌ ERROR",
                "code": str(e)
            })
            print(f"❌ ERROR - {name}: {e}")
            return False
    
    def run_tests(self):
        print("🔍 Testing Dashboard Button Functionality\n")
        
        # Login first
        print("1. Authentication")
        if not self.login():
            print("❌ Login failed - cannot proceed")
            return
        print("✅ Login successful\n")
        
        # Test navigation links
        print("2. Navigation Links")
        self.test_endpoint("Dashboard", "GET", "/dashboard")
        self.test_endpoint("Operators", "GET", "/operators")
        self.test_endpoint("Security", "GET", "/security")
        self.test_endpoint("Mesh Nodes", "GET", "/sys/mesh")
        self.test_endpoint("Agri-Lighthouse", "GET", "/agri/")
        self.test_endpoint("Transport-Mobile", "GET", "/transport/")
        self.test_endpoint("UI Gallery", "GET", "/sys/gallery")
        print()
        
        # Test Agri buttons
        print("3. Agri-Lighthouse Buttons")
        self.test_endpoint("Get Farmer Form", "GET", "/agri/farmer/new")
        self.test_endpoint("Register Farmer", "POST", "/agri/farmer", {
            "name": "Test Farmer",
            "location": "Test Location",
            "contact": "+254700000000"
        })
        print()
        
        # Test Mesh buttons
        print("4. Mesh Network Buttons")
        self.test_endpoint("Register Peer", "POST", "/sys/mesh/register", {
            "node_id": "test-node-01",
            "base_url": "http://192.168.1.50:8000",
            "public_key": "test_public_key_hex"
        })
        print()
        
        # Test Transport buttons
        print("5. Transport-Mobile Buttons")
        self.test_endpoint("Route Details", "GET", "/transport/route/r-46")
        self.test_endpoint("Update Vehicle Status", "POST", "/transport/vehicle/status", {
            "plate": "KCA123X",
            "status": "AVAILABLE",
            "route_id": "r-46"
        })
        print()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        passed = sum(1 for r in self.results if "PASS" in r["status"])
        total = len(self.results)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n✅ All dashboard buttons are functional!")
        else:
            print("\n⚠️  Some buttons need attention:")
            for r in self.results:
                if "FAIL" in r["status"] or "ERROR" in r["status"]:
                    print(f"  - {r['name']}: {r['status']}")

if __name__ == "__main__":
    tester = DashboardTester()
    tester.run_tests()
