import requests
from typing import Dict, Any, Tuple, List

class APIClient:
    def __init__(self, base_url: str = "https://erb-backend.onrender.com"):
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
    def register(self, username: str, email: str, password: str, full_name: str = None) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = self.session.post(
                f"{self.base_url}/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": full_name
                },
                headers={"Content-Type": "application/json"}
            )
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    # -------- Login --------
    def login(self, username: str, password: str) -> bool:
        try:
            resp = self.session.post(
                f"{self.base_url}/auth/token",  # ✅ CHANGED from /auth/token to /users/login
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

    def get_current_user(self) -> Tuple[bool, Any]:
        """Get current user's profile"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/profile/me")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

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

    def get_all_users(self) -> Tuple[bool, Any]:
        """Get all users (admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/admin/users")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def get_all_reports(self) -> Tuple[bool, Any]:
        """Get all reports (admin/reviewer only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/admin/reports")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role (admin only)"""
        if not self.token:
            return False
        try:
            resp = self.session.put(
                f"{self.base_url}/admin/users/{user_id}",
                json={"role": new_role}
            )
            return resp.ok
        except requests.RequestException:
            return False

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user (admin only)"""
        if not self.token:
            return False
        try:
            resp = self.session.put(
                f"{self.base_url}/admin/users/{user_id}",
                json={"is_active": False}
            )
            return resp.ok
        except requests.RequestException:
            return False

    def activate_user(self, user_id: int) -> bool:
        """Activate user (admin only)"""
        if not self.token:
            return False
        try:
            resp = self.session.put(
                f"{self.base_url}/admin/users/{user_id}",
                json={"is_active": True}
            )
            return resp.ok
        except requests.RequestException:
            return False

    def update_profile(self, update_data: dict) -> Tuple[bool, Any]:
        """Update current user's profile"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.put(
                f"{self.base_url}/profile/me",
                json=update_data
            )
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def submit_report_for_review(self, report_id: int) -> Tuple[bool, Any]:
        """Submit a report for review"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.put(f"{self.base_url}/review/reports/{report_id}/submit")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def get_reports_for_review(self, status: str = "submitted") -> Tuple[bool, Any]:
        """Get reports pending review (reviewer/admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/review/reports?status={status}")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def review_report(self, report_id: int, status: str, review_notes: str = None) -> Tuple[bool, Any]:
        """Review a report (approve/reject)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            payload = {"status": status}
            if review_notes:
                payload["review_notes"] = review_notes

            resp = self.session.post(f"{self.base_url}/review/reports/{report_id}", json=payload)
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def resend_verification_email(self, email: str) -> Tuple[bool, Any]:
        """Resend email verification"""
        try:
            resp = self.session.post(
                f"{self.base_url}/auth/resend-verification",
                params={"email": email}
            )
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

def bulk_update_users(self, user_updates: List[dict]) -> Tuple[bool, Any]:
    """Bulk update multiple users (admin only)"""
    if not self.token:
        return False, {"detail": "No token set"}
    try:
        resp = self.session.post(f"{self.base_url}/admin/users/bulk-update", json=user_updates)
        return resp.ok, resp.json()
    except requests.RequestException as e:
        return False, {"detail": str(e)}

def get_system_stats(self) -> Tuple[bool, Any]:
    """Get system statistics (admin only)"""
    if not self.token:
        return False, {"detail": "No token set"}
    try:
        resp = self.session.get(f"{self.base_url}/admin/system-stats")
        return resp.ok, resp.json()
    except requests.RequestException as e:
        return False, {"detail": str(e)}

def resend_verification_email(self, email: str) -> Tuple[bool, Any]:
    """Resend email verification"""
    try:
        resp = self.session.post(
            f"{self.base_url}/auth/resend-verification",
            params={"email": email}
        )
        return resp.ok, resp.json()
    except requests.RequestException as e:
        return False, {"detail": str(e)}

def get_verification_status(self, email: str) -> Tuple[bool, Any]:
    """Get verification status for a user"""
    try:
        resp = self.session.get(f"{self.base_url}/auth/verification-status/{email}")
        return resp.ok, resp.json()
    except requests.RequestException as e:
        return False, {"detail": str(e)}
