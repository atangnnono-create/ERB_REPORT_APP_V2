import requests
import time
import streamlit as st
from typing import Dict, Any, Tuple, List, Optional
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import jwt
import json


class EnhancedAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token: str | None = None
        self.refresh_token: str | None = None
        self.token_expiry: float = 0
        self.session = requests.Session()

        # Enhanced retry strategy
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        self.session.mount("http://", HTTPAdapter(max_retries=self.retry_strategy))
        self.session.mount("https://", HTTPAdapter(max_retries=self.retry_strategy))

        # Timeout configuration
        self.timeout = 30

    def _is_token_expired(self) -> bool:
        """Check if token is expired or about to expire (within 5 minutes)"""
        if not self.token:
            return True

        try:
            # Decode token without verification to check expiry
            payload = jwt.decode(self.token, options={"verify_signature": False})
            expiry = payload.get('exp', 0)
            # Consider token expired if within 5 minutes of expiry
            return time.time() >= (expiry - 300)
        except Exception:
            return True

    def _refresh_auth_token(self) -> bool:
        """Attempt to refresh the authentication token"""
        if not self.refresh_token:
            return False

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": self.refresh_token},
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.set_token(data.get('access_token'))
                self.refresh_token = data.get('refresh_token')
                return True
        except Exception as e:
            print(f"Token refresh failed: {e}")

        return False

    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid token, refresh if needed"""
        if self._is_token_expired():
            return self._refresh_auth_token()
        return True

    def _handle_response(self, response: requests.Response) -> Tuple[bool, Any]:
        """Enhanced response handler with better error handling"""

        try:
            if response.status_code == 200:
                data = response.json() if response.content else {"detail": "Success"}

                return True, data
            elif response.status_code == 204:  # ← FIXED: Handle 204 as SUCCESS
                print("🎯 DEBUG: HTTP 204 - No Content (successful deletion)")
                return True, {"detail": "Successfully deleted"}

            elif response.status_code == 401:
                # Token expired or invalid
                if self._refresh_auth_token():
                    # Retry the request with new token
                    return False, {"detail": "Please retry with new token"}
                return False, {"detail": "Authentication failed - please login again"}
            elif response.status_code == 403:
                return False, {"detail": "Permission denied"}
            elif response.status_code == 404:
                return False, {"detail": "Resource not found"}
            elif response.status_code == 429:
                return False, {"detail": "Rate limit exceeded - please wait"}
            elif 500 <= response.status_code < 600:
                return False, {"detail": f"Server error (HTTP {response.status_code})"}
            else:
                error_data = response.json() if response.content else {"detail": f"HTTP {response.status_code}"}
                ###########################################################
                print(f"DEBUG: Error data type: {type(error_data)}, data: {error_data}")
                # Extract error message from list if needed
                if isinstance(error_data, dict) and isinstance(error_data.get('detail'), list):
                    # Get the first error message from the list
                    errors = error_data['detail']
                    if errors:
                        error_msg = errors[0].get('msg', 'Validation error')
                    else:
                        error_msg = 'Validation error'
                #######################################################
                    return False,{"detail": error_msg}   #removed  error_data, during debug and added {"detail": error_msg}
                return False, error_data
        except json.JSONDecodeError:
            ##############################################
            print("DEBUG: JSON decode error")
            ###############################################
            return False, {"detail": "Invalid response from server"}
        except Exception as e:
            #################################################
            print(f"DEBUG: Exception in _handle_response: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            ###############################################
            return False, {"detail": f"Request failed: {str(e)}"}

    def _request_with_retry(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Any]:
        """Make request with automatic retry and token refresh"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # Ensure valid token before request (skip for auth endpoints)
                if endpoint not in ['/api/v1/auth/token', '/api/v1/auth/refresh', '/api/v1/auth/register']:
                    self._ensure_valid_token()

                # Set timeout if not provided
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.timeout

                response = self.session.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    **kwargs
                )

                success, data = self._handle_response(response)

                # If token expired and we can retry, refresh and try again
                if not success and isinstance(data, dict) and "token" in data.get('detail', '').lower() and attempt < max_retries:
                    if self._refresh_auth_token():
                        continue

                return success, data

            except requests.exceptions.Timeout:
                if attempt == max_retries:
                    return False, {"detail": "Request timeout - server took too long to respond"}
            except requests.exceptions.ConnectionError:
                if attempt == max_retries:
                    return False, {"detail": "Connection error - cannot reach server"}
            except Exception as e:
                if attempt == max_retries:
                    return False, {"detail": f"Request failed: {str(e)}"}

        return False, {"detail": "Max retries exceeded"}

    # -------- Authentication Methods --------
    def login(self, username: str, password: str) -> bool:
        """Enhanced login with token management"""
        try:
            success, data = self._request_with_retry(
                'POST',
                '/api/v1/auth/token',
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if success and data.get("access_token"):
                self.set_token(data["access_token"])
                self.refresh_token = data.get("refresh_token")
                return True

            print(f"Login failed: {data.get('detail', 'Unknown error')}")
            return False

        except Exception as e:
            print(f"Login exception: {e}")
            return False

    def set_token(self, token: str):
        """Set authentication token with expiry tracking"""
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

        # Track token expiry
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            self.token_expiry = payload.get('exp', 0)
        except Exception:
            self.token_expiry = time.time() + 3600  # Default 1 hour

    def logout(self):
        """Clear all authentication data"""
        self.token = None
        self.refresh_token = None
        self.token_expiry = 0
        self.session.headers.pop("Authorization", None)

    # -------- User Management --------
    def register(self, username: str, email: str, password: str, full_name: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Enhanced registration with validation"""
        # Basic client-side validation
        if len(password) < 8:
            return False, {"detail": "Password must be at least 8 characters long"}
        if '@' not in email:
            return False, {"detail": "Invalid email format"}

        return self._request_with_retry(
            'POST',
            '/api/v1/auth/register',
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )

    def get_current_user(self) -> Tuple[bool, Any]:
        """Get current user with enhanced error handling"""
        return self._request_with_retry('GET', '/api/v1/profile/me')

    def update_profile(self, update_data: dict) -> Tuple[bool, Any]:
        """Update profile with validation"""
        allowed_fields = ['email', 'full_name', 'phone', 'company']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        return self._request_with_retry(
            'PUT',
            '/api/v1/profile/me',
            json=filtered_data
        )

    # -------- Report Management --------
    def create_report(self, report_data: dict) -> Tuple[bool, Dict[str, Any]]:
        """Create report with validation"""
        required_fields = ['title', 'content']
        for field in required_fields:
            if not report_data.get(field):
                return False, {"detail": f"Missing required field: {field}"}

        return self._request_with_retry(
            'POST',
            '/api/v1/reports/',
            json=report_data
        )

    def get_report(self, report_id: int) -> Tuple[bool, Any]:
        """Get a specific report by ID"""
        return self._request_with_retry('GET', f'/api/v1/reports/{report_id}')

    def get_my_reports_paginated(self, skip: int = 0, limit: int = 50) -> Tuple[bool, Any]:
        """Get paginated user reports with total count"""
        success, data = self._request_with_retry(
            'GET',
            f'/api/v1/reports/paginated?skip={skip}&limit={limit}'
        )
        return success, data

    def fetch_reports(self) -> Tuple[bool, List[Dict]]:
        """Fetch reports with pagination support"""
        success, data = self._request_with_retry('GET', '/api/v1/reports/')
        if success and isinstance(data, list):
            return True, data
        return success, data

    def delete_report(self, report_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Delete report with confirmation"""
        print(f"🔍 API CLIENT: delete_report called for report {report_id}")
        result = self._request_with_retry('DELETE', f'/api/v1/reports/{report_id}')
        print(f"🔍 API CLIENT: delete_report result: {result}")
        return result

    def delete_report_as_admin(self, report_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Delete any report (admin only) - bypasses ownership checks"""
        print(f"🔍 API CLIENT: delete_report_as_admin called for report {report_id}")
        result = self._request_with_retry('DELETE', f'/api/v1/admin/reports/{report_id}')
        print(f"🔍 API CLIENT: delete_report_as_admin result: {result}")
        return result

    def get_all_reports_paginated(self, skip: int = 0, limit: int = 50) -> Tuple[bool, Any]:
        """Get paginated reports with total count"""
        success, data = self._request_with_retry('GET', f'/api/v1/admin/reports?skip={skip}&limit={limit}')

        if success and isinstance(data, dict) and 'reports' in data:
            return True, data
        return success, data


    def submit_report_for_review(self, report_data: dict) -> Tuple[bool, Any]:
        """Submit a report for review - now accepts full report data instead of report_id"""
        return self._request_with_retry('PUT', '/api/v1/review/reports/submit', json=report_data)

    def get_reports_for_review(self) -> Tuple[bool, Any]:
        """Get reports pending review (reviewer/admin only)"""
        return self._request_with_retry('GET', '/api/v1/review/reports')

    def review_report(self, report_id: int, status: str, review_notes: str = None) -> Tuple[bool, Any]:
        """Review a report (approve/reject)"""
        payload = {"status": status}
        if review_notes:
            payload["review_notes"] = review_notes

        return self._request_with_retry('POST', f'/api/v1/review/reports/{report_id}', json=payload)

    def progress_erb_stage(self, report_id: int, next_stage: str, notes: str = None, status: str = "in_progress") -> \
    Tuple[bool, Any]:
        """Progress report through ERB stages"""
        payload = {
            "next_stage": next_stage,
            "status": status
        }
        if notes:
            payload["notes"] = notes

        return self._request_with_retry('POST', f'/api/v1/review/reports/{report_id}/progress-stage', json=payload)

    # Add this method to your EnhancedAPIClient class in the "Report Management" section

    def assign_reviewer(self, report_id: int, reviewer_id: Optional[int]) -> Tuple[bool, Any]:
        """Assign or remove a reviewer from a report"""
        payload = {}
        if reviewer_id:
            payload["reviewer_id"] = reviewer_id
        else:
            payload["reviewer_id"] = None  # Explicitly remove reviewer

        return self._request_with_retry(
            'PUT',
            f'/api/v1/review/reports/{report_id}/assign',
            json=payload
        )

    def get_stage_history(self, report_id: int) -> Tuple[bool, Any]:
        """Get ERB stage history for a report"""
        return self._request_with_retry('GET', f'/api/v1/review/reports/{report_id}/stage-history')



    # -------- Admin Methods --------
    def get_all_users_paginated(self, skip: int = 0, limit: int = 50) -> Tuple[bool, Any]:
        """Get paginated users with total count"""
        success, data = self._request_with_retry('GET', f'/api/v1/admin/users?skip={skip}&limit={limit}')

        if success and isinstance(data, dict) and 'users' in data:
            return True, data
        return success, data


    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role with validation"""
        allowed_roles = ['admin', 'reviewer', 'engineer', 'technologist', 'technician', 'candidate']
        if new_role not in allowed_roles:
            return False

        success, _ = self._request_with_retry(
            'PUT',
            f'/api/v1/admin/users/{user_id}',
            json={"role": new_role}
        )
        return success

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user (admin only)"""
        success, _ = self._request_with_retry(
            'PUT',
            f'/api/v1/admin/users/{user_id}',
            json={"is_active": False}
        )
        return success

    def activate_user(self, user_id: int) -> bool:
        """Activate user (admin only)"""
        success, _ = self._request_with_retry(
            'PUT',
            f'/api/v1/admin/users/{user_id}',
            json={"is_active": True}
        )
        return success

    def bulk_update_users(self, user_updates: List[dict]) -> Tuple[bool, Any]:
        """Bulk update multiple users (admin only)"""
        return self._request_with_retry('POST', '/api/v1/admin/users/bulk-update', json=user_updates)

    def get_system_stats(self) -> Tuple[bool, Any]:
        """Get system statistics (admin only)"""
        return self._request_with_retry('GET', '/api/v1/admin/system-stats')

    # -------- Email Verification --------
    def resend_verification_email(self, email: str) -> Tuple[bool, Any]:
        """Resend email verification"""
        return self._request_with_retry(
            'POST',
            '/api/v1/auth/resend-verification',
            params={"email": email}
        )

    def get_verification_status(self, email: str) -> Tuple[bool, Any]:
        """Get verification status for a user"""
        return self._request_with_retry('GET', f'/api/v1/auth/verification-status/{email}')

    def verify_email(self, token: str) -> Tuple[bool, Any]:
        """Verify email using token"""
        return self._request_with_retry(
            'POST',
            '/api/v1/auth/verify-email',  # Remove ?token= from URL
            json={"token": token}  # Send token in JSON body
        )

    # -------- Audit Methods --------
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
        """Get audit logs with parameter validation"""
        params = {"limit": limit, "offset": offset}
        if user_id: params["user_id"] = user_id
        if username: params["username"] = username
        if action: params["action"] = action
        if resource_type: params["resource_type"] = resource_type
        if resource_id: params["resource_id"] = resource_id
        if start_date: params["start_date"] = start_date
        if end_date: params["end_date"] = end_date

        return self._request_with_retry('GET', '/api/v1/audit/logs', params=params)

    def get_user_audit_logs(self, user_id: int, limit: int = 100, offset: int = 0) -> Tuple[bool, Any]:
        """Get audit logs for a specific user"""
        return self._request_with_retry(
            'GET',
            f'/api/v1/audit/logs/user/{user_id}',
            params={"limit": limit, "offset": offset}
        )

    def get_audit_stats(self, days: int = 30) -> Tuple[bool, Any]:
        """Get audit statistics"""
        return self._request_with_retry('GET', '/api/v1/audit/stats', params={"days": days})

    def get_audit_actions(self) -> Tuple[bool, Any]:
        """Get available audit actions"""
        return self._request_with_retry('GET', '/api/v1/audit/actions')

    def cleanup_audit_logs(self, days_to_keep: int = 365) -> Tuple[bool, Any]:
        """Clean up old audit logs"""
        return self._request_with_retry(
            'DELETE',
            '/api/v1/audit/cleanup',
            params={"days_to_keep": days_to_keep}
        )

    def get_quick_stats(self) -> Tuple[bool, Any]:
        """Get lightweight quick stats"""
        return self._request_with_retry('GET', '/api/v1/admin/quick-stats')


    # Health check method
    def health_check(self) -> Tuple[bool, Any]:
        """Check if API is responsive"""
        return self._request_with_retry('GET', '/health')

    # Backward compatibility - async method (if needed)
    async def request_with_timeout(self, method, endpoint, **kwargs):
        """Async method for backward compatibility"""
        try:
            # Convert sync to async (basic implementation)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.request(method, f"{self.base_url}{endpoint}", **kwargs)
            )
            return self._handle_response(response)
        except asyncio.TimeoutError:
            return False, {"detail": "Request timeout"}
        except Exception as e:
            return False, {"detail": str(e)}

    # -------------- Password Reset Methods ---------------------------
    def forgot_password(self, email: str) -> Tuple[bool, Any]:
        """Request password reset"""
        ###############################################
        print(f"=== DEBUG forgot_password ===")
        print(f"Calling endpoint with email: {email}")
        #############################################
        result = self._request_with_retry(
        'POST',
        '/api/v1/auth/forgot-password',
        json={"email": email}
        )
        ###########################################
        print(f"DEBUG: forgot_password result: {result}")
        #########################################
        return result

    def reset_password(self, token: str, new_password: str) -> Tuple[bool, Any]:
        """Reset password with token"""
        print(f"=== DEBUG reset_password ===")
        print(f"Token: {token}")
        print(f"Password length: {len(new_password)}")

        result = self._request_with_retry(
            'POST',
            '/api/v1/auth/reset-password',
            json={"token": token, "new_password": new_password}
        )

        print(f"=== DEBUG reset_password result: {result} ===")
        return result

    def validate_reset_token(self, token: str) -> Tuple[bool, Any]:
        """Validate reset token"""
        return self._request_with_retry(
            'GET',
            f'/api/v1/auth/validate-reset-token?token={token}'
        )

##################### DATABASE STATISTICS##################################

 # -------- Database & System Statistics --------
    def get_database_stats(self) -> Tuple[bool, Any]:
        """Get comprehensive database statistics (admin only)"""
        return self._request_with_retry('GET', '/api/v1/admin/database/stats')

    def get_database_health(self) -> Tuple[bool, Any]:
        """Get database health and performance metrics"""
        return self._request_with_retry('GET', '/api/v1/admin/database/health')

    def get_system_metrics(self) -> Tuple[bool, Any]:
        """Get system performance metrics"""
        return self._request_with_retry('GET', '/api/v1/admin/system/metrics')

    def get_database_tables(self) -> Tuple[bool, Any]:
        """Get list of database tables with row counts"""
        return self._request_with_retry('GET', '/api/v1/admin/database/tables')

    def get_database_size(self) -> Tuple[bool, Any]:
        """Get database storage metrics"""
        return self._request_with_retry('GET', '/api/v1/admin/database/size')


# Global API client instance
api_client = EnhancedAPIClient()