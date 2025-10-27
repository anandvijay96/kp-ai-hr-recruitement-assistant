"""Vendor Management Service"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from datetime import datetime
from decimal import Decimal

from models.vendor_models import Vendor, CandidateVendor
from models.vendor_schemas import (
    VendorCreate, VendorUpdate, VendorFilter,
    CandidateVendorCreate, CandidateVendorUpdate
)

logger = logging.getLogger(__name__)


class VendorService:
    """Service for managing vendors and candidate-vendor relationships"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============================================================================
    # VENDOR CRUD OPERATIONS
    # ============================================================================
    
    async def create_vendor(self, vendor_data: VendorCreate, created_by: str) -> Vendor:
        """Create a new vendor"""
        try:
            # Check if vendor with same name already exists
            existing = await self.db.execute(
                select(Vendor).where(Vendor.company_name == vendor_data.company_name)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Vendor with name {vendor_data.company_name} already exists")
            
            # Create vendor
            vendor = Vendor(
                **vendor_data.model_dump(),
                created_by=created_by,
                status="active"
            )
            
            self.db.add(vendor)
            await self.db.commit()
            await self.db.refresh(vendor)
            
            logger.info(f"Created vendor: {vendor.company_name} (ID: {vendor.id})")
            return vendor
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating vendor: {str(e)}")
            raise
    
    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        try:
            result = await self.db.execute(
                select(Vendor)
                .where(Vendor.id == vendor_id)
                .where(Vendor.is_deleted == False)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting vendor: {str(e)}")
            raise
    
    async def update_vendor(self, vendor_id: str, vendor_data: VendorUpdate, updated_by: str) -> Vendor:
        """Update vendor"""
        try:
            vendor = await self.get_vendor(vendor_id)
            if not vendor:
                raise ValueError(f"Vendor not found: {vendor_id}")
            
            # Update fields
            update_data = vendor_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(vendor, field, value)
            
            vendor.updated_by = updated_by
            
            await self.db.commit()
            await self.db.refresh(vendor)
            
            logger.info(f"Updated vendor: {vendor.company_name} (ID: {vendor_id})")
            return vendor
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating vendor: {str(e)}")
            raise
    
    async def delete_vendor(self, vendor_id: str, deleted_by: str) -> bool:
        """Delete vendor (soft delete)"""
        try:
            vendor = await self.get_vendor(vendor_id)
            if not vendor:
                raise ValueError(f"Vendor not found: {vendor_id}")
            
            vendor.is_deleted = True
            vendor.deleted_at = datetime.utcnow()
            vendor.deleted_by = deleted_by
            
            await self.db.commit()
            
            logger.info(f"Deleted vendor: {vendor.company_name} (ID: {vendor_id})")
            return True
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting vendor: {str(e)}")
            raise
    
    async def search_vendors(
        self,
        filters: VendorFilter,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search and filter vendors"""
        try:
            # Build base query
            query = select(Vendor).where(Vendor.is_deleted == False)
            filter_conditions = []
            
            # Search query
            if filters.search_query:
                search_term = f"%{filters.search_query}%"
                filter_conditions.append(
                    or_(
                        Vendor.company_name.ilike(search_term),
                        Vendor.contact_email.ilike(search_term),
                        Vendor.contact_person.ilike(search_term),
                        Vendor.city.ilike(search_term),
                        Vendor.industry_specialization.ilike(search_term)
                    )
                )
            
            # Status filter
            if filters.status:
                filter_conditions.append(Vendor.status.in_(filters.status))
            
            # Vendor type filter
            if filters.vendor_type:
                filter_conditions.append(Vendor.vendor_type.in_(filters.vendor_type))
            
            # Industry filter
            if filters.industry:
                filter_conditions.append(Vendor.industry_specialization.ilike(f"%{filters.industry}%"))
            
            # City filter
            if filters.city:
                filter_conditions.append(Vendor.city.ilike(f"%{filters.city}%"))
            
            # Country filter
            if filters.country:
                filter_conditions.append(Vendor.country.ilike(f"%{filters.country}%"))
            
            # Portal access filter
            if filters.has_portal_access is not None:
                filter_conditions.append(Vendor.has_portal_access == filters.has_portal_access)
            
            # Apply filters
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
            
            # Get total count
            count_query = select(func.count(Vendor.id)).where(Vendor.is_deleted == False)
            if filter_conditions:
                count_query = count_query.filter(and_(*filter_conditions))
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # Apply sorting
            sort_column_map = {
                'created_at': Vendor.created_at,
                'updated_at': Vendor.updated_at,
                'company_name': Vendor.company_name,
                'status': Vendor.status,
                'success_rate': Vendor.success_rate
            }
            sort_column = sort_column_map.get(filters.sort_by, Vendor.created_at)
            
            if filters.sort_order == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            vendors = result.scalars().all()
            
            # Format results
            vendor_list = []
            for vendor in vendors:
                # Get candidate counts
                candidates_count = await self._get_vendor_candidate_count(vendor.id)
                active_candidates_count = await self._get_vendor_active_candidate_count(vendor.id)
                
                vendor_dict = {
                    **vendor.__dict__,
                    'candidates_count': candidates_count,
                    'active_candidates_count': active_candidates_count
                }
                vendor_list.append(vendor_dict)
            
            return {
                "vendors": vendor_list,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Error searching vendors: {str(e)}")
            raise
    
    async def _get_vendor_candidate_count(self, vendor_id: str) -> int:
        """Get count of candidates linked to vendor"""
        try:
            result = await self.db.execute(
                select(func.count(CandidateVendor.id))
                .where(CandidateVendor.vendor_id == vendor_id)
            )
            return result.scalar() or 0
        except:
            return 0
    
    async def _get_vendor_active_candidate_count(self, vendor_id: str) -> int:
        """Get count of active candidates linked to vendor"""
        try:
            result = await self.db.execute(
                select(func.count(CandidateVendor.id))
                .where(CandidateVendor.vendor_id == vendor_id)
                .where(CandidateVendor.candidate_status.in_(['referred', 'screened', 'submitted']))
            )
            return result.scalar() or 0
        except:
            return 0
    
    # ============================================================================
    # CANDIDATE-VENDOR LINKING OPERATIONS
    # ============================================================================
    
    async def link_candidate_to_vendor(
        self,
        link_data: CandidateVendorCreate,
        created_by: str
    ) -> CandidateVendor:
        """Link a candidate to a vendor"""
        try:
            # Check if vendor exists
            vendor = await self.get_vendor(link_data.vendor_id)
            if not vendor:
                raise ValueError(f"Vendor not found: {link_data.vendor_id}")
            
            # Check if link already exists
            existing = await self.db.execute(
                select(CandidateVendor).where(
                    CandidateVendor.candidate_id == link_data.candidate_id,
                    CandidateVendor.vendor_id == link_data.vendor_id
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError("Candidate is already linked to this vendor")
            
            # Create link
            link = CandidateVendor(
                **link_data.model_dump(),
                created_by=created_by
            )
            
            self.db.add(link)
            
            # Update vendor metrics
            vendor.total_candidates_referred += 1
            
            await self.db.commit()
            await self.db.refresh(link)
            
            # Recalculate success rate
            await self._update_vendor_metrics(link_data.vendor_id)
            
            logger.info(f"Linked candidate {link_data.candidate_id} to vendor {link_data.vendor_id}")
            return link
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error linking candidate to vendor: {str(e)}")
            raise
    
    async def update_candidate_vendor_link(
        self,
        link_id: str,
        link_data: CandidateVendorUpdate
    ) -> CandidateVendor:
        """Update candidate-vendor relationship"""
        try:
            result = await self.db.execute(
                select(CandidateVendor).where(CandidateVendor.id == link_id)
            )
            link = result.scalar_one_or_none()
            
            if not link:
                raise ValueError(f"Candidate-vendor link not found: {link_id}")
            
            # Update fields
            update_data = link_data.model_dump(exclude_unset=True)
            old_status = link.candidate_status
            
            for field, value in update_data.items():
                setattr(link, field, value)
            
            await self.db.commit()
            await self.db.refresh(link)
            
            # Update vendor metrics if status changed
            if 'candidate_status' in update_data and update_data['candidate_status'] != old_status:
                await self._update_vendor_metrics(link.vendor_id)
            
            logger.info(f"Updated candidate-vendor link: {link_id}")
            return link
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating candidate-vendor link: {str(e)}")
            raise
    
    async def get_vendor_candidates(self, vendor_id: str) -> List[CandidateVendor]:
        """Get all candidates linked to a vendor"""
        try:
            result = await self.db.execute(
                select(CandidateVendor)
                .where(CandidateVendor.vendor_id == vendor_id)
                .order_by(CandidateVendor.referral_date.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting vendor candidates: {str(e)}")
            raise
    
    async def _update_vendor_metrics(self, vendor_id: str):
        """Update vendor performance metrics"""
        try:
            vendor = await self.get_vendor(vendor_id)
            if not vendor:
                return
            
            # Get total candidates referred
            total_result = await self.db.execute(
                select(func.count(CandidateVendor.id))
                .where(CandidateVendor.vendor_id == vendor_id)
            )
            vendor.total_candidates_referred = total_result.scalar() or 0
            
            # Get hired candidates
            hired_result = await self.db.execute(
                select(func.count(CandidateVendor.id))
                .where(CandidateVendor.vendor_id == vendor_id)
                .where(CandidateVendor.candidate_status == 'hired')
            )
            vendor.candidates_hired = hired_result.scalar() or 0
            
            # Calculate success rate
            if vendor.total_candidates_referred > 0:
                vendor.success_rate = Decimal(
                    (vendor.candidates_hired / vendor.total_candidates_referred) * 100
                ).quantize(Decimal('0.01'))
            else:
                vendor.success_rate = Decimal('0.00')
            
            # Calculate average rating
            rating_result = await self.db.execute(
                select(func.avg(CandidateVendor.vendor_rating))
                .where(CandidateVendor.vendor_id == vendor_id)
                .where(CandidateVendor.vendor_rating.isnot(None))
            )
            avg_rating = rating_result.scalar()
            if avg_rating:
                vendor.average_rating = Decimal(str(avg_rating)).quantize(Decimal('0.01'))
            
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating vendor metrics: {str(e)}")
    
    # ============================================================================
    # STATISTICS
    # ============================================================================
    
    async def get_vendor_statistics(self) -> Dict[str, Any]:
        """Get overall vendor statistics"""
        try:
            # Total vendors
            total_result = await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.is_deleted == False)
            )
            total_vendors = total_result.scalar() or 0
            
            # Active vendors
            active_result = await self.db.execute(
                select(func.count(Vendor.id))
                .where(Vendor.is_deleted == False)
                .where(Vendor.status == 'active')
            )
            active_vendors = active_result.scalar() or 0
            
            # Inactive vendors
            inactive_result = await self.db.execute(
                select(func.count(Vendor.id))
                .where(Vendor.is_deleted == False)
                .where(Vendor.status == 'inactive')
            )
            inactive_vendors = inactive_result.scalar() or 0
            
            # Suspended vendors
            suspended_result = await self.db.execute(
                select(func.count(Vendor.id))
                .where(Vendor.is_deleted == False)
                .where(Vendor.status == 'suspended')
            )
            suspended_vendors = suspended_result.scalar() or 0
            
            # Total candidates referred
            candidates_result = await self.db.execute(
                select(func.sum(Vendor.total_candidates_referred))
                .where(Vendor.is_deleted == False)
            )
            total_candidates_referred = candidates_result.scalar() or 0
            
            # Total candidates hired
            hired_result = await self.db.execute(
                select(func.sum(Vendor.candidates_hired))
                .where(Vendor.is_deleted == False)
            )
            total_candidates_hired = hired_result.scalar() or 0
            
            # Overall success rate
            if total_candidates_referred > 0:
                overall_success_rate = Decimal(
                    (total_candidates_hired / total_candidates_referred) * 100
                ).quantize(Decimal('0.01'))
            else:
                overall_success_rate = Decimal('0.00')
            
            # Average vendor rating
            avg_rating_result = await self.db.execute(
                select(func.avg(Vendor.average_rating))
                .where(Vendor.is_deleted == False)
                .where(Vendor.average_rating.isnot(None))
            )
            avg_rating = avg_rating_result.scalar()
            average_vendor_rating = Decimal(str(avg_rating)).quantize(Decimal('0.01')) if avg_rating else None
            
            return {
                "total_vendors": total_vendors,
                "active_vendors": active_vendors,
                "inactive_vendors": inactive_vendors,
                "suspended_vendors": suspended_vendors,
                "total_candidates_referred": int(total_candidates_referred),
                "total_candidates_hired": int(total_candidates_hired),
                "overall_success_rate": overall_success_rate,
                "average_vendor_rating": average_vendor_rating
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor statistics: {str(e)}")
            raise
