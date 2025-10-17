import streamlit as st
import requests
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def show():
    st.set_page_config(
        page_title="About - Engineering Report Deck",
        page_icon="ℹ️",
        layout="wide"
    )

    # Custom CSS for elegant styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f3a60;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #1f3a60, #4a6fa5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .section-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f3a60;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-2px);
    }
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        text-align: center;
        margin-bottom: 1rem;
    }
    .developer-card {
        background: linear-gradient(135deg, #1f3a60, #4a6fa5);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .divider {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #1f3a60, transparent);
        margin: 2rem 0;
    }
    .icon-large {
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown('<div class="main-header">🧮 About Engineering Report Deck</div>', unsafe_allow_html=True)

    # Hero Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        <div style='text-align: left; color: #555; line-height: 1.6;'>
            <h3 style='color: #1f3a60; margin-bottom: 1rem;'>Empowering Engineering Excellence</h3>
            <p style='font-size: 1.1rem;'>
                <strong>Engineering Report Deck</strong> is an intelligent reporting platform designed specifically for 
                engineers, engineering technologists, and engineering technicians to streamline their 
                <strong>ERB (Engineer Registration Board)</strong> reporting process.
            </p>
            <p style='font-size: 1.1rem;'>
                Our mission is to reduce administrative burden and empower engineering professionals 
                to focus on what they do best – engineering innovation and technical excellence.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1f3a60, #4a6fa5); color: white; padding: 2rem; border-radius: 15px; text-align: center;'>
            <h3 style='color: white; margin-bottom: 1rem;'>🚀 Why Choose Us?</h3>
            <p style='margin-bottom: 0.5rem;'>• 80% Faster Report Preparation</p>
            <p style='margin-bottom: 0.5rem;'>• ERB-Compliant Templates</p>
            <p style='margin-bottom: 0;'>• AI-Powered Writing Assistance</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Features Section
    st.markdown('<div class="sub-header">✨ Key Features & Capabilities</div>', unsafe_allow_html=True)

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">📑</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Structured Competency Documentation</h4>
            <p style='color: #666; margin: 0;'>
                Pre-built templates aligned with ERB requirements. Organize your engineering competencies systematically.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">💾</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Secure Data Management</h4>
            <p style='color: #666; margin: 0;'>
                Save progress locally with automatic backup. Your data remains secure and accessible.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">🤖</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>AI-Powered Writing Assistant</h4>
            <p style='color: #666; margin: 0;'>
                Enhance your technical writing with intelligent suggestions and quality improvements.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">📤</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Professional Export</h4>
            <p style='color: #666; margin: 0;'>
                Generate polished reports ready for ERB submission in multiple formats.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">🔄</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Progress Tracking</h4>
            <p style='color: #666; margin: 0;'>
                Monitor your report completion status with intuitive progress indicators.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <div class="icon-large">🔒</div>
            <h4 style='color: #1f3a60; margin-bottom: 0.5rem;'>Role-Based Access</h4>
            <p style='color: #666; margin: 0;'>
                Secure authentication with different access levels for engineers and reviewers.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Developer Section
    st.markdown('<div class="sub-header">👨‍💻 Meet the Developer</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("""
        <div class="developer-card">
            <div class="icon-large">⚡</div>
            <h3 style='color: white; margin-bottom: 0.5rem;'>Lefa Molokwe</h3>
            <p style='color: white; margin-bottom: 0.5rem; font-weight: 600;'>Pr.Eng 20180649</p>
            <p style='color: rgba(255,255,255,0.9); margin-bottom: 1rem;'>
                Electrical Engineer | Software Developer
            </p>
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;'>
                <p style='margin: 0.25rem 0; color: white;'>📱 Cell: +267 7144 1429</p>
                <p style='margin: 0.25rem 0; color: white;'>📧 WhatsApp: +267 7144 1429</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 15px; border-left: 4px solid #1f3a60;'>
            <h4 style='color: #1f3a60; margin-bottom: 1rem;'>About the Creator</h4>
            <p style='color: #666; line-height: 1.6; margin-bottom: 1rem;'>
                <strong>Lefa Molokwe</strong> is a registered Professional Electrical Engineer with a passion for 
                combining engineering practice with software innovation. With extensive experience in 
                both electrical engineering and software development, he identified the need for 
                streamlined engineering reporting tools in the industry.
            </p>
            <p style='color: #666; line-height: 1.6;'>
                This application represents the intersection of engineering expertise and modern 
                software development, designed specifically to address the challenges faced by 
                engineering professionals in their registration and continuous professional 
                development journeys.
            </p>
            <div style='margin-top: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 8px;'>
                <p style='margin: 0; color: #1f3a60; font-style: italic;'>
                    "Combining engineering excellence with digital innovation to empower the next generation of engineering professionals."
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # System Status Section
    st.markdown('<div class="sub-header">🔧 System Status & Connectivity</div>', unsafe_allow_html=True)

    # Check system status
    backend_available, internet_available, google_available = check_system_status()

    # Status Overview
    col1, col2, col3 = st.columns(3)

    with col1:
        status_color = "#27ae60" if backend_available else "#e74c3c"
        status_icon = "✅" if backend_available else "❌"
        st.markdown(f"""
        <div class="status-card">
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{status_icon}</div>
            <h4 style='color: {status_color}; margin-bottom: 0.5rem;'>Backend Services</h4>
            <p style='color: #666; margin: 0;'>API & Database Connectivity</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_color = "#27ae60" if internet_available else "#e74c3c"
        status_icon = "✅" if internet_available else "❌"
        st.markdown(f"""
        <div class="status-card">
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{status_icon}</div>
            <h4 style='color: {status_color}; margin-bottom: 0.5rem;'>Internet Connectivity</h4>
            <p style='color: #666; margin: 0;'>External Service Access</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        status_color = "#27ae60" if google_available else "#e74c3c"
        status_icon = "✅" if google_available else "❌"
        st.markdown(f"""
        <div class="status-card">
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{status_icon}</div>
            <h4 style='color: {status_color}; margin-bottom: 0.5rem;'>Google Services</h4>
            <p style='color: #666; margin: 0;'>Cloud Integration</p>
        </div>
        """, unsafe_allow_html=True)

    # Feature Availability Matrix
    st.markdown("""
    <div style='background: white; padding: 2rem; border-radius: 15px; margin-top: 1rem;'>
        <h4 style='color: #1f3a60; margin-bottom: 1rem;'>📊 Feature Availability</h4>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Core Features**")
        features = [
            ("Report Management", backend_available),
            ("User Authentication", backend_available),
            ("Data Storage", backend_available),
            ("Progress Tracking", backend_available)
        ]
        for feature, available in features:
            icon = "✅" if available else "⚠️"
            color = "#27ae60" if available else "#e67e22"
            st.markdown(f"<span style='color: {color};'>{icon}</span> {feature}", unsafe_allow_html=True)

    with col2:
        st.write("**Export Features**")
        features = [
            ("PDF Export", internet_available),
            ("Report Download", internet_available),
            ("Template Generation", True),
            ("Format Conversion", internet_available)
        ]
        for feature, available in features:
            icon = "✅" if available else "⚠️"
            color = "#27ae60" if available else "#e67e22"
            st.markdown(f"<span style='color: {color};'>{icon}</span> {feature}", unsafe_allow_html=True)

    with col3:
        st.write("**Advanced Features**")
        features = [
            ("Google Sheets Sync", google_available),
            ("Cloud Backup", google_available),
            ("AI Assistance", internet_available),
            ("Auto-save", True)
        ]
        for feature, available in features:
            icon = "✅" if available else "⚠️"
            color = "#27ae60" if available else "#e67e22"
            st.markdown(f"<span style='color: {color};'>{icon}</span> {feature}", unsafe_allow_html=True)

    # Technical Details (Collapsible)
    with st.expander("**🔍 Detailed Technical Information**", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Backend Connection**")
            backend_url = st.session_state.get(
                'backend_url',
                os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
            )
            st.code(f"Endpoint: {backend_url}")

            if backend_available:
                st.success("✅ Backend services are fully operational")
            else:
                st.error("❌ Backend connection failed")
                st.info("""
                **Troubleshooting Steps:**
                1. Ensure FastAPI backend is running
                2. Verify backend URL configuration
                3. Check firewall and network settings
                4. Run: `uvicorn backend.main:app --reload`
                """)

        with col2:
            st.write("**Network Services**")

            if internet_available:
                st.success("✅ Internet connectivity confirmed")
            else:
                st.error("❌ Internet connection unavailable")

            if google_available:
                st.success("✅ Google APIs accessible")
            else:
                st.warning("⚠️ Google services limited")

    # Footer
    st.markdown("""
    <div style='text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0;'>
            <strong>Engineering Report Deck</strong> • Built with ❤️ for the Engineering Community
        </p>
        <p style='color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
            Version 2.0 • Tsodilo Edition • Professional Engineering Reporting Solution
        </p>
    </div>
    """, unsafe_allow_html=True)


def check_system_status():
    """Check system connectivity status"""
    backend_available = False
    internet_available = False
    google_available = False

    # Check backend
    try:
        backend_url = st.session_state.get(
            'backend_url',
            os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
        )
        response = requests.get(f"{backend_url}/", timeout=3)
        backend_available = response.status_code == 200
    except:
        backend_available = False

    # Check internet
    try:
        response = requests.get("https://www.google.com", timeout=3)
        internet_available = True
    except:
        internet_available = False

    # Check Google services
    try:
        import socket
        socket.gethostbyname('oauth2.googleapis.com')
        google_available = True
    except:
        google_available = False

    return backend_available, internet_available, google_available


# Handle module execution
if __name__ == "__main__":
    show()