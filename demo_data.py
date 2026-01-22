"""
Demo Data Loader
Creates sample data for testing the application
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import (
    User, UserRole, Issuer, Deal, Band, Invitation, Investor,
    IOI, DealType, DealStatus, InvestorType, IOIStrength, InvitationStatus
)
from auth import hash_password, generate_token


def load_demo_data(db: Session) -> dict:
    """
    Load demo data for testing
    Creates an issuer, a deal with 5 bands, and 4 investors with IOIs
    
    Returns dict with created entities and credentials
    """
    # Create issuer user
    issuer_user = User(
        email="demo@issuer.com",
        password_hash=hash_password("demo123"),
        role=UserRole.ISSUER,
        display_name="Demo Issuer Admin"
    )
    db.add(issuer_user)
    db.flush()
    
    # Create issuer profile
    issuer = Issuer(
        org_name="Demo Holdings LLC",
        owner_user_id=issuer_user.id
    )
    db.add(issuer)
    db.flush()
    
    # Create a deal
    deal = Deal(
        issuer_id=issuer.id,
        name="Series B Equity Raise",
        deal_type=DealType.EQUITY,
        currency="AED",
        target_amount=20000000,
        description="Series B equity raise for expansion into GCC markets.",
        status=DealStatus.OPEN,
        start_at=datetime.utcnow() - timedelta(days=2),
        end_at=datetime.utcnow() + timedelta(days=5),
        max_ioi_amount=50000000
    )
    db.add(deal)
    db.flush()
    
    # Create 5 bands
    bands_data = [
        {"label": "Price 1", "value": 175000000, "pe": "P/E (2025): 10x", "ev": "EV/EBITDA (2026): 4.5x"},
        {"label": "Price 2", "value": 190000000, "pe": "P/E (2025): 11x", "ev": "EV/EBITDA (2026): 4.2x"},
        {"label": "Price 3", "value": 225000000, "pe": "P/E (2025): 12.5x", "ev": "EV/EBITDA (2026): 4.0x"},
        {"label": "Price 4", "value": 250000000, "pe": "P/E (2025): 14x", "ev": "EV/EBITDA (2026): 3.7x"},
        {"label": "Price 5", "value": 270000000, "pe": "P/E (2025): 15x", "ev": "EV/EBITDA (2026): 3.5x"},
    ]
    
    bands = []
    for i, bd in enumerate(bands_data):
        band = Band(
            deal_id=deal.id,
            label=bd["label"],
            band_value=bd["value"],
            order_index=i + 1,
            pe_ratio=bd["pe"],
            ev_ebitda=bd["ev"]
        )
        db.add(band)
        db.flush()
        bands.append(band)
    
    # Create investors
    investors_data = [
        {
            "email": "ahmed@investor.com",
            "name": "Ahmed Al-Mansoori",
            "type": InvestorType.HNWI,
            "anchor": False
        },
        {
            "email": "family@alfuttaim.com",
            "name": "Al-Futtaim Family Office",
            "type": InvestorType.FAMILY_OFFICE,
            "anchor": False
        },
        {
            "email": "invest@ewm.ae",
            "name": "Emirates Wealth Mgmt",
            "type": InvestorType.INSTITUTIONAL,
            "anchor": True
        },
        {
            "email": "fund@gulfsovereign.ae",
            "name": "Gulf Sovereign Fund",
            "type": InvestorType.SOVEREIGN,
            "anchor": True
        },
    ]
    
    investors = []
    for inv_data in investors_data:
        # Create user
        inv_user = User(
            email=inv_data["email"],
            password_hash=hash_password("investor123"),
            role=UserRole.INVESTOR,
            display_name=inv_data["name"]
        )
        db.add(inv_user)
        db.flush()
        
        # Create investor profile
        investor = Investor(
            user_id=inv_user.id,
            display_name=inv_data["name"],
            investor_type=inv_data["type"]
        )
        db.add(investor)
        db.flush()
        
        # Create invitation (already accepted)
        invitation = Invitation(
            deal_id=deal.id,
            investor_email=inv_data["email"],
            investor_name=inv_data["name"],
            investor_type=inv_data["type"],
            anchor_potential=inv_data["anchor"],
            token=generate_token(32),
            expires_at=datetime.utcnow() + timedelta(days=30),
            status=InvitationStatus.ACCEPTED,
            accepted_user_id=inv_user.id
        )
        db.add(invitation)
        
        investors.append({
            "user": inv_user,
            "profile": investor,
            "data": inv_data
        })
    
    db.flush()
    
    # Create IOIs
    iois_data = [
        {"investor_idx": 0, "band_idx": 2, "amount": 2500000, "strength": IOIStrength.SOFT, "anchor": False},
        {"investor_idx": 1, "band_idx": 1, "amount": 5000000, "strength": IOIStrength.STRONG, "anchor": False},
        {"investor_idx": 2, "band_idx": 2, "amount": 10000000, "strength": IOIStrength.STRONG, "anchor": True},
        {"investor_idx": 3, "band_idx": 1, "amount": 15000000, "strength": IOIStrength.STRONG, "anchor": True},
    ]
    
    for ioi_data in iois_data:
        ioi = IOI(
            deal_id=deal.id,
            investor_user_id=investors[ioi_data["investor_idx"]]["user"].id,
            band_id=bands[ioi_data["band_idx"]].id,
            amount=ioi_data["amount"],
            strength=ioi_data["strength"],
            anchor_flag=ioi_data["anchor"],
            disclaimer_accepted=True,
            created_at=datetime.utcnow() - timedelta(hours=12 - ioi_data["investor_idx"]),
            investor_note="Looking forward to this opportunity." if ioi_data["investor_idx"] % 2 == 0 else ""
        )
        db.add(ioi)
    
    db.commit()
    
    return {
        "issuer_email": "demo@issuer.com",
        "issuer_password": "demo123",
        "investor_password": "investor123",
        "deal_id": deal.id,
        "deal_name": deal.name,
        "investors": [
            {"email": inv["data"]["email"], "name": inv["data"]["name"]}
            for inv in investors
        ]
    }


def clear_demo_data(db: Session):
    """Clear all demo data"""
    from models import IOIHistory, FeedbackNote, DealDocument
    
    # Delete in order to respect foreign keys
    db.query(IOIHistory).delete()
    db.query(IOI).delete()
    db.query(FeedbackNote).delete()
    db.query(DealDocument).delete()
    db.query(Invitation).delete()
    db.query(Band).delete()
    db.query(Deal).delete()
    db.query(Investor).delete()
    db.query(Issuer).delete()
    db.query(User).delete()
    db.commit()
