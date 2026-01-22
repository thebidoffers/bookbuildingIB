"""
Issuer Dashboard UI
Main dashboard for issuers to manage deals and view demand
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional
import io

from db import get_session
from models import (
    Deal, Band, IOI, Issuer, Invitation, User, DealStatus, DealType,
    InvestorType, FeedbackScope, InvitationStatus, IOIStrength
)
from services.deal_service import DealService
from auth import create_invitation, get_user_deals, can_access_deal
from ui.components import (
    apply_dark_theme, show_disclaimer, format_currency,
    get_coverage_class, render_coverage_badge, render_status_badge,
    render_metric_card, render_band_demand_card,
    show_error, show_success, show_warning, show_info
)
from utils.report_generator import generate_deal_report, format_datetime


def render_issuer_dashboard():
    """Main issuer dashboard"""
    apply_dark_theme()
    
    user = st.session_state.user
    
    # Sidebar navigation
    st.sidebar.markdown("### 🏢 Issuer Portal")
    
    # Check if viewing a specific deal
    if st.session_state.get('current_deal_id'):
        if st.sidebar.button("← Back to Deals List", use_container_width=True):
            st.session_state.current_deal_id = None
            st.rerun()
        st.sidebar.markdown("---")
    
    menu_options = [
        "📊 My Deals",
        "➕ Create New Deal",
    ]
    
    selected = st.sidebar.radio("Navigation", menu_options, label_visibility="collapsed")
    
    # Load demo data option
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎭 Demo Mode")
    if st.sidebar.button("Load Demo Data", use_container_width=True):
        load_demo_data_handler()
    
    # Route to appropriate page
    if st.session_state.get('current_deal_id'):
        render_deal_dashboard(st.session_state.current_deal_id)
    elif selected == "📊 My Deals":
        render_deals_list()
    elif selected == "➕ Create New Deal":
        render_create_deal()


def load_demo_data_handler():
    """Handle loading demo data"""
    from utils.demo_data import load_demo_data, clear_demo_data
    
    db = get_session()
    try:
        # Clear existing demo data first
        clear_demo_data(db)
        result = load_demo_data(db)
        st.session_state.demo_info = result
        show_success(f"Demo data loaded! Deal: {result['deal_name']}")
        st.rerun()
    except Exception as e:
        show_error(f"Error loading demo data: {str(e)}")
    finally:
        db.close()


def render_deals_list():
    """Render list of issuer's deals"""
    st.markdown("## 📊 My Deals")
    
    # Show demo credentials if available
    if st.session_state.get('demo_info'):
        info = st.session_state.demo_info
        with st.expander("🎭 Demo Credentials", expanded=True):
            st.markdown(f"""
            **Issuer Login:** `{info['issuer_email']}` / `{info['issuer_password']}`  
            **Investor Password:** `{info['investor_password']}`  
            **Investors:** {', '.join([i['email'] for i in info['investors']])}
            """)
    
    db = get_session()
    try:
        # Get issuer's deals
        issuer = db.query(Issuer).filter(
            Issuer.owner_user_id == st.session_state.user['id']
        ).first()
        
        if not issuer:
            show_warning("No issuer profile found. Please contact support.")
            return
        
        deals = db.query(Deal).filter(Deal.issuer_id == issuer.id).order_by(Deal.created_at.desc()).all()
        
        if not deals:
            st.markdown("""
            <div style="text-align: center; padding: 60px 20px; background: #1a1a2e; border-radius: 12px; margin: 20px 0;">
                <h3 style="color: #9ca3af;">No deals yet</h3>
                <p style="color: #6b7280;">Create your first deal to get started with bookbuilding</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ Create Your First Deal", use_container_width=True):
                st.session_state.nav_to_create = True
                st.rerun()
            return
        
        # Deal cards grid
        for deal in deals:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                status_color = {
                    DealStatus.DRAFT: "#6b7280",
                    DealStatus.OPEN: "#22c55e", 
                    DealStatus.CLOSED: "#ef4444"
                }.get(deal.status, "#6b7280")
                
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 12px; padding: 20px; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="margin: 0; color: white;">{deal.name}</h3>
                            <p style="color: #9ca3af; margin: 5px 0;">
                                {deal.deal_type.value.capitalize()} • {deal.currency} {deal.target_amount:,.0f} target
                            </p>
                        </div>
                        <span style="color: {status_color}; font-weight: bold; font-size: 12px; 
                                     background: {status_color}22; padding: 4px 12px; border-radius: 20px;">
                            {deal.status.value.upper()}
                        </span>
                    </div>
                    <p style="color: #6b7280; font-size: 12px; margin-top: 10px;">
                        Created: {deal.created_at.strftime('%Y-%m-%d %H:%M')}
                        {f" • Closed: {deal.closed_at.strftime('%Y-%m-%d %H:%M')}" if deal.closed_at else ""}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📈 Open Dashboard", key=f"view_{deal.id}", use_container_width=True):
                    st.session_state.current_deal_id = deal.id
                    st.rerun()
    
    finally:
        db.close()


def render_deal_dashboard(deal_id: int):
    """Render the live bookbuilding dashboard for a deal"""
    db = get_session()
    try:
        deal_service = DealService(db)
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        
        if not deal:
            show_error("Deal not found")
            return
        
        # Header with status
        status_color = {
            DealStatus.DRAFT: "#6b7280",
            DealStatus.OPEN: "#22c55e", 
            DealStatus.CLOSED: "#ef4444"
        }.get(deal.status, "#6b7280")
        
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <h1 style="color: #a78bfa; margin: 0;">Live Bookbuilding Window</h1>
                <p style="color: #9ca3af;">Real-Time Demand Monitor • {deal.name}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_h2:
            st.markdown(f"""
            <div style="text-align: right; padding: 10px;">
                <span style="color: {status_color}; font-weight: bold; font-size: 14px;">
                    {deal.status.value.upper()}
                </span>
                <br>
                <span style="color: #6b7280; font-size: 12px;">
                    {f"Closed: {deal.closed_at.strftime('%Y-%m-%d')}" if deal.closed_at else f"Target: {deal.currency} {deal.target_amount:,.0f}"}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Get demand summary
        summary = deal_service.get_demand_summary(deal_id)
        total_demand = summary.get('total_demand', 0)
        total_bids = summary.get('total_bids', 0)
        
        # Top KPIs row
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.metric("Total Demand", f"{deal.currency} {total_demand:,.0f}")
        with kpi2:
            st.metric("Total Bids", str(total_bids))
        with kpi3:
            coverage = total_demand / deal.target_amount if deal.target_amount > 0 else 0
            st.metric("Coverage", f"{coverage:.2f}x")
        with kpi4:
            st.metric("Status", deal.status.value.upper())
        
        # Deal controls
        st.markdown("---")
        ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)
        
        with ctrl1:
            if deal.status == DealStatus.DRAFT:
                if st.button("🚀 Open Book", use_container_width=True, type="primary"):
                    success, msg = deal_service.open_deal(deal_id)
                    if success:
                        show_success(msg)
                        st.rerun()
                    else:
                        show_error(msg)
        
        with ctrl2:
            if deal.status == DealStatus.OPEN:
                if st.button("🔒 Close Book", use_container_width=True):
                    success, msg = deal_service.close_deal(deal_id)
                    if success:
                        show_success(msg)
                        st.rerun()
                    else:
                        show_error(msg)
        
        with ctrl3:
            if deal.status == DealStatus.CLOSED:
                if st.button("📄 Download Report", use_container_width=True):
                    generate_and_download_report(db, deal, deal_service)
        
        with ctrl4:
            if st.button("👥 Manage Investors", use_container_width=True):
                st.session_state.show_investors = True
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Demand & Coverage", 
            "📋 Bid Management", 
            "👥 Investors",
            "💬 Feedback Notes",
            "🎯 Select Range"
        ])
        
        with tab1:
            render_demand_coverage(deal, summary, deal_service)
        
        with tab2:
            render_bid_management(db, deal, summary)
        
        with tab3:
            render_investors_management(db, deal)
        
        with tab4:
            render_feedback_notes(db, deal, deal_service)
        
        with tab5:
            render_range_selection(db, deal, deal_service, summary)
    
    finally:
        db.close()


def render_demand_coverage(deal, summary, deal_service):
    """Render demand curve and coverage visualization"""
    st.markdown("### Demand Curve & Coverage")
    
    bands = summary.get('bands', [])
    demand_by_band = summary.get('demand_by_band', {})
    
    if not bands:
        show_warning("No pricing bands defined yet. Please add bands to the deal.")
        return
    
    # Coverage cards
    cols = st.columns(len(bands))
    for i, band in enumerate(bands):
        band_data = demand_by_band.get(band.id, {})
        demand = band_data.get('demand', 0)
        coverage = band_data.get('coverage', 0)
        
        color_class = get_coverage_class(coverage)
        bg_color = {
            'green': '#1a2e1a',
            'amber': '#2e2a1a', 
            'red': '#2e1a1a'
        }.get(color_class, '#1a1a2e')
        
        badge_color = {
            'green': '#22c55e',
            'amber': '#f59e0b',
            'red': '#ef4444'
        }.get(color_class, '#6b7280')
        
        with cols[i]:
            st.markdown(f"""
            <div style="background: {bg_color}; border: 1px solid #2d2d44; border-radius: 12px; padding: 15px; text-align: center;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="color: white; font-weight: bold;">{band.label}</span>
                    <span style="background: {badge_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">
                        {coverage:.2f}x Covered
                    </span>
                </div>
                <div style="color: #a78bfa; font-size: 20px; font-weight: bold;">
                    {deal.currency} {demand:,.0f}
                </div>
                <div style="color: #6b7280; font-size: 11px;">
                    of {deal.currency} {deal.target_amount:,.0f} target
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Bar chart
    st.markdown("### Demand by Band")
    
    chart_data = []
    for band in bands:
        band_data = demand_by_band.get(band.id, {})
        chart_data.append({
            'Band': band.label,
            'Demand': band_data.get('demand', 0),
            'Value': band.band_value
        })
    
    df = pd.DataFrame(chart_data)
    
    fig = px.bar(
        df, 
        x='Band', 
        y='Demand',
        color_discrete_sequence=['#a78bfa'],
        labels={'Demand': f'Committed ({deal.currency})'}
    )
    
    fig.update_layout(
        plot_bgcolor='#1a1a2e',
        paper_bgcolor='#1a1a2e',
        font_color='white',
        xaxis=dict(gridcolor='#2d2d44'),
        yaxis=dict(gridcolor='#2d2d44'),
        showlegend=False
    )
    
    # Add target line
    fig.add_hline(
        y=deal.target_amount, 
        line_dash="dash", 
        line_color="#ef4444",
        annotation_text=f"Target: {deal.currency} {deal.target_amount:,.0f}"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_bid_management(db, deal, summary):
    """Render bid management table"""
    st.markdown("### Bid Management Table")
    
    # Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    bands = summary.get('bands', [])
    band_options = ["All Bands"] + [b.label for b in bands]
    
    with col1:
        selected_band = st.selectbox("Filter by Band", band_options)
    
    with col2:
        investor_types = ["All Investor Types"] + [t.value for t in InvestorType]
        selected_type = st.selectbox("Filter by Type", investor_types)
    
    with col3:
        show_anchors = st.checkbox("Show Anchors Only")
    
    # Get IOIs
    iois = db.query(IOI).filter(
        IOI.deal_id == deal.id,
        IOI.is_active == True
    ).all()
    
    if not iois:
        show_info("No IOIs submitted yet.")
        return
    
    # Build table data
    table_data = []
    for ioi in iois:
        investor = db.query(User).filter(User.id == ioi.investor_user_id).first()
        invitation = db.query(Invitation).filter(
            Invitation.deal_id == deal.id,
            Invitation.accepted_user_id == ioi.investor_user_id
        ).first()
        
        band = db.query(Band).filter(Band.id == ioi.band_id).first()
        
        inv_type = invitation.investor_type.value if invitation and invitation.investor_type else "Other"
        
        # Apply filters
        if selected_band != "All Bands" and band.label != selected_band:
            continue
        if selected_type != "All Investor Types" and inv_type != selected_type:
            continue
        if show_anchors and not ioi.anchor_flag:
            continue
        
        table_data.append({
            'Investor Name': investor.display_name if investor else "Unknown",
            'Type': inv_type,
            'Amount': f"{deal.currency} {ioi.amount:,.0f}",
            'Band': band.label if band else "N/A",
            'Strength': ioi.strength.value if ioi.strength else "N/A",
            'Anchor': "⚓" if ioi.anchor_flag else "",
            'Timestamp': ioi.created_at.strftime('%Y-%m-%d %H:%M'),
            'Note': ioi.investor_note or ""
        })
    
    if not table_data:
        show_info("No IOIs match the current filters.")
        return
    
    # Display table
    df = pd.DataFrame(table_data)
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Amount': st.column_config.TextColumn('Amount (AED)'),
            'Anchor': st.column_config.TextColumn('Anchor', width='small'),
            'Note': st.column_config.TextColumn('Note', width='medium')
        }
    )
    
    # Export button
    with col4:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            f"iois_{deal.name}_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )


def render_investors_management(db, deal):
    """Render investor invitation management"""
    st.markdown("### Investor Management")
    
    # Current invitations
    invitations = db.query(Invitation).filter(Invitation.deal_id == deal.id).all()
    
    invite_count = len(invitations)
    st.markdown(f"**{invite_count}/10 investors invited**")
    
    if invitations:
        for inv in invitations:
            status_color = {
                InvitationStatus.PENDING: "#f59e0b",
                InvitationStatus.ACCEPTED: "#22c55e",
                InvitationStatus.EXPIRED: "#ef4444"
            }.get(inv.status, "#6b7280")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                anchor_badge = '<span style="background:#8b5cf6;color:white;padding:2px 6px;border-radius:4px;font-size:10px;margin-left:8px;">ANCHOR</span>' if inv.anchor_potential else ''
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 8px; padding: 12px; margin: 5px 0;">
                    <div style="color: white; font-weight: bold;">
                        {inv.investor_name or inv.investor_email}{anchor_badge}
                    </div>
                    <div style="color: #6b7280; font-size: 12px;">{inv.investor_email}</div>
                    <div style="color: #9ca3af; font-size: 11px;">{inv.investor_type.value if inv.investor_type else 'Other'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="padding: 15px; text-align: center;">
                    <span style="color: {status_color}; font-weight: bold; font-size: 12px;">
                        {inv.status.value.upper()}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                if inv.status == InvitationStatus.PENDING:
                    # Show invite link
                    invite_url = f"?invite={inv.token}"
                    if st.button("📋 Copy Link", key=f"copy_{inv.id}"):
                        st.code(invite_url, language=None)
    
    # Add new invitation form
    if invite_count < 10:
        st.markdown("---")
        st.markdown("### ➕ Invite New Investor")
        
        with st.form("invite_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                inv_name = st.text_input("Investor Name", placeholder="John Smith")
                inv_email = st.text_input("Email", placeholder="investor@company.com")
            
            with col2:
                inv_type = st.selectbox("Investor Type", [t.value for t in InvestorType])
                anchor_potential = st.checkbox("Anchor Potential")
            
            submitted = st.form_submit_button("Send Invitation", use_container_width=True)
            
            if submitted:
                if not inv_name or not inv_email:
                    show_error("Please fill in all required fields")
                else:
                    inv_type_enum = InvestorType(inv_type)
                    success, msg, invitation = create_invitation(
                        db, deal.id, inv_email, inv_name, inv_type_enum, anchor_potential
                    )
                    if success:
                        show_success(f"Invitation created! Share this link with the investor:")
                        st.code(f"?invite={invitation.token}")
                        st.rerun()
                    else:
                        show_error(msg)
    else:
        show_warning("Maximum of 10 investors reached for this deal.")


def render_feedback_notes(db, deal, deal_service):
    """Render feedback notes section"""
    st.markdown("### 💬 Investor Feedback")
    
    # Add note form
    with st.form("feedback_form"):
        note_text = st.text_area(
            "Add a note",
            placeholder="Log investor feedback, e.g., 'Investor X wants anchor status...'"
        )
        submitted = st.form_submit_button("💾 Add Note", use_container_width=True)
        
        if submitted and note_text:
            success, msg, note = deal_service.add_feedback_note(
                deal.id,
                st.session_state.user['id'],
                note_text,
                FeedbackScope.GENERAL
            )
            if success:
                show_success("Note added!")
                st.rerun()
            else:
                show_error(msg)
    
    # Display existing notes
    notes = deal_service.get_feedback_notes(deal.id)
    
    if not notes:
        st.markdown("""
        <div style="color: #6b7280; text-align: center; padding: 20px;">
            No feedback notes yet.
        </div>
        """, unsafe_allow_html=True)
    else:
        for note in notes:
            st.markdown(f"""
            <div style="background: #1a1a2e; border-left: 3px solid #6366f1; padding: 12px 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <div style="color: white;">{note.note_text}</div>
                <div style="color: #6b7280; font-size: 11px; margin-top: 8px;">
                    {note.created_at.strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_range_selection(db, deal, deal_service, summary):
    """Render indicative range selection"""
    st.markdown("### 🎯 Select Indicative Valuation Range")
    
    if deal.status != DealStatus.CLOSED:
        show_warning("Please close the book before selecting the indicative range.")
        return
    
    bands = summary.get('bands', [])
    demand_by_band = summary.get('demand_by_band', {})
    
    if len(bands) < 2:
        show_error("At least 2 bands required to select a range.")
        return
    
    # Show early-look demand summary table
    st.markdown("#### Early-Look Demand Summary")
    
    table_data = []
    for band in bands:
        band_data = demand_by_band.get(band.id, {})
        
        # Calculate heat level
        coverage = band_data.get('coverage', 0)
        if coverage >= 1.0:
            heat = "🟢🟢🟢🟢"
        elif coverage >= 0.75:
            heat = "🟢🟢🟢"
        elif coverage >= 0.5:
            heat = "🟡🟡"
        elif coverage >= 0.25:
            heat = "🟠"
        else:
            heat = ""
        
        table_data.append({
            'Valuation Band': band.label,
            f'Equity Value ({deal.currency})': f"{deal.currency} {band.band_value:,.0f}",
            'Valuation Multiples': f"{band.pe_ratio or ''}\n{band.ev_ebitda or ''}".strip(),
            f'Total Demand ({deal.currency})': f"{deal.currency} {band_data.get('demand', 0):,.0f}",
            '# Investors': band_data.get('bid_count', 0),
            'Demand Heatmap': heat
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Range selection
    st.markdown("---")
    st.markdown("#### Select ITF Valuation Range")
    st.markdown("*Choose two adjacent valuation bands to set the official ITF range.*")
    
    # Create range options (adjacent pairs)
    range_options = []
    for i in range(len(bands) - 1):
        low_band = bands[i]
        high_band = bands[i + 1]
        range_options.append({
            'label': f"{low_band.label} – {high_band.label}",
            'subtitle': f"{deal.currency} {low_band.band_value/1e6:.0f}M – {deal.currency} {high_band.band_value/1e6:.0f}M",
            'low_id': low_band.id,
            'high_id': high_band.id
        })
    
    # Display as selectable cards
    cols = st.columns(len(range_options))
    
    selected_range_idx = st.session_state.get('selected_range_idx', None)
    
    for i, opt in enumerate(range_options):
        with cols[i]:
            is_selected = selected_range_idx == i
            border_color = '#8b5cf6' if is_selected else '#2d2d44'
            bg_color = '#1e1e3f' if is_selected else '#1a1a2e'
            
            if st.button(
                f"**{opt['label']}**\n{opt['subtitle']}", 
                key=f"range_{i}",
                use_container_width=True
            ):
                st.session_state.selected_range_idx = i
                st.rerun()
    
    # Description and confirmation
    if selected_range_idx is not None:
        selected = range_options[selected_range_idx]
        
        st.markdown("---")
        st.markdown("#### Prepare ITF Announcement")
        
        description = st.text_area(
            "Investor-Facing Description",
            placeholder="Provide a short summary for the ITF announcement...",
            key="range_description"
        )
        
        if st.button("✅ Confirm Indicative Range", type="primary", use_container_width=True):
            success, msg = deal_service.set_indicative_range(
                deal.id,
                selected['low_id'],
                selected['high_id'],
                description
            )
            if success:
                show_success(f"Indicative range set to {selected['label']}")
                st.rerun()
            else:
                show_error(msg)
    
    # Show current selection if exists
    if deal.indicative_range_low_band_id and deal.indicative_range_high_band_id:
        low_band = db.query(Band).filter(Band.id == deal.indicative_range_low_band_id).first()
        high_band = db.query(Band).filter(Band.id == deal.indicative_range_high_band_id).first()
        
        st.markdown("---")
        st.success(f"**Current Indicative Range:** {low_band.label} – {high_band.label}")
        if deal.indicative_range_description:
            st.markdown(f"*{deal.indicative_range_description}*")


def generate_and_download_report(db, deal, deal_service):
    """Generate and offer download of deal report"""
    summary = deal_service.get_demand_summary(deal.id)
    bands = summary.get('bands', [])
    
    # Prepare bands data
    bands_data = []
    for band in bands:
        bands_data.append({
            'id': band.id,
            'label': band.label,
            'band_value': band.band_value,
            'pe_ratio': band.pe_ratio,
            'ev_ebitda': band.ev_ebitda
        })
    
    # Prepare IOIs data
    iois = deal_service.get_all_deal_iois(deal.id)
    iois_data = []
    for ioi in iois:
        investor = db.query(User).filter(User.id == ioi.investor_user_id).first()
        invitation = db.query(Invitation).filter(
            Invitation.deal_id == deal.id,
            Invitation.accepted_user_id == ioi.investor_user_id
        ).first()
        band = db.query(Band).filter(Band.id == ioi.band_id).first()
        
        iois_data.append({
            'investor_name': investor.display_name if investor else "Unknown",
            'investor_type': invitation.investor_type.value if invitation and invitation.investor_type else "Other",
            'amount': ioi.amount,
            'band_label': band.label if band else "N/A",
            'strength': ioi.strength.value if ioi.strength else "N/A",
            'anchor_flag': ioi.anchor_flag
        })
    
    # Prepare selected range
    selected_range = None
    if deal.indicative_range_low_band_id and deal.indicative_range_high_band_id:
        low_band = db.query(Band).filter(Band.id == deal.indicative_range_low_band_id).first()
        high_band = db.query(Band).filter(Band.id == deal.indicative_range_high_band_id).first()
        selected_range = {
            'low_label': low_band.label,
            'high_label': high_band.label,
            'low_value': low_band.band_value,
            'high_value': high_band.band_value,
            'description': deal.indicative_range_description
        }
    
    # Prepare deal data
    deal_data = {
        'name': deal.name,
        'deal_type': deal.deal_type,
        'currency': deal.currency,
        'target_amount': deal.target_amount,
        'status': deal.status.value.upper(),
        'start_at': format_datetime(deal.start_at),
        'closed_at': format_datetime(deal.closed_at)
    }
    
    # Generate PDF
    pdf_bytes = generate_deal_report(
        deal_data,
        bands_data,
        summary,
        iois_data,
        selected_range
    )
    
    # Offer download
    st.download_button(
        "📥 Download PDF Report",
        pdf_bytes,
        f"bookbuilding_report_{deal.name}_{datetime.now().strftime('%Y%m%d')}.pdf",
        "application/pdf",
        use_container_width=True
    )


def render_create_deal():
    """Render create new deal form"""
    st.markdown("## ➕ Create New Deal")
    
    db = get_session()
    try:
        issuer = db.query(Issuer).filter(
            Issuer.owner_user_id == st.session_state.user['id']
        ).first()
        
        if not issuer:
            show_error("Issuer profile not found")
            return
        
        with st.form("create_deal_form"):
            st.markdown("### Deal Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                deal_name = st.text_input("Deal Name", placeholder="Series B Equity Raise")
                deal_type = st.selectbox("Deal Type", ["Equity", "Debt"])
                currency = st.selectbox("Currency", ["AED", "USD"])
            
            with col2:
                target_amount = st.number_input(
                    "Target Raise Amount",
                    min_value=0.0,
                    value=20000000.0,
                    step=1000000.0,
                    format="%.0f"
                )
                max_ioi = st.number_input(
                    "Max IOI Amount (optional)",
                    min_value=0.0,
                    value=0.0,
                    step=1000000.0,
                    format="%.0f",
                    help="Leave 0 for no limit"
                )
            
            description = st.text_area("Deal Description", placeholder="Brief description of the capital raise...")
            
            st.markdown("---")
            st.markdown("### Pricing Bands")
            st.markdown("*Define 3-7 pricing bands for investor IOIs*")
            
            num_bands = st.slider("Number of Bands", 3, 7, 5)
            
            bands_input = []
            cols = st.columns(num_bands)
            
            for i in range(num_bands):
                with cols[i]:
                    label = f"Price {i+1}" if deal_type == "Equity" else f"Yield {i+1}"
                    st.markdown(f"**{label}**")
                    
                    if deal_type == "Equity":
                        value = st.number_input(
                            "Valuation",
                            min_value=0.0,
                            value=float(150000000 + i * 25000000),
                            step=5000000.0,
                            format="%.0f",
                            key=f"band_val_{i}"
                        )
                        pe = st.text_input("P/E Ratio", placeholder="10x", key=f"pe_{i}")
                        ev = st.text_input("EV/EBITDA", placeholder="4.5x", key=f"ev_{i}")
                    else:
                        value = st.number_input(
                            "Yield %",
                            min_value=0.0,
                            max_value=50.0,
                            value=float(5 + i * 0.5),
                            step=0.25,
                            format="%.2f",
                            key=f"band_val_{i}"
                        )
                        pe = ""
                        ev = ""
                    
                    bands_input.append({
                        'label': label,
                        'value': value,
                        'pe': pe if deal_type == "Equity" else "",
                        'ev': ev if deal_type == "Equity" else ""
                    })
            
            st.markdown("---")
            submitted = st.form_submit_button("Create Deal", use_container_width=True, type="primary")
            
            if submitted:
                if not deal_name:
                    show_error("Please enter a deal name")
                elif target_amount <= 0:
                    show_error("Target amount must be positive")
                else:
                    deal_service = DealService(db)
                    
                    # Create deal
                    deal_type_enum = DealType.EQUITY if deal_type == "Equity" else DealType.DEBT
                    success, msg, deal = deal_service.create_deal(
                        issuer_id=issuer.id,
                        name=deal_name,
                        deal_type=deal_type_enum,
                        target_amount=target_amount,
                        currency=currency,
                        description=description,
                        max_ioi_amount=max_ioi if max_ioi > 0 else None
                    )
                    
                    if not success:
                        show_error(msg)
                    else:
                        # Add bands
                        for i, band in enumerate(bands_input):
                            deal_service.add_band(
                                deal_id=deal.id,
                                label=band['label'],
                                band_value=band['value'],
                                order_index=i + 1,
                                pe_ratio=band.get('pe', ''),
                                ev_ebitda=band.get('ev', '')
                            )
                        
                        show_success(f"Deal '{deal_name}' created successfully!")
                        st.session_state.current_deal_id = deal.id
                        st.rerun()
    
    finally:
        db.close()


def render_issuer_settings():
    """Render issuer settings page"""
    st.markdown("## ⚙️ Settings")
    show_info("Settings page coming soon...")
