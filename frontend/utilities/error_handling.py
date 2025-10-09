import streamlit as st
import time
from typing import Callable, Any
from functools import wraps


class ErrorHandler:
    @staticmethod
    def show_error(message: str, details: str = None):
        """Display standardized error message"""
        st.error(f"❌ {message}")
        if details and st.session_state.get('debug_mode', False):
            with st.expander("Technical Details"):
                st.code(details)

    @staticmethod
    def show_warning(message: str):
        """Display standardized warning"""
        st.warning(f"⚠️ {message}")

    @staticmethod
    def show_success(message: str):
        """Display standardized success message"""
        st.success(f"✅ {message}")

    @staticmethod
    def show_info(message: str):
        """Display standardized info message"""
        st.info(f"ℹ️ {message}")


def with_loading(spinner_text: str = "Processing..."):
    """Decorator to add loading spinner to any function"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(spinner_text):
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None

        return wrapper

    return decorator


def handle_api_errors(func: Callable) -> Callable:
    """Decorator to handle API errors gracefully"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.show_error(
                "An unexpected error occurred",
                f"Error type: {type(e).__name__}\nError message: {str(e)}"
            )
            return None

    return wrapper


class LoadingState:
    """Context manager for loading states"""

    def __init__(self, message: str = "Loading...", use_container: bool = True):
        self.message = message
        self.use_container = use_container
        self.placeholder = None

    def __enter__(self):
        if self.use_container:
            self.placeholder = st.empty()
            with self.placeholder.container():
                st.info(f"⏳ {self.message}")
        else:
            self.placeholder = st.info(f"⏳ {self.message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.placeholder:
            if self.use_container:
                self.placeholder.empty()
            else:
                self.placeholder.empty()


def display_network_status(api_client):
    """Display current network and API status"""
    col1, col2, col3 = st.columns(3)

    with col1:
        # Check internet connectivity
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            st.success("🌐 Internet: Connected")
        except:
            st.error("🌐 Internet: Disconnected")

    with col2:
        # Check API connectivity
        success, _ = api_client.health_check()
        if success:
            st.success("🔌 API: Connected")
        else:
            st.error("🔌 API: Disconnected")

    with col3:
        # Check token status
        if api_client.token:
            if api_client._is_token_expired():
                st.error("🔑 Token: Expired")
            else:
                st.success("🔑 Token: Valid")
        else:
            st.warning("🔑 Token: Missing")