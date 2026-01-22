"""
Early-Look Bookbuilding MVP
Main Application Entry Point

A lightweight, non-binding bookbuilding tool for small/medium issuers
to discover institutional investor demand and indicative pricing.
"""

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, get_session
from ui.auth_pages import (
    init_session_state, render_login_page, render_sidebar_user_info, logout
)
from ui.issuer_dashboard import render_issuer_dashboard
from ui.investor_portal import render_investor_portal
from ui.components import apply_dark_theme

# Page configuration
st.set_page_config(
    page_title="Early-Look Bookbuilding",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
@st.cache_resource
def initialize_database():
    """Initialize database (runs once)"""
    init_db()
    return True

# Initialize
initialize_database()
init_session_state()


def main():
    """Main application router"""
    
    # Apply dark theme
    apply_dark_theme()
    
    # Check authentication
    if not st.session_state.authenticated:
        render_login_page()
        return
    
    # Render sidebar user info
    render_sidebar_user_info()
    
    # Route based on user role
    user = st.session_state.user
    
    if user['role'] == 'issuer':
        render_issuer_dashboard()
    elif user['role'] == 'investor':
        render_investor_portal()
    else:
        st.error("Unknown user role")
        if st.button("Logout"):
            logout()


if __name__ == "__main__":
    main()
