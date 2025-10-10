import streamlit as st
from typing import Any, List, Dict, Callable


class MobileResponsive:
    """Mobile-responsive component utilities"""

    @staticmethod
    def init_responsive_css():
        """Initialize responsive CSS for mobile devices"""
        st.markdown("""
            <style>
            /* Mobile-first responsive design */
            @media (max-width: 768px) {
                /* Main container adjustments */
                .main .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                    padding-left: 0.5rem;
                    padding-right: 0.5rem;
                }

                /* Sidebar adjustments */
                .css-1d391kg {
                    padding: 1rem 0.5rem;
                }

                /* Text sizing for mobile */
                h1 {
                    font-size: 1.5rem !important;
                }
                h2 {
                    font-size: 1.3rem !important;
                }
                h3 {
                    font-size: 1.1rem !important;
                }

                /* Button sizing */
                .stButton button {
                    width: 100%;
                    margin: 0.25rem 0;
                    font-size: 0.9rem;
                    padding: 0.5rem 1rem;
                }

                /* Input fields */
                .stTextInput input, .stTextArea textarea {
                    font-size: 16px; /* Prevents zoom on iOS */
                }

                /* Dataframe responsiveness */
                .dataframe {
                    font-size: 0.8rem;
                }

                /* Column adjustments */
                .row-widget.stColumns {
                    gap: 0.5rem;
                }

                /* Hide non-essential elements on mobile */
                .mobile-hidden {
                    display: none;
                }

                /* Expandable containers */
                .mobile-expandable {
                    border: 1px solid #ddd;
                    border-radius: 0.5rem;
                    padding: 0.75rem;
                    margin: 0.5rem 0;
                }
            }

            /* Desktop enhancements */
            @media (min-width: 769px) {
                .mobile-only {
                    display: none;
                }
            }

            /* Touch-friendly elements */
            .touch-friendly {
                min-height: 44px;
                min-width: 44px;
                padding: 12px 16px;
            }

            /* Safe area for notched devices */
            .safe-area {
                padding-top: env(safe-area-inset-top);
                padding-bottom: env(safe-area-inset-bottom);
                padding-left: env(safe-area-inset-left);
                padding-right: env(safe-area-inset-right);
            }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def responsive_columns(sizes: List[int] = None, gap: str = "small"):
        """Create responsive columns that stack on mobile"""
        if sizes is None:
            sizes = [1, 1]

        # On mobile, use single column
        if MobileResponsive.is_mobile():
            return [st.container() for _ in sizes]
        else:
            return st.columns(sizes, gap=gap)

    @staticmethod
    def is_mobile() -> bool:
        """Check if the app is being viewed on a mobile device"""
        # This is a heuristic approach since Streamlit doesn't provide screen size
        try:
            # Check if we're in a mobile context (you might need to adjust this)
            user_agent = st.experimental_get_query_params().get('user_agent', [''])[0].lower()
            mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
            return any(keyword in user_agent for keyword in mobile_keywords)
        except:
            return False

    @staticmethod
    def mobile_navigation():
        """Mobile-optimized navigation"""
        if MobileResponsive.is_mobile():
            return st.selectbox(
                "Navigate to:",
                ["Dashboard", "Create Report", "My Reports", "Profile", "About", "Contact"],
                key="mobile_nav"
            )
        else:
            # Return regular sidebar navigation for desktop
            return None

    @staticmethod
    def touch_friendly_button(label: str, key: str, **kwargs):
        """Create a touch-friendly button"""
        return st.button(
            label,
            key=key,
            use_container_width=MobileResponsive.is_mobile(),
            **kwargs
        )

    @staticmethod
    def responsive_dataframe(data, **kwargs):
        """Display dataframe with mobile responsiveness"""
        if MobileResponsive.is_mobile():
            # For mobile, use a simpler display or pagination
            return st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
                **kwargs
            )
        else:
            return st.dataframe(data, **kwargs)

    @staticmethod
    def mobile_collapsible_section(title: str, content: Callable, expanded: bool = False):
        """Create a collapsible section for mobile"""
        if MobileResponsive.is_mobile():
            with st.expander(title, expanded=expanded):
                content()
        else:
            st.subheader(title)
            content()


class MobileForm:
    """Mobile-optimized form components"""

    @staticmethod
    def text_input(label: str, key: str, **kwargs):
        """Mobile-optimized text input"""
        return st.text_input(
            label,
            key=key,
            **kwargs
        )

    @staticmethod
    def text_area(label: str, key: str, height: int = 120, **kwargs):
        """Mobile-optimized text area"""
        if MobileResponsive.is_mobile():
            height = min(height, 150)  # Limit height on mobile
        return st.text_area(
            label,
            key=key,
            height=height,
            **kwargs
        )

    @staticmethod
    def selectbox(label: str, options: List, key: str, **kwargs):
        """Mobile-optimized selectbox"""
        return st.selectbox(
            label,
            options,
            key=key,
            **kwargs
        )

    @staticmethod
    def slider(label: str, min_value: int, max_value: int, value: int, key: str, **kwargs):
        """Mobile-optimized slider"""
        return st.slider(
            label,
            min_value=min_value,
            max_value=max_value,
            value=value,
            key=key,
            **kwargs
        )


class MobileLayout:
    """Mobile layout utilities"""

    @staticmethod
    def header(title: str, subtitle: str = None):
        """Mobile-optimized header"""
        st.markdown(f"""
            <div class="safe-area">
                <h1 style="margin-bottom: 0.5rem;">{title}</h1>
                {f'<p style="margin-top: 0; color: #666;">{subtitle}</p>' if subtitle else ''}
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def card(title: str, content: Any, border: bool = True):
        """Mobile-optimized card layout"""
        if border:
            st.container(border=True).write(f"**{title}**\n\n{content}")
        else:
            st.write(f"**{title}**\n\n{content}")

    @staticmethod
    def action_bar(actions: List[Dict]):
        """Mobile action bar with touch-friendly buttons"""
        cols = st.columns(len(actions))
        for i, action in enumerate(actions):
            with cols[i]:
                st.button(
                    action['label'],
                    key=action.get('key', f"action_{i}"),
                    use_container_width=True,
                    on_click=action.get('on_click'),
                    type=action.get('type', 'secondary')
                )


def init_mobile_app():
    """Initialize mobile-responsive app"""
    MobileResponsive.init_responsive_css()

    # Set page config for mobile
    st.set_page_config(
        layout="wide",
        initial_sidebar_state="collapsed" if MobileResponsive.is_mobile() else "expanded"
    )


# Example usage component
def mobile_report_card(report: Dict):
    """Mobile-optimized report card"""
    with st.container(border=True):
        col1, col2 = MobileResponsive.responsive_columns([2, 1])

        with col1:
            st.write(f"**{report['title']}**")
            st.write(f"Status: {report.get('status', 'draft').title()}")
            st.write(f"Created: {report.get('created_at', 'N/A')}")

        with col2:
            MobileResponsive.touch_friendly_button(
                "View",
                f"view_{report['id']}",
                type="primary"
            )

            if MobileResponsive.is_mobile():
                st.write("")  # Spacer
                MobileResponsive.touch_friendly_button(
                    "Delete",
                    f"delete_{report['id']}",
                    type="secondary"
                )


def mobile_competency_editor(competency: Dict, current_response: str, on_save: Callable):
    """Mobile-optimized competency editor"""
    with st.container(border=True):
        st.write(f"### {competency['title']}")
        st.info(competency['instructions'])

        response = MobileForm.text_area(
            "Your response:",
            key=f"editor_{competency['id']}",
            value=current_response,
            height=200
        )

        # Word count
        word_count = len(response.split())
        st.write(f"Words: {word_count}/{competency.get('word_limit', 500)}")

        # Action buttons
        col1, col2 = MobileResponsive.responsive_columns([1, 1])
        with col1:
            MobileResponsive.touch_friendly_button(
                "💾 Save",
                f"save_{competency['id']}",
                on_click=lambda: on_save(response),
                type="primary"
            )
        with col2:
            MobileResponsive.touch_friendly_button(
                "🤖 AI Review",
                f"ai_{competency['id']}",
                type="secondary"
            )