import streamlit as st
import requests
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def show():
    st.set_page_config(page_title="About - Engineering Report Deck")

    # Display connection status
    try:
        # Try to connect to backend to check status
        backend_url = st.session_state.get(
            'backend_url',
            os.getenv('BACKEND_URL', 'https://erb-backend.onrender.com')
        )

        # Simple health check
        response = requests.get(f"{backend_url}/", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ Backend connected")
        else:
            st.sidebar.warning("⚠️ Backend connection issue")

    except requests.exceptions.ConnectionError:
        st.sidebar.error("🔌 Backend connection failed")
        st.sidebar.info("Please ensure the backend server is running on port 8000")

    except requests.exceptions.Timeout:
        st.sidebar.warning("⏰ Backend connection timeout")

    except Exception as e:
        st.sidebar.warning(f"⚠️ Connection status unknown: {str(e)}")

    st.subheader("ℹ️ About Engineering Report Deck")
    st.write(
        """
        **Engineering Report Deck** is an intelligent reporting assistant designed to help 
        engineers, engineering technologists and engineering technicians efficiently prepare 
        their **ERB (Engineer Registration Board) reports**. It provides a structured workspace where engineers can build, edit, and organize 
        their competencies with ease.  

        ### ✨ Key Features
        - 📑 Streamlined competency documentation  
        - 🤖 AI-powered suggestions to refine your writing  
        - 💾 Save & load progress locally  
        - 📤 Export reports for submission  

        This tool aims to **reduce the stress of report writing** and empower engineers 
        to focus on their technical achievements while ensuring alignment with ERB requirements.
        """
    )

    st.markdown("---")
    st.subheader("👨‍💻 The Application Developer")
    st.write(
        """
        **Lefa Molokwe Pr.Eng 20180649**  
        Electrical Engineer | Software Developer 

        Software & Embedded Systems Developer. Passionate about combining engineering practice with software innovation 
        to solve real-world problems.

        **Contacts** Cell: 71441429 | 𝑾𝒉𝒂𝒕𝒔𝑨pp 71441429
        """
    )

    # Network status section (collapsible)
    with st.expander("🔧 Network & Service Status"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Backend Connection:**")
            backend_url = st.session_state.get(
                'backend_url',
                os.getenv('BACKEND_URL', 'http://https://erb-backend.onrender.com')
            )
            st.code(f"Backend URL: {backend_url}")

            try:
                response = requests.get(f"{backend_url}/", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Backend is running and responsive")
                else:
                    st.warning(f"⚠️ Backend status: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend server")
                st.info("""
                **Troubleshooting:**
                1. Ensure FastAPI backend is running
                2. Check backend URL configuration
                3. Verify no firewall blocking
                4. Run: `uvicorn backend.main:app --reload`
                """)

            except requests.exceptions.Timeout:
                st.warning("⏰ Backend connection timed out")

            except Exception as e:
                st.error(f"💥 Backend error: {str(e)}")

        with col2:
            st.write("**Internet & External Services:**")

            # Test internet connectivity
            try:
                internet_test = requests.get("https://www.google.com", timeout=5)
                st.success("✅ Internet connection active")
            except Exception:
                st.error("❌ No internet connection")
                st.info("""
                **Network Issues Detected:**
                - Check your internet connection
                - Verify network settings
                - Contact your network administrator
                - Google services may be unavailable
                """)

            # Test DNS resolution (common cause of the Google API error)
            try:
                import socket
                socket.gethostbyname('oauth2.googleapis.com')
                st.success("✅ DNS resolution working")
            except socket.gaierror:
                st.error("❌ DNS resolution failed")
                st.info("""
                **DNS Issues:**
                - Cannot resolve Google API endpoints
                - Check DNS settings
                - Try different network
                - Google Sheets features will be unavailable
                """)

            # Test Google APIs availability
            try:
                google_test = requests.get("https://www.googleapis.com", timeout=5)
                st.success("✅ Google APIs reachable")
            except Exception as e:
                st.warning("⚠️ Google APIs may be unavailable")
                st.info(f"Google services error: {str(e)}")

    # Feature status based on network conditions
    st.markdown("---")
    st.subheader("📊 Current Feature Status")

    # Check what features are available
    backend_available = False
    internet_available = False
    google_available = False

    try:
        backend_response = requests.get(
            st.session_state.get('backend_url', 'http://https://erb-backend.onrender.com') + "/",
            timeout=3
        )
        backend_available = backend_response.status_code == 200
    except:
        backend_available = False

    try:
        internet_response = requests.get("https://www.google.com", timeout=3)
        internet_available = True
    except:
        internet_available = False

    try:
        import socket
        socket.gethostbyname('oauth2.googleapis.com')
        google_available = True
    except:
        google_available = False

    # Display feature matrix
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Core Features**")
        if backend_available:
            st.success("✅ Report Management")
            st.success("✅ User Authentication")
            st.success("✅ Data Storage")
        else:
            st.warning("⚠️ Report Management")
            st.warning("⚠️ User Authentication")
            st.warning("⚠️ Data Storage")
            st.info("Backend required")

    with col2:
        st.write("**Export Features**")
        if internet_available:
            st.success("✅ PDF Export")
            st.success("✅ Report Download")
        else:
            st.warning("⚠️ PDF Export")
            st.warning("⚠️ Report Download")
            st.info("Internet required")

    with col3:
        st.write("**Advanced Features**")
        if google_available and internet_available:
            st.success("✅ Google Sheets Sync")
            st.success("✅ Cloud Backup")
        else:
            st.warning("⚠️ Google Sheets Sync")
            st.warning("⚠️ Cloud Backup")
            st.info("Google services required")


# Handle module execution
if __name__ == "__main__":
    show()
