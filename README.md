# 📊 Early-Look Bookbuilding MVP

A lightweight, non-binding bookbuilding web application for small/medium issuers to discover institutional investor demand and indicative pricing for capital raises.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Overview

This application enables issuers to:
- Create "Deal Rooms" for equity or debt capital raises
- Invite up to 10 institutional investors
- Collect non-binding Indications of Interest (IOIs) tied to price/yield bands
- View real-time demand aggregation during the bookbuilding window
- Select an indicative price range and generate summary reports

**Important:** All IOIs are non-binding and subject to further diligence and documentation. This is not an offering platform.

## ✨ Features

### For Issuers
- 🏢 Create and manage multiple deal rooms
- 📊 Define 3-7 pricing bands (equity valuation or debt yield)
- 👥 Invite up to 10 investors per deal
- 📈 Real-time demand dashboard with coverage metrics
- 💬 Log investor feedback notes
- 🎯 Select indicative price range (adjacent bands)
- 📄 Generate PDF summary reports

### For Investors
- 📋 View deals they're invited to
- 📝 Submit IOIs with amount, strength, and notes
- ✏️ Edit or delete IOIs while book is open
- 🔒 Private - cannot see other investors' IOIs

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python 3.9+
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** bcrypt password hashing
- **Charts:** Plotly
- **Reports:** ReportLab (PDF generation)

## 📁 Project Structure

```
bookbuilding-mvp/
├── app.py                 # Main Streamlit application
├── db.py                  # Database connection & session management
├── models.py              # SQLAlchemy ORM models
├── auth.py                # Authentication & authorization
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── services/
│   ├── __init__.py
│   └── deal_service.py    # Business logic for deals & IOIs
├── ui/
│   ├── __init__.py
│   ├── components.py      # Shared UI components & styling
│   ├── auth_pages.py      # Login/registration pages
│   ├── issuer_dashboard.py # Issuer portal UI
│   └── investor_portal.py  # Investor portal UI
├── utils/
│   ├── __init__.py
│   ├── report_generator.py # PDF report generation
│   └── demo_data.py        # Demo data loader
└── data/
    ├── bookbuilding.db    # SQLite database (auto-created)
    └── uploads/           # Document uploads directory
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bookbuilding-mvp.git
   cd bookbuilding-mvp
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser:**
   The app will automatically open at `http://localhost:8501`

## 📖 User Guide

### Creating an Issuer Account

1. Open the app and click "Register as Issuer" tab
2. Enter your organization name, email, and password
3. Click "Create Issuer Account"
4. Log in with your credentials

### Creating a Deal

1. Log in as an issuer
2. Click "➕ Create New Deal" in the sidebar
3. Fill in deal details:
   - Deal name
   - Deal type (Equity/Debt)
   - Target raise amount
   - Currency (AED/USD)
4. Configure 3-7 pricing bands with valuations/yields
5. Click "Create Deal"

### Inviting Investors

1. Open a deal dashboard
2. Go to "👥 Investors" tab
3. Fill in investor details (name, email, type)
4. Click "Send Invitation"
5. Share the generated invite link with the investor

### Opening the Book

1. Ensure you have at least 3 pricing bands
2. Click "🚀 Open Book" on the deal dashboard
3. Investors can now submit IOIs

### Submitting an IOI (Investor)

1. Click the invite link received from issuer
2. Create an account with the invited email
3. View the deal and pricing bands
4. Select a band and enter your IOI amount
5. Choose interest strength (Soft/Strong)
6. Accept the disclaimer and submit

### Closing the Book & Selecting Range

1. Click "🔒 Close Book" when ready
2. Go to "🎯 Select Range" tab
3. Review demand summary
4. Select two adjacent bands for the indicative range
5. Add an investor-facing description
6. Confirm the selection

### Generating Reports

1. Close the book first
2. Click "📄 Download Report"
3. A PDF will be generated with:
   - Deal overview
   - Band summary with demand
   - IOI details (confidential)
   - Selected indicative range
   - Disclaimer

## 🎭 Demo Mode

To quickly test the application:

1. Log in as any issuer
2. Click "Load Demo Data" in the sidebar
3. Demo credentials will be displayed:
   - **Issuer:** `demo@issuer.com` / `demo123`
   - **Investors:** Use password `investor123`

This creates a sample deal with 5 bands and 4 investors with pre-submitted IOIs.

## 🔐 Security Features

- Password hashing with bcrypt
- Role-based access control (Issuer/Investor)
- Token-based invite links with expiration
- Investors cannot see other investors' IOIs
- Max 10 investors per deal
- IOI amount validation

## ⚠️ Compliance Disclaimer

This application displays the following disclaimer on all relevant screens:

> **IMPORTANT DISCLAIMER:** This is an indicative early-look demand tool. It is not an offering document, not investment advice, and not a solicitation. All Indications of Interest (IOIs) are non-binding and subject to further diligence and documentation.

This MVP does NOT handle:
- Public marketing or prospectuses
- Securities law compliance
- Actual allocations or underwriting
- KYC/AML verification

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root:

```env
# Database path (default: ./data/bookbuilding.db)
DATABASE_PATH=./data/bookbuilding.db

# Debug mode
DEBUG=false
```

### Database

The application uses SQLite by default. The database file is created automatically at `./data/bookbuilding.db`.

To reset the database:
```python
from db import reset_db
reset_db()  # WARNING: Deletes all data
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Charts powered by [Plotly](https://plotly.com/)
- PDF generation by [ReportLab](https://www.reportlab.com/)

---

**Note:** This is an MVP for demonstration purposes. For production use, additional security measures, compliance features, and infrastructure considerations would be required.
