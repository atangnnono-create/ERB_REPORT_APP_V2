import requests
from typing import Dict, Any, Tuple, List

class APIClient:
    def __init__(self, base_url: str = "http://https://erb-backend.onrender.com"):
        self.base_url = base_url
        self.token: str | None = None
        self.session = requests.Session()

    def _handle_response(self, response: requests.Response) -> Tuple[bool, Any]:
        """Standardized response handler"""
        try:
            if response.status_code == 200:
                return True, response.json() if response.content else {"detail": "Success"}
            elif response.status_code == 401:
                return False, {"detail": "Unauthorized - please login again"}
            elif response.status_code == 404:
                return False, {"detail": "Resource not found"}
            else:
                return False, response.json() if response.content else {"detail": f"HTTP {response.status_code}"}
        except Exception as e:
            return False, {"detail": str(e)}

    # -------- Register --------
    def register(self, username: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = self.session.post(
                f"{self.base_url}/users/register",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    # -------- Login --------
    # -------- Login --------
    def login(self, username: str, password: str) -> bool:
        try:
            resp = self.session.post(
                f"{self.base_url}/auth/token",  # ✅ CHANGED from /users/login to /auth/token
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            if not token:
                print("Login failed: no token received")
                return False
            self.set_token(token)
            return True
        except requests.RequestException as e:
            print("Login failed:", e)
            return False

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    # ---------------- REPORTS ----------------
    def create_report(self, report_data: dict) -> Tuple[bool, Dict[str, Any]]:
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.post(f"{self.base_url}/reports/", json=report_data)
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def fetch_reports(self) -> Tuple[bool, List[Dict]]:
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.get(f"{self.base_url}/reports/")
            success, data = self._handle_response(resp)
            if success and isinstance(data, list):
                return True, data
            return success, data
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def delete_report(self, report_id: int) -> Tuple[bool, Dict[str, Any]]:
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.delete(f"{self.base_url}/reports/{report_id}")
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}
