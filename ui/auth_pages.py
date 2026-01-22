"""
Authentication UI Pages
Login, Registration, and Invitation handling
"""

import streamlit as st
from typing import Optional

from db import get_session
from auth import (
    authenticate_user, register_issuer, register_investor_from_invitation,
    validate_invitation_token
)
from models import User, UserRole
from ui.components import apply_dark_theme, show_error, show_success, show_warning


def init_session_state():
    """Initialize session state variables"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_deal_id' not in st.session_state:
        st.session_state.current_deal_id = None


def logout():
    """Log out the current user"""
    st.session_state.user = None
    st.session_state.authenticated = False
    st.session_state.current_deal_id = None
    st.rerun()


def render_login_page():
    """Render the login page"""
    apply_dark_theme()
    
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="color: #a78bfa;">📊 Early-Look Bookbuilding</h1>
        <p style="color: #9ca3af; font-size: 16px;">
            Discover demand and price for your capital raise
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for invitation token in URL
    query_params = st.query_params
    invite_token = query_params.get("invite")
    
    if invite_token:
        render_invitation_page(invite_token)
        return
    
    # Tab selection
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register as Issuer"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_issuer_registration_form()


def render_login_form():
    """Render login form"""
    st.markdown("### Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        
        if submitted:
            if not email or not password:
                show_error("Please enter both email and password")
            else:
                db = get_session()
                try:
                    success, message, user = authenticate_user(db, email, password)
                    if success:
                        st.session_state.user = {
                            'id': user.id,
                            'email': user.email,
                            'role': user.role.value,
                            'display_name': user.display_name
                        }
                        st.session_state.authenticated = True
                        show_success("Login successful!")
                        st.rerun()
                    else:
                        show_error(message)
                finally:
                    db.close()


def render_issuer_registration_form():
    """Render issuer registration form"""
    st.markdown("### Register as Issuer")
    st.markdown("*Create an account to start your capital raise journey*")
    
    with st.form("register_form"):
        org_name = st.text_input("Organization Name", placeholder="Your Company Ltd")
        display_name = st.text_input("Your Name", placeholder="John Smith")
        email = st.text_input("Email", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Min 8 characters")
        password_confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
        
        submitted = st.form_submit_button("Create Issuer Account", use_container_width=True)
        
        if submitted:
            if not all([org_name, email, password, password_confirm]):
                show_error("Please fill in all required fields")
            elif password != password_confirm:
                show_error("Passwords do not match")
            elif len(password) < 8:
                show_error("Password must be at least 8 characters")
            else:
                db = get_session()
                try:
                    success, message, user = register_issuer(
                        db, email, password, org_name, display_name
                    )
                    if success:
                        show_success("Registration successful! Please log in.")
                    else:
                        show_error(message)
                finally:
                    db.close()


def render_invitation_page(token: str):
    """Render invitation acceptance page"""
    st.markdown("### 📧 You've Been Invited!")
    
    db = get_session()
    try:
        valid, message, invitation = validate_invitation_token(db, token)
        
        if not valid:
            show_error(message)
            st.markdown("---")
            st.markdown("If you already have an account, please [log in](/)")
            return
        
        # Show invitation details
        st.markdown(f"""
        <div class="metric-card">
            <p style="color: #9ca3af;">You've been invited to participate in:</p>
            <h3 style="color: white;">{invitation.deal.name}</h3>
            <p style="color: #6b7280;">by {invitation.deal.issuer.org_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Create Your Investor Account")
        
        with st.form("investor_register_form"):
            st.text_input("Email", value=invitation.investor_email, disabled=True)
            display_name = st.text_input(
                "Your Display Name",
                value=invitation.investor_name or "",
                placeholder="How you'll appear to the issuer"
            )
            password = st.text_input("Create Password", type="password", placeholder="Min 8 characters")
            password_confirm = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Create Account & Join Deal", use_container_width=True)
            
            if submitted:
                if not password or not password_confirm:
                    show_error("Please enter a password")
                elif password != password_confirm:
                    show_error("Passwords do not match")
                elif len(password) < 8:
                    show_error("Password must be at least 8 characters")
                else:
                    success, message, user = register_investor_from_invitation(
                        db, token, password, display_name
                    )
                    if success:
                        show_success("Account created! Logging you in...")
                        st.session_state.user = {
                            'id': user.id,
                            'email': user.email,
                            'role': user.role.value,
                            'display_name': user.display_name
                        }
                        st.session_state.authenticated = True
                        st.session_state.current_deal_id = invitation.deal_id
                        # Clear the invite param
                        st.query_params.clear()
                        st.rerun()
                    else:
                        show_error(message)
    finally:
        db.close()


def render_sidebar_user_info():
    """Render user info in sidebar"""
    if st.session_state.authenticated and st.session_state.user:
        user = st.session_state.user
        
        st.sidebar.markdown(f"""
        <div style="padding: 10px; background: #1a1a2e; border-radius: 8px; margin-bottom: 20px;">
            <div style="color: #9ca3af; font-size: 12px;">Signed in as</div>
            <div style="color: white; font-weight: bold;">{user['display_name']}</div>
            <div style="color: #6b7280; font-size: 12px;">{user['email']}</div>
            <div style="color: #a78bfa; font-size: 11px; margin-top: 5px;">
                {user['role'].upper()}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
