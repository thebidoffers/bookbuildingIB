"""
Authentication Module
Handles user registration, login, password hashing, and session management
"""

import bcrypt
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from models import User, UserRole, Issuer, Investor, Invitation, InvitationStatus, InvestorType


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(length: int = 32) -> str:
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def register_issuer(
    db: Session,
    email: str,
    password: str,
    org_name: str,
    display_name: Optional[str] = None
) -> Tuple[bool, str, Optional[User]]:
    """
    Register a new issuer user
    Returns: (success, message, user)
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        return False, "Email already registered", None
    
    # Create user
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=UserRole.ISSUER,
        display_name=display_name or org_name
    )
    db.add(user)
    db.flush()  # Get user.id
    
    # Create issuer profile
    issuer = Issuer(
        org_name=org_name,
        owner_user_id=user.id
    )
    db.add(issuer)
    db.commit()
    
    return True, "Issuer registered successfully", user


def register_investor_from_invitation(
    db: Session,
    token: str,
    password: str,
    display_name: Optional[str] = None
) -> Tuple[bool, str, Optional[User]]:
    """
    Register a new investor user from an invitation token
    Returns: (success, message, user)
    """
    # Find and validate invitation
    invitation = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.status == InvitationStatus.PENDING
    ).first()
    
    if not invitation:
        return False, "Invalid or expired invitation", None
    
    if invitation.expires_at < datetime.utcnow():
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        return False, "Invitation has expired", None
    
    # Check if email already registered
    existing = db.query(User).filter(User.email == invitation.investor_email.lower()).first()
    if existing:
        # Link existing user to invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_user_id = existing.id
        db.commit()
        return True, "Existing user linked to invitation", existing
    
    # Create new user
    user = User(
        email=invitation.investor_email.lower(),
        password_hash=hash_password(password),
        role=UserRole.INVESTOR,
        display_name=display_name or invitation.investor_name or invitation.investor_email
    )
    db.add(user)
    db.flush()
    
    # Create investor profile
    investor = Investor(
        user_id=user.id,
        display_name=display_name or invitation.investor_name,
        investor_type=invitation.investor_type
    )
    db.add(investor)
    
    # Update invitation
    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_user_id = user.id
    db.commit()
    
    return True, "Investor registered successfully", user


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Tuple[bool, str, Optional[User]]:
    """
    Authenticate a user with email and password
    Returns: (success, message, user)
    """
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user:
        return False, "Invalid email or password", None
    
    if not verify_password(password, user.password_hash):
        return False, "Invalid email or password", None
    
    return True, "Login successful", user


def create_invitation(
    db: Session,
    deal_id: int,
    investor_email: str,
    investor_name: str,
    investor_type: InvestorType,
    anchor_potential: bool = False,
    expires_days: int = 7
) -> Tuple[bool, str, Optional[Invitation]]:
    """
    Create an invitation for an investor to join a deal
    Returns: (success, message, invitation)
    """
    # Check if already invited
    existing = db.query(Invitation).filter(
        Invitation.deal_id == deal_id,
        Invitation.investor_email == investor_email.lower()
    ).first()
    
    if existing:
        if existing.status == InvitationStatus.PENDING:
            return False, "Investor already invited", None
        elif existing.status == InvitationStatus.ACCEPTED:
            return False, "Investor already joined this deal", None
    
    # Count existing invitations for this deal
    invite_count = db.query(Invitation).filter(
        Invitation.deal_id == deal_id
    ).count()
    
    if invite_count >= 10:
        return False, "Maximum of 10 investors per deal reached", None
    
    # Create invitation
    invitation = Invitation(
        deal_id=deal_id,
        investor_email=investor_email.lower(),
        investor_name=investor_name,
        investor_type=investor_type,
        anchor_potential=anchor_potential,
        token=generate_token(32),
        expires_at=datetime.utcnow() + timedelta(days=expires_days)
    )
    db.add(invitation)
    db.commit()
    
    return True, "Invitation created successfully", invitation


def validate_invitation_token(db: Session, token: str) -> Tuple[bool, str, Optional[Invitation]]:
    """
    Validate an invitation token
    Returns: (valid, message, invitation)
    """
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    
    if not invitation:
        return False, "Invalid invitation token", None
    
    if invitation.status == InvitationStatus.ACCEPTED:
        return False, "Invitation already used", invitation
    
    if invitation.expires_at < datetime.utcnow():
        if invitation.status != InvitationStatus.EXPIRED:
            invitation.status = InvitationStatus.EXPIRED
            db.commit()
        return False, "Invitation has expired", invitation
    
    return True, "Valid invitation", invitation


def get_user_deals(db: Session, user: User) -> list:
    """Get all deals accessible to a user based on their role"""
    from models import Deal
    
    if user.role == UserRole.ISSUER:
        # Issuer sees their own deals
        issuer = db.query(Issuer).filter(Issuer.owner_user_id == user.id).first()
        if issuer:
            return db.query(Deal).filter(Deal.issuer_id == issuer.id).all()
        return []
    else:
        # Investor sees deals they're invited to
        invitations = db.query(Invitation).filter(
            Invitation.accepted_user_id == user.id,
            Invitation.status == InvitationStatus.ACCEPTED
        ).all()
        deal_ids = [inv.deal_id for inv in invitations]
        return db.query(Deal).filter(Deal.id.in_(deal_ids)).all() if deal_ids else []


def can_access_deal(db: Session, user: User, deal_id: int) -> bool:
    """Check if a user can access a specific deal"""
    from models import Deal
    
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        return False
    
    if user.role == UserRole.ISSUER:
        issuer = db.query(Issuer).filter(Issuer.owner_user_id == user.id).first()
        return issuer and deal.issuer_id == issuer.id
    else:
        invitation = db.query(Invitation).filter(
            Invitation.deal_id == deal_id,
            Invitation.accepted_user_id == user.id,
            Invitation.status == InvitationStatus.ACCEPTED
        ).first()
        return invitation is not None
