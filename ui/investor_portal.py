"""
Investor Portal UI
Interface for investors to view deals and submit IOIs
"""

import streamlit as st
from datetime import datetime
from typing import Optional

from db import get_session
from models import (
    Deal, Band, IOI, Invitation, User, DealStatus, DealType,
    InvestorType, IOIStrength, InvitationStatus
)
from services.deal_service import DealService
from auth import get_user_deals, can_access_deal
from ui.components import (
    apply_dark_theme, show_disclaimer, format_currency,
    get_coverage_class, show_error, show_success, show_warning, show_info
)


def render_investor_portal():
    """Main investor portal"""
    apply_dark_theme()
    
    user = st.session_state.user
    
    # Sidebar
    st.sidebar.markdown("### 💼 Investor Portal")
    
    # Check if viewing a specific deal
    if st.session_state.get('current_deal_id'):
        if st.sidebar.button("← Back to My Deals", use_container_width=True):
            st.session_state.current_deal_id = None
            st.rerun()
    
    # Navigation
    if st.session_state.get('current_deal_id'):
        render_deal_view(st.session_state.current_deal_id)
    else:
        render_investor_deals_list()


def render_investor_deals_list():
    """Render list of deals investor has access to"""
    st.markdown("## 💼 My Investment Opportunities")
    
    db = get_session()
    try:
        user_id = st.session_state.user['id']
        
        # Get deals through accepted invitations
        invitations = db.query(Invitation).filter(
            Invitation.accepted_user_id == user_id,
            Invitation.status == InvitationStatus.ACCEPTED
        ).all()
        
        if not invitations:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px; background: #1a1a2e; border-radius: 12px; margin: 20px 0;">
                <h3 style="color: #9ca3af;">No deal invitations yet</h3>
                <p style="color: #6b7280;">You'll see deals here once an issuer invites you to participate.</p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        for inv in invitations:
            deal = db.query(Deal).filter(Deal.id == inv.deal_id).first()
            if not deal:
                continue
            
            # Get user's IOIs for this deal
            user_iois = db.query(IOI).filter(
                IOI.deal_id == deal.id,
                IOI.investor_user_id == user_id,
                IOI.is_active == True
            ).all()
            
            total_committed = sum(ioi.amount for ioi in user_iois)
            
            status_color = {
                DealStatus.DRAFT: "#6b7280",
                DealStatus.OPEN: "#22c55e", 
                DealStatus.CLOSED: "#ef4444"
            }.get(deal.status, "#6b7280")
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 12px; padding: 20px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="margin: 0; color: white;">{deal.name}</h3>
                            <p style="color: #9ca3af; margin: 5px 0;">
                                {deal.deal_type.value.capitalize()} • {deal.currency} {deal.target_amount:,.0f} target
                            </p>
                            <p style="color: #6b7280; font-size: 12px;">
                                by {deal.issuer.org_name}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <span style="color: {status_color}; font-weight: bold; font-size: 12px; 
                                         background: {status_color}22; padding: 4px 12px; border-radius: 20px;">
                                {deal.status.value.upper()}
                            </span>
                            <br><br>
                            <span style="color: #a78bfa; font-size: 14px;">
                                Your IOIs: {deal.currency} {total_committed:,.0f}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                btn_text = "📝 View & Submit IOI" if deal.status == DealStatus.OPEN else "👁️ View Deal"
                if st.button(btn_text, key=f"view_{deal.id}", use_container_width=True):
                    st.session_state.current_deal_id = deal.id
                    st.rerun()
    
    finally:
        db.close()


def render_deal_view(deal_id: int):
    """Render deal view for investor"""
    db = get_session()
    try:
        user_id = st.session_state.user['id']
        
        # Verify access
        if not can_access_deal(db, db.query(User).filter(User.id == user_id).first(), deal_id):
            show_error("You don't have access to this deal.")
            return
        
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            show_error("Deal not found.")
            return
        
        deal_service = DealService(db)
        bands = deal_service.get_deal_bands(deal_id)
        
        # Header
        status_color = {
            DealStatus.DRAFT: "#6b7280",
            DealStatus.OPEN: "#22c55e", 
            DealStatus.CLOSED: "#ef4444"
        }.get(deal.status, "#6b7280")
        
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h1 style="color: #a78bfa; margin: 0;">{deal.name}</h1>
                    <p style="color: #9ca3af;">by {deal.issuer.org_name}</p>
                </div>
                <span style="color: {status_color}; font-weight: bold; font-size: 14px; 
                             background: {status_color}22; padding: 6px 16px; border-radius: 20px;">
                    BOOK {deal.status.value.upper()}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Deal info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Deal Type", deal.deal_type.value.capitalize())
        with col2:
            st.metric("Target Raise", f"{deal.currency} {deal.target_amount:,.0f}")
        with col3:
            st.metric("Currency", deal.currency)
        
        if deal.description:
            st.markdown(f"""
            <div style="background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 8px; padding: 15px; margin: 15px 0;">
                <p style="color: #e5e5e5; margin: 0;">{deal.description}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Disclaimer
        show_disclaimer()
        
        # Tabs
        tab1, tab2 = st.tabs(["📊 Pricing Bands & IOI Submission", "📋 My IOIs"])
        
        with tab1:
            render_ioi_submission(db, deal, bands, deal_service, user_id)
        
        with tab2:
            render_my_iois(db, deal, bands, deal_service, user_id)
    
    finally:
        db.close()


def render_ioi_submission(db, deal, bands, deal_service, user_id):
    """Render IOI submission form"""
    st.markdown("### 📊 Pricing Bands")
    
    if not bands:
        show_warning("No pricing bands available for this deal yet.")
        return
    
    # Show bands as cards
    band_type = "Valuation" if deal.deal_type == DealType.EQUITY else "Yield"
    
    # Table header
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat({len(bands)}, 1fr); gap: 10px; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    cols = st.columns(len(bands))
    for i, band in enumerate(bands):
        with cols[i]:
            # Check if user has IOI for this band
            existing_ioi = db.query(IOI).filter(
                IOI.deal_id == deal.id,
                IOI.investor_user_id == user_id,
                IOI.band_id == band.id,
                IOI.is_active == True
            ).first()
            
            has_ioi = existing_ioi is not None
            border_color = '#22c55e' if has_ioi else '#2d2d44'
            
            st.markdown(f"""
            <div style="background: #1a1a2e; border: 2px solid {border_color}; border-radius: 12px; padding: 15px; text-align: center;">
                <div style="color: #a78bfa; font-weight: bold; font-size: 16px;">{band.label}</div>
                <div style="color: white; font-size: 18px; margin: 10px 0;">
                    {deal.currency} {band.band_value:,.0f}
                </div>
                {f'<div style="color: #6b7280; font-size: 11px;">{band.pe_ratio}</div>' if band.pe_ratio else ''}
                {f'<div style="color: #6b7280; font-size: 11px;">{band.ev_ebitda}</div>' if band.ev_ebitda else ''}
                {'<div style="color: #22c55e; font-size: 11px; margin-top: 8px;">✓ IOI Submitted</div>' if has_ioi else ''}
            </div>
            """, unsafe_allow_html=True)
    
    # IOI Submission Form
    if deal.status != DealStatus.OPEN:
        show_warning("The book is not currently open for IOI submissions.")
        return
    
    st.markdown("---")
    st.markdown("### 📝 Submit Indication of Interest")
    
    with st.form("ioi_submission_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Band selection
            band_options = {b.label: b.id for b in bands}
            selected_band_label = st.selectbox(
                "Select Price/Yield Band",
                list(band_options.keys())
            )
            selected_band_id = band_options[selected_band_label]
            
            # Amount
            amount = st.number_input(
                f"IOI Amount ({deal.currency})",
                min_value=0.0,
                value=1000000.0,
                step=100000.0,
                format="%.0f"
            )
        
        with col2:
            # Strength
            strength = st.selectbox(
                "Interest Strength",
                ["Soft", "Strong"],
                help="Soft = preliminary interest, Strong = high conviction"
            )
            
            # Anchor flag
            anchor_flag = st.checkbox(
                "Request Anchor Status",
                help="Indicate if you're interested in being an anchor investor"
            )
        
        # Note
        investor_note = st.text_area(
            "Additional Notes (optional)",
            placeholder="E.g., 'Would consider higher amount at Price 2', 'Need covenant X'...",
            max_chars=500
        )
        
        # Disclaimer acceptance
        st.markdown("---")
        disclaimer_accepted = st.checkbox(
            "I acknowledge that this IOI is non-binding and subject to further diligence and documentation. "
            "This is not a commitment to invest and may be withdrawn at any time before final documentation.",
            value=False
        )
        
        submitted = st.form_submit_button("Submit IOI", use_container_width=True, type="primary")
        
        if submitted:
            if not disclaimer_accepted:
                show_error("Please accept the disclaimer to submit your IOI.")
            elif amount <= 0:
                show_error("Please enter a valid amount greater than zero.")
            else:
                strength_enum = IOIStrength.SOFT if strength == "Soft" else IOIStrength.STRONG
                
                success, msg, ioi = deal_service.submit_ioi(
                    deal_id=deal.id,
                    investor_user_id=user_id,
                    band_id=selected_band_id,
                    amount=amount,
                    strength=strength_enum,
                    anchor_flag=anchor_flag,
                    investor_note=investor_note,
                    disclaimer_accepted=True
                )
                
                if success:
                    show_success(f"IOI submitted successfully for {selected_band_label}!")
                    st.rerun()
                else:
                    show_error(msg)


def render_my_iois(db, deal, bands, deal_service, user_id):
    """Render investor's IOIs for this deal"""
    st.markdown("### 📋 My IOIs for this Deal")
    
    iois = deal_service.get_investor_iois(deal.id, user_id)
    
    if not iois:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: #1a1a2e; border-radius: 12px;">
            <p style="color: #9ca3af;">You haven't submitted any IOIs for this deal yet.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    total_committed = sum(ioi.amount for ioi in iois)
    
    st.markdown(f"""
    <div style="background: #1a2e1a; border: 1px solid #2d442d; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <div style="color: #9ca3af; font-size: 12px;">Total Committed</div>
        <div style="color: #22c55e; font-size: 28px; font-weight: bold;">{deal.currency} {total_committed:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # IOI cards
    for ioi in iois:
        band = db.query(Band).filter(Band.id == ioi.band_id).first()
        
        anchor_badge = '<span style="background:#8b5cf6;color:white;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:10px;">ANCHOR REQUEST</span>' if ioi.anchor_flag else ''
        
        st.markdown(f"""
        <div style="background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 12px; padding: 20px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="color: #a78bfa; font-weight: bold; font-size: 16px;">
                        {band.label if band else 'N/A'}{anchor_badge}
                    </div>
                    <div style="color: white; font-size: 24px; font-weight: bold; margin: 8px 0;">
                        {deal.currency} {ioi.amount:,.0f}
                    </div>
                    <div style="color: #9ca3af; font-size: 12px;">
                        Strength: <span style="color: {'#22c55e' if ioi.strength == IOIStrength.STRONG else '#f59e0b'};">
                            {ioi.strength.value if ioi.strength else 'N/A'}
                        </span>
                    </div>
                    {f'<div style="color: #6b7280; font-size: 12px; margin-top: 8px; font-style: italic;">"{ioi.investor_note}"</div>' if ioi.investor_note else ''}
                </div>
                <div style="text-align: right; color: #6b7280; font-size: 11px;">
                    Submitted: {ioi.created_at.strftime('%Y-%m-%d %H:%M')}<br>
                    {f"Updated: {ioi.updated_at.strftime('%Y-%m-%d %H:%M')}" if ioi.updated_at != ioi.created_at else ""}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Edit/Delete buttons (only if book is open)
        if deal.status == DealStatus.OPEN:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("✏️ Edit", key=f"edit_ioi_{ioi.id}", use_container_width=True):
                    st.session_state[f'editing_ioi_{ioi.id}'] = True
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", key=f"delete_ioi_{ioi.id}", use_container_width=True):
                    success, msg = deal_service.delete_ioi(ioi.id, user_id)
                    if success:
                        show_success("IOI deleted.")
                        st.rerun()
                    else:
                        show_error(msg)
    
    # Show indicative range if deal is closed and range is set
    if deal.status == DealStatus.CLOSED and deal.indicative_range_low_band_id:
        low_band = db.query(Band).filter(Band.id == deal.indicative_range_low_band_id).first()
        high_band = db.query(Band).filter(Band.id == deal.indicative_range_high_band_id).first()
        
        if low_band and high_band:
            st.markdown("---")
            st.markdown("### 🎯 Indicative Price Range Announced")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #2d1a4a 100%); 
                        border: 2px solid #8b5cf6; border-radius: 12px; padding: 25px; text-align: center;">
                <div style="color: #a78bfa; font-size: 14px; margin-bottom: 10px;">Selected Range</div>
                <div style="color: white; font-size: 24px; font-weight: bold;">
                    {low_band.label} – {high_band.label}
                </div>
                <div style="color: #9ca3af; font-size: 16px; margin-top: 10px;">
                    {deal.currency} {low_band.band_value:,.0f} – {deal.currency} {high_band.band_value:,.0f}
                </div>
                {f'<div style="color: #6b7280; font-size: 13px; margin-top: 15px; font-style: italic;">{deal.indicative_range_description}</div>' if deal.indicative_range_description else ''}
            </div>
            """, unsafe_allow_html=True)
