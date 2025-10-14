import requests
from typing import Dict, Any, Tuple, List,Optional
from requests.adapters import HTTPAdapter
import asyncio
from urllib3 import Retry

class APIClient:
    def __init__(self, base_url: str= "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token: str | None = None
        self.session = requests.Session()
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=self.retry_strategy))

    async def request_with_timeout(self, method, endpoint, **kwargs):
        try:
            response = await asyncio.wait_for(
                self.session.request(method, f"{self.base_url}{endpoint}", **kwargs),
                timeout=30.0
            )
            return self._handle_response(response)
        except asyncio.TimeoutError:
            return False, {"detail": "Request timeout"}


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
                f"{self.base_url}/api/v1/auth/register",
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
                f"{self.base_url}/api/v1/auth/token",  # ✅ CHANGED from /auth/token to /users/login
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
        """Get current user's profile with better error handling"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/profile/me")
            if resp.status_code == 200:
                user_data = resp.json()
                # DEBUG: Log the user data we receive
                print(f"DEBUG: User data received: {user_data}")
                return True, user_data
            else:
                return False, {"detail": f"HTTP {resp.status_code}: {resp.text}"}
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def get_all_users(self) -> Tuple[bool, Any]:
        """Get all users (admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/admin/users")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})


    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role (admin only)"""
        if not self.token:
            return False
        try:
            resp = self.session.put(
                f"{self.base_url}/api/v1/admin/users/{user_id}",
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
                f"{self.base_url}/api/v1/admin/users/{user_id}",
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
                f"{self.base_url}/api/v1/admin/users/{user_id}",
                json={"is_active": True}
            )
            return resp.ok
        except requests.RequestException:
            return False

    def bulk_update_users(self, user_updates: List[dict]) -> Tuple[bool, Any]:
        """Bulk update multiple users (admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.post(f"{self.base_url}/api/v1/admin/users/bulk-update", json=user_updates)
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    # ---------------- REPORTS ----------------
    def create_report(self, report_data: dict) -> Tuple[bool, Dict[str, Any]]:
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.post(f"{self.base_url}/api/v1/reports/", json=report_data)
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def fetch_reports(self) -> Tuple[bool, List[Dict]]:
        if not self.token:
            return False, {"detail": "No token set. Please login first."}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/reports/")
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
            resp = self.session.delete(f"{self.base_url}/api/v1/reports/{report_id}")
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_all_reports(self) -> Tuple[bool, Any]:
        """Get all reports (admin/reviewer only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/admin/reports")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def update_profile(self, update_data: dict) -> Tuple[bool, Any]:
        """Update current user's profile"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.put(
                f"{self.base_url}/api/v1/profile/me",
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
            resp = self.session.put(f"{self.base_url}/api/v1/review/reports/{report_id}/submit")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def get_reports_for_review(self, status: str = "submitted") -> Tuple[bool, Any]:
        """Get reports pending review (reviewer/admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/review/reports?status={status}")
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

            resp = self.session.post(f"{self.base_url}/api/v1/review/reports/{report_id}", json=payload)
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_system_stats(self) -> Tuple[bool, Any]:
        """Get system statistics (admin only)"""
        if not self.token:
            return False, {"detail": "No token set"}
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/admin/system-stats")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    ############# EMAIL VERIFICATION #######################################

    def resend_verification_email(self, email: str) -> Tuple[bool, Any]:
        """Resend email verification"""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/v1/auth/resend-verification",
                params={"email": email}
            )
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}

    def get_verification_status(self, email: str) -> Tuple[bool, Any]:
        """Get verification status for a user"""
        try:
            resp = self.session.get(f"{self.base_url}/api/v1/auth/verification-status/{email}")
            return resp.ok, resp.json()
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_audit_logs(
            self,
            user_id: Optional[int] = None,
            username: Optional[str] = None,
            action: Optional[str] = None,
            resource_type: Optional[str] = None,
            resource_id: Optional[int] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            limit: int = 100,
            offset: int = 0
    ) -> Tuple[bool, Any]:
        """Get audit logs with filtering"""
        if not self.token:
            return False, {"detail": "No token set"}

        try:
            params = {
                "limit": limit,
                "offset": offset
            }
            if user_id: params["user_id"] = user_id
            if username: params["username"] = username
            if action: params["action"] = action
            if resource_type: params["resource_type"] = resource_type
            if resource_id: params["resource_id"] = resource_id
            if start_date: params["start_date"] = start_date
            if end_date: params["end_date"] = end_date

            resp = self.session.get(f"{self.base_url}/api/v1/audit/logs", params=params)
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_user_audit_logs(self, user_id: int, limit: int = 100, offset: int = 0) -> Tuple[bool, Any]:
        """Get audit logs for a specific user"""
        if not self.token:
            return False, {"detail": "No token set"}

        try:
            resp = self.session.get(
                f"{self.base_url}/api/v1/audit/logs/user/{user_id}",
                params={"limit": limit, "offset": offset}
            )
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_audit_stats(self, days: int = 30) -> Tuple[bool, Any]:
        """Get audit statistics"""
        if not self.token:
            return False, {"detail": "No token set"}

        try:
            resp = self.session.get(
                f"{self.base_url}/api/v1/audit/stats",
                params={"days": days}
            )
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def get_audit_actions(self) -> Tuple[bool, Any]:
        """Get available audit actions"""
        if not self.token:
            return False, {"detail": "No token set"}

        try:
            resp = self.session.get(f"{self.base_url}/api/v1/audit/actions")
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}


    def cleanup_audit_logs(self, days_to_keep: int = 365) -> Tuple[bool, Any]:
        """Clean up old audit logs"""
        if not self.token:
            return False, {"detail": "No token set"}

        try:
            resp = self.session.delete(
                f"{self.base_url}/api/v1/audit/cleanup",
                params={"days_to_keep": days_to_keep}
            )
            return self._handle_response(resp)
        except requests.RequestException as e:
            return False, {"detail": str(e)}