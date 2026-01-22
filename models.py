"""
Database Models for Early-Look Bookbuilding MVP
SQLAlchemy ORM models for all entities
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    Enum, create_engine, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    ISSUER = "issuer"
    INVESTOR = "investor"


class DealType(enum.Enum):
    EQUITY = "equity"
    DEBT = "debt"


class DealStatus(enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class InvestorType(enum.Enum):
    INSTITUTIONAL = "Institutional"
    FAMILY_OFFICE = "Family Office"
    HNWI = "HNWI"
    SOVEREIGN = "Sovereign"
    OTHER = "Other"


class IOIStrength(enum.Enum):
    SOFT = "Soft"
    STRONG = "Strong"


class FeedbackScope(enum.Enum):
    INVESTOR = "investor"
    BAND = "band"
    GENERAL = "general"


class User(Base):
    """User table for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    display_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    issuer_profile = relationship("Issuer", back_populates="owner", uselist=False)
    investor_profile = relationship("Investor", back_populates="user", uselist=False)
    iois = relationship("IOI", back_populates="investor")
    feedback_notes = relationship("FeedbackNote", back_populates="created_by")


class Issuer(Base):
    """Issuer organization profile"""
    __tablename__ = "issuers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    org_name = Column(String(255), nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="issuer_profile")
    deals = relationship("Deal", back_populates="issuer")


class Deal(Base):
    """Deal room for a capital raise"""
    __tablename__ = "deals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    issuer_id = Column(Integer, ForeignKey("issuers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    deal_type = Column(Enum(DealType), nullable=False)
    currency = Column(String(10), default="AED")
    target_amount = Column(Float, nullable=False)
    status = Column(Enum(DealStatus), default=DealStatus.DRAFT)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    max_ioi_amount = Column(Float)  # Optional max IOI per investor
    description = Column(Text)  # Deal description
    
    # Final indicative range selection
    indicative_range_low_band_id = Column(Integer, ForeignKey("bands.id"))
    indicative_range_high_band_id = Column(Integer, ForeignKey("bands.id"))
    indicative_range_description = Column(Text)
    
    # Relationships
    issuer = relationship("Issuer", back_populates="deals")
    bands = relationship("Band", back_populates="deal", foreign_keys="Band.deal_id")
    invitations = relationship("Invitation", back_populates="deal")
    iois = relationship("IOI", back_populates="deal")
    feedback_notes = relationship("FeedbackNote", back_populates="deal")
    documents = relationship("DealDocument", back_populates="deal")


class Band(Base):
    """Price/Yield bands for a deal"""
    __tablename__ = "bands"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    label = Column(String(50), nullable=False)  # e.g., "Price 1", "Yield 1"
    band_value = Column(Float, nullable=False)  # Valuation or yield %
    order_index = Column(Integer, nullable=False)  # For ordering bands
    
    # Optional display fields for equity
    pe_ratio = Column(String(50))
    ev_ebitda = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship("Deal", back_populates="bands", foreign_keys=[deal_id])
    iois = relationship("IOI", back_populates="band")
    
    __table_args__ = (
        UniqueConstraint('deal_id', 'order_index', name='unique_deal_band_order'),
    )


class Invitation(Base):
    """Investor invitations to deals"""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    investor_email = Column(String(255), nullable=False)
    investor_name = Column(String(255))
    investor_type = Column(Enum(InvestorType), default=InvestorType.INSTITUTIONAL)
    anchor_potential = Column(Boolean, default=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)
    accepted_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship("Deal", back_populates="invitations")
    accepted_user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('deal_id', 'investor_email', name='unique_deal_investor_email'),
    )


class Investor(Base):
    """Investor profile linked to user"""
    __tablename__ = "investors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    display_name = Column(String(255))
    investor_type = Column(Enum(InvestorType), default=InvestorType.INSTITUTIONAL)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="investor_profile")


class IOI(Base):
    """Indication of Interest submissions"""
    __tablename__ = "iois"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    investor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False)
    amount = Column(Float, nullable=False)
    strength = Column(Enum(IOIStrength), default=IOIStrength.SOFT)
    anchor_flag = Column(Boolean, default=False)
    investor_note = Column(Text)
    disclaimer_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # For soft delete / versioning
    
    # Relationships
    deal = relationship("Deal", back_populates="iois")
    investor = relationship("User", back_populates="iois")
    band = relationship("Band", back_populates="iois")
    
    __table_args__ = (
        UniqueConstraint('deal_id', 'investor_user_id', 'band_id', 'is_active', 
                        name='unique_active_ioi_per_band'),
    )


class IOIHistory(Base):
    """Audit trail for IOI changes"""
    __tablename__ = "ioi_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ioi_id = Column(Integer, ForeignKey("iois.id"), nullable=False)
    amount = Column(Float, nullable=False)
    strength = Column(Enum(IOIStrength))
    anchor_flag = Column(Boolean)
    investor_note = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_type = Column(String(20))  # 'create', 'update', 'delete'


class FeedbackNote(Base):
    """Issuer feedback notes"""
    __tablename__ = "feedback_notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scope = Column(Enum(FeedbackScope), default=FeedbackScope.GENERAL)
    scope_id = Column(Integer)  # investor_user_id or band_id depending on scope
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship("Deal", back_populates="feedback_notes")
    created_by = relationship("User", back_populates="feedback_notes")


class DealDocument(Base):
    """Uploaded documents for deals"""
    __tablename__ = "deal_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pitch_deck, term_summary, financials, other
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    deal = relationship("Deal", back_populates="documents")
