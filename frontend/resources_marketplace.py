import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List
import json


def resources_marketplace():
    """Resources & Marketplace for ERD Products and Services"""

    st.set_page_config(
        page_title="Resources & Marketplace - ERD Platform",
        page_icon="🛍️",
        layout="wide"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .price-tag {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.1em;
    }
    .free-badge {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .coaching-badge {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .merch-badge {
        background: linear-gradient(135deg, #FFD93D 0%, #FF9A3D 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🎓 ERD Resources & Marketplace")
        st.markdown("""
        **Level up your engineering career** with premium resources, expert coaching, 
        and professional tools designed to help you succeed in the ERB process.
        """)

    with col2:
        st.metric("Happy Customers", "250+", "+42 this month")

    st.markdown("---")

    # Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎓 Learning Center",
        "📚 Premium Products",
        "🛍️ Merchandise",
        "👥 Workshops"
    ])

    # TAB 1: LEARNING CENTER (Free Resources)
    with tab1:
        st.header("🎓 Free Learning Center")
        st.markdown("Start your journey with these free resources")

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="free-badge">FREE</span>', unsafe_allow_html=True)
                st.subheader("📝 ERB Report Template Pack")
                st.markdown("""
                **Get started quickly** with our professional templates:
                - 5 customizable report templates
                - Best practice examples
                - Competency response guides
                """)
                if st.button("Download Template Pack", key="template_download", use_container_width=True):
                    st.success("✅ Download started! Check your email.")
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="free-badge">FREE</span>', unsafe_allow_html=True)
                st.subheader("🎥 Video Tutorial Series")
                st.markdown("""
                **Learn from experts:**
                - Writing winning competencies
                - Common mistakes to avoid
                - Review process explained
                - 5 video lessons (2+ hours)
                """)
                if st.button("Watch Videos", key="video_access", use_container_width=True):
                    st.success("✅ Video access granted! Check your email.")
                st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="free-badge">FREE</span>', unsafe_allow_html=True)
                st.subheader("📊 Success Stories & Case Studies")
                st.markdown("""
                **Learn from successful engineers:**
                - Real approved reports (anonymized)
                - Before/after improvements
                - Interview preparation guides
                """)
                if st.button("Access Stories", key="stories_access", use_container_width=True):
                    st.success("✅ Success stories unlocked! Check your email.")
                st.markdown('</div>', unsafe_allow_html=True)

        # Email List Signup
        st.markdown("---")
        st.subheader("🚀 Get Weekly ERD Tips & Updates")
        email = st.text_input("Enter your email for exclusive content:", placeholder="your.email@example.com")
        if st.button("Subscribe to Updates", type="primary"):
            if email:
                st.success("🎉 Welcome aboard! You'll receive our next ERD tips email.")
            else:
                st.warning("Please enter your email address.")

    # TAB 2: PREMIUM PRODUCTS
    with tab2:
        st.header("📚 Premium Educational Products")
        st.markdown("Invest in your success with our expert-curated resources")

        col1, col2 = st.columns(2)

        with col1:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<div class="price-tag">P450</div>', unsafe_allow_html=True)
                st.subheader("📖 The Complete Guide to Engineering Registration In Botswana")
                st.markdown("""
                **Your ultimate guide to ERB success:**

                ✨ **What's Included:**
                - 180+ page comprehensive guide
                - Step-by-step writing process
                - 50+ real examples (approved reports)
                - Common pitfalls and how to avoid them
                - Interview preparation section

                🎯 **Perfect For:**
                - First-time applicants
                - Engineers who want to maximize approval chances
                - Those struggling with competency responses

                💡 **Bonus:** Includes lifetime access to our AI report writing web app
                """)

                if st.button("Buy Now - P450", key="book_purchase", use_container_width=True, type="primary"):
                    st.session_state.current_product = "ERB Report Writing Guide"
                    st.session_state.product_price = 450
                    st.rerun()

                st.markdown("**✅ 30-day money-back guarantee**")
                st.markdown("**⭐ 4.9/5 from 150+ reviews**")
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<div class="price-tag">P400</div>', unsafe_allow_html=True)
                st.subheader("🎬 ERD Mastery Video Course")
                st.markdown("""
                **From beginner to expert - video-based learning:**

                ✨ **Course Modules:**
                - Module 1: ERB Process Fundamentals (4 hours)
                - Module 2: Writing Winning Competencies (6 hours) 
                - Module 3: Technical Depth & Evidence (5 hours)
                - Module 4: Review Process & Interview Prep (3 hours)
                - Module 5: Advanced Strategies (4 hours)

                🎯 **Includes:**
                - 22+ hours of video content
                - Downloadable workbooks
                - Community access
                - Certificate of completion

                💡 **Bonus:** 1-hour 1-on-1 consultation included
                """)

                if st.button("Enroll Now - P400", key="course_purchase", use_container_width=True, type="primary"):
                    st.session_state.current_product = "ERD Mastery Video Course"
                    st.session_state.product_price = 400
                    st.rerun()

                st.markdown("**✅ Lifetime access**")
                st.markdown("**⭐ 4.8/5 from 89+ reviews**")
                st.markdown('</div>', unsafe_allow_html=True)

    # TAB 3: MERCHANDISE
    with tab3:
        st.header("🛍️ ERD Branded Merchandise")
        st.markdown("Show your engineering pride with our professional merchandise")

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="merch-badge">P100</span>', unsafe_allow_html=True)
                st.subheader("☕ ERD Approved Mug")
                st.markdown("""
                **Start your day with engineering excellence:**
                - Premium ceramic mug
                - "ERD Approved" design
                - Dishwasher safe
                - 15oz capacity
                """)
                st.image("https://via.placeholder.com/200x150/667eea/ffffff?text=ERD+Mug", use_container_width=True)
                if st.button("Add to Cart - P100", key="mug_purchase", use_container_width=True):
                    st.success("✅ Mug added to cart!")
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="merch-badge">P400</span>', unsafe_allow_html=True)
                st.subheader("👕 Engineering Branded T-Shirts")
                st.markdown("""
                **Wear your achievement:**
                - Premium cotton t-shirt
                - "Assorted Engineering" designs
                - Multiple sizes available
                - Machine washable
                """)
                st.image("https://via.placehold.co/200x150/764ba2/ffffff?text=ERD+Shirt", use_container_width=True)
                if st.button("Add to Cart - P400", key="shirt_purchase", use_container_width=True):
                    st.success("✅ T-Shirt added to cart!")
                st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="merch-badge">P700</span>', unsafe_allow_html=True)
                st.subheader("💼 Professional Engineer Toolkit")
                st.markdown("""
                **Your daily engineering companion:**
                - Leather notebook cover
                - ERD-approved pen set
                - Engineering reference cards
                - Certificate frame
                """)
                st.image("https://via.placeholder.com/200x150/FFD93D/000000?text=Toolkit", use_container_width=True)
                if st.button("Add to Cart - P700", key="toolkit_purchase", use_container_width=True):
                    st.success("✅ Toolkit added to cart!")
                st.markdown('</div>', unsafe_allow_html=True)

    # TAB 4: COACHING SERVICES
    with tab4:
        st.header("👥 Report Writing Workshops and Coaching Services")
        st.markdown("Get personalized guidance from ERB experts")

        col1, col2 = st.columns(2)

        with col1:
           # with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="coaching-badge">P600</span>', unsafe_allow_html=True)
                st.subheader("🚀 ERB Strategy Session")
                st.markdown("""
                **Personalized 1-on-1 guidance:**

                ✨ **Session Includes:**
                - Complete report review & feedback(if report exists)
                - 120-minute virtual/physical consultation
                - Personalized startup/improvement plan
                - Follow-up action items
                - Final review before submission to ERB

                🎯 **Perfect For:**
                - First-time applicants wanting guaranteed success
                - Stuck on specific competencies
                - Need strategic direction
                - Overcoming previous rejections
                - Preparing for Professional interview

                💡 **Results:** Most clients see immediate improvement in their reports
                """)

                # Coaching Inquiry Form
                with st.expander("📅 Book Your Session"):
                    st.write("**Schedule your strategy session:**")
                    name = st.text_input("Your Name", key="strategy_name")
                    email = st.text_input("Your Email", key="strategy_email")
                    current_challenge = st.text_area("What's your biggest challenge?")
                    preferred_date = st.date_input("Preferred Session Date")

                    if st.button("Request Strategy Session", key="strategy_request", use_container_width=True):
                        if name and email:
                            st.success("🎉 Session request received! We'll contact you within 24 hours to schedule.")
                        else:
                            st.warning("Please fill in your name and email.")

                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown('<div class="product-card">', unsafe_allow_html=True)
                st.markdown('<span class="coaching-badge">P400</span>', unsafe_allow_html=True)
                st.subheader("🎯 Report Writing Workshops")
                st.markdown("""
                **End-to-end support for ERB success:**

                ✨ **Workshop Package Includes:**
                - Module 1: ERB Process Fundamentals (1 hour)
                - Module 2: Writing Winning Competencies (2 hours) 
                - Module 3: Technical Depth & Evidence (2 hour)
                - Module 4: ERB Review Process & Interview Prep (1 hour)
                - Module 5: Engineering Report Deck Application (1 hour)

                🎯 **Perfect For:**
                - First-time applicants wanting guaranteed success
                - Understanding ERB Professional Report writing process 
                - Overcoming previous rejections
                - Understanding ERB Assessors Expectations
                - Learning how to use Engineering Report Deck Application

                💡 **Bonus:** Includes all premium templates and guides
                """)

                # Package Inquiry Form
                with st.expander("📅 Inquire About Package"):
                    st.write("**Learn more about our comprehensive package:**")
                    name = st.text_input("Your Name", key="package_name")
                    email = st.text_input("Your Email", key="package_email")
                    experience_level = st.selectbox("Your Experience Level",
                                                    ["First-time applicant", "Previously rejected",
                                                     "Seeking advancement"])
                    timeline = st.selectbox("Your Timeline",
                                            ["1-2 months", "3-4 months", "6+ months", "Urgent (2-4 weeks)"])

                    if st.button("Request Package Details", key="package_request", use_container_width=True):
                        if name and email:
                            st.success("📬 Package details sent! Check your email for comprehensive information.")
                        else:
                            st.warning("Please fill in your name and email.")

                st.markdown('</div>', unsafe_allow_html=True)

    # Checkout Section (if product selected)
    if hasattr(st.session_state, 'current_product'):
        st.markdown("---")
        st.header("🛒 Checkout")

        with st.container():
            st.success(f"**Ready to purchase:** {st.session_state.current_product}")
            st.info(f"**Total:** ${st.session_state.product_price}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Billing Information")
                name = st.text_input("Full Name")
                email = st.text_input("Email Address")
                address = st.text_area("Billing Address")

            with col2:
                st.subheader("Payment Details")
                card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                col_exp, col_cvv = st.columns(2)
                with col_exp:
                    exp_date = st.text_input("Expiry Date", placeholder="MM/YY")
                with col_cvv:
                    cvv = st.text_input("CVV", placeholder="123")

            if st.button("Complete Purchase", type="primary", use_container_width=True):
                if name and email and card_number:
                    st.balloons()
                    st.success(f"🎉 Purchase Complete! {st.session_state.current_product} is now yours!")
                    st.info("📧 Check your email for access instructions and receipt.")

                    # Clear the session state
                    del st.session_state.current_product
                    del st.session_state.product_price
                    st.rerun()
                else:
                    st.warning("Please fill in all required fields.")

    # Footer Section
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**💼 Business Info**")
        st.markdown("""
        ERD Resources & Marketplace  
        Supporting Engineers Since 2024  
        Email: customengineeringreports.com
        """)

    with col2:
        st.markdown("**🔒 Trust & Security**")
        st.markdown("""
        ✓ 30-day money-back guarantee  
        ✓ Secure payment processing  
        ✓ Privacy protected  
        ✓ SSL encrypted
        """)

    with col3:
        st.markdown("**📞 Support**")
        st.markdown("""
        Need help choosing?  
        📧 Email our advisors  
        🕒 24h response time  
        💬 Live chat available
        """)

        # Footer
    st.markdown("""
          <div style='text-align: center; margin-top: 3rem; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
              <p style='color: #666; margin: 0;'>
                  <strong>Engineering Report Deck</strong> • Confidence with Clarity
              </p>
              <p style='color: #888; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
                  TurtleTEC Solutions Africa
                  © 2025. ALL RIGHTS RESERVED.
              </p>
          </div>
          """, unsafe_allow_html=True)


def main():
    # Check if user is logged in (optional - remove if you want public access)
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("🔒 Please login to access the resources marketplace")
        return

    resources_marketplace()


if __name__ == "__main__":
    main()