import requests
from typing import Dict, Any, Tuple

class APIClient:
    def __init__(self, base_url: str = "https://erb-backend.onrender.com"):
        self.base_url = base_url
        self.token: str | None = None
        self.session = requests.Session()

    # -------- Register --------
    def register(self, username: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = self.session.post(
                f"{self.base_url}/users/register",
                json={"username": username, "password": password},  # JSON is correct here
                headers={"Content-Type": "application/json"}
            )
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    # -------- Login --------
    def login(self, username: str, password: str) -> bool:
        try:
            resp = self.session.post(
                f"{self.base_url}/auth/token",
                data={"username": username, "password": password},  # must be form-encoded
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
        """Submit a report to backend using stored token."""
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.post(f"{self.base_url}/reports/", json=report_data)
            if resp.status_code == 401:
                return False, {"detail": "Unauthorized. Token may be invalid or expired."}
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def fetch_reports(self) -> Tuple[bool, Any]:
        """Get all reports for the logged-in user."""
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.get(f"{self.base_url}/reports/")
            if resp.status_code == 401:
                return False, {"detail": "Unauthorized. Token may be invalid or expired."}
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def delete_report(self, report_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Delete a report by ID."""
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.delete(f"{self.base_url}/reports/{report_id}")
            if resp.status_code == 401:
                return False, {"detail": "Unauthorized. Token may be invalid or expired."}
            return resp.ok, resp.json() if resp.content else {"detail": "Deleted"}
        except requests.RequestException as e:
            return False, {"detail": str(e)}