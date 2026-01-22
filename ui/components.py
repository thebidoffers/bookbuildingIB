"""
Common UI Components and Styling
Shared components and CSS for the application
"""

import streamlit as st


# Dark theme CSS
DARK_THEME_CSS = """
<style>
    /* Main app background */
    .stApp {
        background-color: #0e0e1a;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Card container styling */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2d2d44;
        margin-bottom: 15px;
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #1a2e1a 0%, #163e16 100%);
        border: 1px solid #2d442d;
    }
    
    .metric-card-amber {
        background: linear-gradient(135deg, #2e2a1a 0%, #3e3516 100%);
        border: 1px solid #44402d;
    }
    
    .metric-card-red {
        background: linear-gradient(135deg, #2e1a1a 0%, #3e1616 100%);
        border: 1px solid #442d2d;
    }
    
    /* Coverage badge */
    .coverage-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .coverage-green {
        background-color: #22c55e;
        color: white;
    }
    
    .coverage-amber {
        background-color: #f59e0b;
        color: white;
    }
    
    .coverage-red {
        background-color: #ef4444;
        color: white;
    }
    
    /* Band card styling */
    .band-card {
        background: #1a1a2e;
        border: 1px solid #2d2d44;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .band-card-selected {
        border: 2px solid #8b5cf6;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
    }
    
    /* Status indicators */
    .status-open {
        color: #22c55e;
        font-weight: bold;
    }
    
    .status-closed {
        color: #ef4444;
        font-weight: bold;
    }
    
    .status-draft {
        color: #6b7280;
        font-weight: bold;
    }
    
    /* Table styling */
    .dataframe {
        background-color: #1a1a2e !important;
    }
    
    .dataframe th {
        background-color: #2d2d44 !important;
        color: white !important;
    }
    
    .dataframe td {
        background-color: #1a1a2e !important;
        color: #e5e5e5 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    }
    
    /* Secondary button */
    .secondary-btn > button {
        background: transparent !important;
        border: 1px solid #6366f1 !important;
        color: #6366f1 !important;
    }
    
    /* Danger button */
    .danger-btn > button {
        background: #ef4444 !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        background-color: #1a1a2e !important;
        color: white !important;
        border: 1px solid #2d2d44 !important;
    }
    
    /* Disclaimer box */
    .disclaimer-box {
        background-color: #1a1a2e;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        font-size: 12px;
        color: #fbbf24;
    }
    
    /* Header bar */
    .header-bar {
        background: linear-gradient(90deg, #1a1a2e 0%, #2d2d44 100%);
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Anchor badge */
    .anchor-badge {
        display: inline-block;
        background-color: #8b5cf6;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        margin-left: 8px;
    }
    
    /* Feedback note */
    .feedback-note {
        background-color: #1a1a2e;
        border-left: 3px solid #6366f1;
        padding: 10px 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Range selector */
    .range-option {
        background: #1a1a2e;
        border: 2px solid #2d2d44;
        border-radius: 8px;
        padding: 15px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .range-option:hover {
        border-color: #6366f1;
    }
    
    .range-option-selected {
        border-color: #8b5cf6;
        background: #1e1e3f;
    }
    
    /* Heat map colors */
    .heat-low { background: linear-gradient(90deg, #ef4444 0%, transparent 100%); }
    .heat-medium { background: linear-gradient(90deg, #f59e0b 0%, transparent 100%); }
    .heat-high { background: linear-gradient(90deg, #22c55e 0%, transparent 100%); }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""


def apply_dark_theme():
    """Apply dark theme CSS to the app"""
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def show_disclaimer():
    """Show the standard disclaimer"""
    st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ IMPORTANT DISCLAIMER:</strong><br>
        This is an indicative early-look demand tool. It is not an offering document, 
        not investment advice, and not a solicitation. All Indications of Interest (IOIs) 
        are non-binding and subject to further diligence and documentation.
    </div>
    """, unsafe_allow_html=True)


def format_currency(amount: float, currency: str = "AED") -> str:
    """Format amount as currency string"""
    if amount >= 1_000_000:
        return f"{currency} {amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{currency} {amount/1_000:.0f}K"
    else:
        return f"{currency} {amount:,.0f}"


def get_coverage_class(coverage: float) -> str:
    """Get CSS class based on coverage ratio"""
    if coverage >= 1.0:
        return "green"
    elif coverage >= 0.75:
        return "amber"
    else:
        return "red"


def render_coverage_badge(coverage: float) -> str:
    """Render coverage badge HTML"""
    color_class = get_coverage_class(coverage)
    return f'<span class="coverage-badge coverage-{color_class}">{coverage:.2f}x Covered</span>'


def render_status_badge(status: str) -> str:
    """Render status badge HTML"""
    status_lower = status.lower() if isinstance(status, str) else status.value.lower()
    return f'<span class="status-{status_lower}">{status_lower.upper()}</span>'


def render_metric_card(title: str, value: str, subtitle: str = "", color: str = "default") -> str:
    """Render a metric card"""
    card_class = f"metric-card metric-card-{color}" if color != "default" else "metric-card"
    return f"""
    <div class="{card_class}">
        <div style="color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        <div style="color: white; font-size: 24px; font-weight: bold; margin: 8px 0;">{value}</div>
        <div style="color: #6b7280; font-size: 12px;">{subtitle}</div>
    </div>
    """


def render_band_demand_card(
    label: str,
    demand: float,
    target: float,
    currency: str,
    coverage: float
) -> str:
    """Render a band demand card"""
    color_class = get_coverage_class(coverage)
    coverage_badge = render_coverage_badge(coverage)
    
    return f"""
    <div class="band-card metric-card-{color_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="color: white; font-size: 16px; font-weight: bold;">{label}</span>
            {coverage_badge}
        </div>
        <div style="color: #a78bfa; font-size: 24px; font-weight: bold;">{currency} {demand:,.0f}</div>
        <div style="color: #6b7280; font-size: 12px;">of {currency} {target:,.0f} target</div>
    </div>
    """


def show_error(message: str):
    """Show error message"""
    st.error(f"❌ {message}")


def show_success(message: str):
    """Show success message"""
    st.success(f"✅ {message}")


def show_warning(message: str):
    """Show warning message"""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """Show info message"""
    st.info(f"ℹ️ {message}")
