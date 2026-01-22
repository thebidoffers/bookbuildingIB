"""
Deal Service
Business logic for deal management, bands, IOIs, and reporting
"""

from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    Deal, Band, IOI, IOIHistory, FeedbackNote, DealDocument,
    DealType, DealStatus, IOIStrength, FeedbackScope,
    User, Issuer, Invitation, InvitationStatus, UserRole
)


class DealService:
    """Service class for deal-related operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_deal(
        self,
        issuer_id: int,
        name: str,
        deal_type: DealType,
        target_amount: float,
        currency: str = "AED",
        description: str = "",
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        max_ioi_amount: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Deal]]:
        """Create a new deal"""
        try:
            deal = Deal(
                issuer_id=issuer_id,
                name=name,
                deal_type=deal_type,
                currency=currency,
                target_amount=target_amount,
                description=description,
                status=DealStatus.DRAFT,
                start_at=start_at,
                end_at=end_at,
                max_ioi_amount=max_ioi_amount
            )
            self.db.add(deal)
            self.db.commit()
            return True, "Deal created successfully", deal
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
    
    def update_deal(self, deal_id: int, **kwargs) -> Tuple[bool, str]:
        """Update deal properties"""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return False, "Deal not found"
        
        try:
            for key, value in kwargs.items():
                if hasattr(deal, key):
                    setattr(deal, key, value)
            self.db.commit()
            return True, "Deal updated successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def add_band(
        self,
        deal_id: int,
        label: str,
        band_value: float,
        order_index: int,
        pe_ratio: str = "",
        ev_ebitda: str = ""
    ) -> Tuple[bool, str, Optional[Band]]:
        """Add a pricing band to a deal"""
        try:
            band = Band(
                deal_id=deal_id,
                label=label,
                band_value=band_value,
                order_index=order_index,
                pe_ratio=pe_ratio,
                ev_ebitda=ev_ebitda
            )
            self.db.add(band)
            self.db.commit()
            return True, "Band added successfully", band
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
    
    def get_deal_bands(self, deal_id: int) -> List[Band]:
        """Get all bands for a deal, ordered by index"""
        return self.db.query(Band).filter(
            Band.deal_id == deal_id
        ).order_by(Band.order_index).all()
    
    def delete_band(self, band_id: int) -> Tuple[bool, str]:
        """Delete a band (only if no IOIs exist for it)"""
        band = self.db.query(Band).filter(Band.id == band_id).first()
        if not band:
            return False, "Band not found"
        
        ioi_count = self.db.query(IOI).filter(IOI.band_id == band_id).count()
        if ioi_count > 0:
            return False, "Cannot delete band with existing IOIs"
        
        try:
            self.db.delete(band)
            self.db.commit()
            return True, "Band deleted successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def open_deal(self, deal_id: int) -> Tuple[bool, str]:
        """Open a deal for IOI submissions"""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return False, "Deal not found"
        
        # Validate deal has bands
        band_count = self.db.query(Band).filter(Band.deal_id == deal_id).count()
        if band_count < 3:
            return False, "Deal must have at least 3 bands before opening"
        if band_count > 7:
            return False, "Deal cannot have more than 7 bands"
        
        deal.status = DealStatus.OPEN
        if not deal.start_at:
            deal.start_at = datetime.utcnow()
        self.db.commit()
        return True, "Deal opened successfully"
    
    def close_deal(self, deal_id: int) -> Tuple[bool, str]:
        """Close a deal for IOI submissions"""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return False, "Deal not found"
        
        deal.status = DealStatus.CLOSED
        deal.closed_at = datetime.utcnow()
        self.db.commit()
        return True, "Deal closed successfully"
    
    def submit_ioi(
        self,
        deal_id: int,
        investor_user_id: int,
        band_id: int,
        amount: float,
        strength: IOIStrength = IOIStrength.SOFT,
        anchor_flag: bool = False,
        investor_note: str = "",
        disclaimer_accepted: bool = True
    ) -> Tuple[bool, str, Optional[IOI]]:
        """Submit or update an IOI"""
        # Validate deal is open
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return False, "Deal not found", None
        if deal.status != DealStatus.OPEN:
            return False, "Deal is not open for IOIs", None
        
        # Validate band belongs to deal
        band = self.db.query(Band).filter(Band.id == band_id, Band.deal_id == deal_id).first()
        if not band:
            return False, "Invalid band for this deal", None
        
        # Validate amount
        if amount <= 0:
            return False, "IOI amount must be positive", None
        if deal.max_ioi_amount and amount > deal.max_ioi_amount:
            return False, f"IOI amount exceeds maximum of {deal.currency} {deal.max_ioi_amount:,.0f}", None
        
        # Check for existing IOI for this band
        existing = self.db.query(IOI).filter(
            IOI.deal_id == deal_id,
            IOI.investor_user_id == investor_user_id,
            IOI.band_id == band_id,
            IOI.is_active == True
        ).first()
        
        try:
            if existing:
                # Log history before update
                history = IOIHistory(
                    ioi_id=existing.id,
                    amount=existing.amount,
                    strength=existing.strength,
                    anchor_flag=existing.anchor_flag,
                    investor_note=existing.investor_note,
                    change_type="update"
                )
                self.db.add(history)
                
                # Update existing IOI
                existing.amount = amount
                existing.strength = strength
                existing.anchor_flag = anchor_flag
                existing.investor_note = investor_note
                existing.updated_at = datetime.utcnow()
                self.db.commit()
                return True, "IOI updated successfully", existing
            else:
                # Create new IOI
                ioi = IOI(
                    deal_id=deal_id,
                    investor_user_id=investor_user_id,
                    band_id=band_id,
                    amount=amount,
                    strength=strength,
                    anchor_flag=anchor_flag,
                    investor_note=investor_note,
                    disclaimer_accepted=disclaimer_accepted
                )
                self.db.add(ioi)
                self.db.flush()
                
                # Log creation
                history = IOIHistory(
                    ioi_id=ioi.id,
                    amount=amount,
                    strength=strength,
                    anchor_flag=anchor_flag,
                    investor_note=investor_note,
                    change_type="create"
                )
                self.db.add(history)
                self.db.commit()
                return True, "IOI submitted successfully", ioi
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
    
    def delete_ioi(self, ioi_id: int, investor_user_id: int) -> Tuple[bool, str]:
        """Soft delete an IOI (mark as inactive)"""
        ioi = self.db.query(IOI).filter(
            IOI.id == ioi_id,
            IOI.investor_user_id == investor_user_id
        ).first()
        
        if not ioi:
            return False, "IOI not found"
        
        deal = self.db.query(Deal).filter(Deal.id == ioi.deal_id).first()
        if deal.status != DealStatus.OPEN:
            return False, "Cannot modify IOIs when deal is not open"
        
        try:
            # Log deletion
            history = IOIHistory(
                ioi_id=ioi.id,
                amount=ioi.amount,
                strength=ioi.strength,
                anchor_flag=ioi.anchor_flag,
                investor_note=ioi.investor_note,
                change_type="delete"
            )
            self.db.add(history)
            
            ioi.is_active = False
            self.db.commit()
            return True, "IOI deleted successfully"
        except Exception as e:
            self.db.rollback()
            return False, str(e)
    
    def get_investor_iois(self, deal_id: int, investor_user_id: int) -> List[IOI]:
        """Get all active IOIs for an investor in a deal"""
        return self.db.query(IOI).filter(
            IOI.deal_id == deal_id,
            IOI.investor_user_id == investor_user_id,
            IOI.is_active == True
        ).all()
    
    def get_all_deal_iois(self, deal_id: int) -> List[IOI]:
        """Get all active IOIs for a deal (issuer view)"""
        return self.db.query(IOI).filter(
            IOI.deal_id == deal_id,
            IOI.is_active == True
        ).all()
    
    def get_demand_summary(self, deal_id: int) -> Dict[str, Any]:
        """Get aggregated demand summary for a deal"""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return {}
        
        bands = self.get_deal_bands(deal_id)
        iois = self.get_all_deal_iois(deal_id)
        
        # Calculate totals
        total_demand = sum(ioi.amount for ioi in iois)
        total_bids = len(iois)
        
        # Demand by band
        demand_by_band = {}
        for band in bands:
            band_iois = [ioi for ioi in iois if ioi.band_id == band.id]
            band_demand = sum(ioi.amount for ioi in band_iois)
            coverage = band_demand / deal.target_amount if deal.target_amount > 0 else 0
            demand_by_band[band.id] = {
                "label": band.label,
                "band_value": band.band_value,
                "order_index": band.order_index,
                "demand": band_demand,
                "bid_count": len(band_iois),
                "coverage": coverage
            }
        
        return {
            "deal": deal,
            "total_demand": total_demand,
            "total_bids": total_bids,
            "overall_coverage": total_demand / deal.target_amount if deal.target_amount > 0 else 0,
            "demand_by_band": demand_by_band,
            "bands": bands
        }
    
    def set_indicative_range(
        self,
        deal_id: int,
        low_band_id: int,
        high_band_id: int,
        description: str = ""
    ) -> Tuple[bool, str]:
        """Set the indicative price/yield range (must be adjacent bands)"""
        deal = self.db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return False, "Deal not found"
        
        # Get bands
        low_band = self.db.query(Band).filter(Band.id == low_band_id).first()
        high_band = self.db.query(Band).filter(Band.id == high_band_id).first()
        
        if not low_band or not high_band:
            return False, "Invalid bands"
        
        if low_band.deal_id != deal_id or high_band.deal_id != deal_id:
            return False, "Bands must belong to this deal"
        
        # Check adjacency
        if abs(low_band.order_index - high_band.order_index) != 1:
            return False, "Selected bands must be adjacent"
        
        # Ensure low is actually lower
        if low_band.order_index > high_band.order_index:
            low_band, high_band = high_band, low_band
        
        deal.indicative_range_low_band_id = low_band.id
        deal.indicative_range_high_band_id = high_band.id
        deal.indicative_range_description = description
        self.db.commit()
        
        return True, "Indicative range set successfully"
    
    def add_feedback_note(
        self,
        deal_id: int,
        user_id: int,
        note_text: str,
        scope: FeedbackScope = FeedbackScope.GENERAL,
        scope_id: Optional[int] = None
    ) -> Tuple[bool, str, Optional[FeedbackNote]]:
        """Add a feedback note"""
        try:
            note = FeedbackNote(
                deal_id=deal_id,
                created_by_user_id=user_id,
                scope=scope,
                scope_id=scope_id,
                note_text=note_text
            )
            self.db.add(note)
            self.db.commit()
            return True, "Note added successfully", note
        except Exception as e:
            self.db.rollback()
            return False, str(e), None
    
    def get_feedback_notes(self, deal_id: int) -> List[FeedbackNote]:
        """Get all feedback notes for a deal"""
        return self.db.query(FeedbackNote).filter(
            FeedbackNote.deal_id == deal_id
        ).order_by(FeedbackNote.created_at.desc()).all()
    
    def get_deal_investors(self, deal_id: int) -> List[Dict]:
        """Get all investors invited to a deal with their invitation status"""
        invitations = self.db.query(Invitation).filter(
            Invitation.deal_id == deal_id
        ).all()
        
        result = []
        for inv in invitations:
            investor_data = {
                "invitation_id": inv.id,
                "email": inv.investor_email,
                "name": inv.investor_name,
                "type": inv.investor_type.value if inv.investor_type else "Other",
                "anchor_potential": inv.anchor_potential,
                "status": inv.status.value,
                "token": inv.token,
                "user_id": inv.accepted_user_id
            }
            result.append(investor_data)
        return result
