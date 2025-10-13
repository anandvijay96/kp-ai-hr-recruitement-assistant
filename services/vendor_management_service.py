"""Vendor management service"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from models.database import (
    Vendor, VendorContract, VendorPerformanceReview, 
    VendorComplianceDocument, VendorCommunication,
    VendorNotification, VendorJobAssignment, VendorAnalytics, User
)
from models.vendor_schemas import (
    VendorCreateRequest, VendorUpdateRequest, VendorDeactivateRequest,
    ContractCreateRequest, ContractUpdateRequest,
    PerformanceReviewCreateRequest, PerformanceReviewUpdateRequest,
    ComplianceDocumentCreateRequest, ComplianceDocumentUpdateRequest,
    CommunicationCreateRequest, JobAssignmentCreateRequest, JobAssignmentUpdateRequest
)

logger = logging.getLogger(__name__)


class VendorManagementService:
    """Service for managing vendors"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    # ========================================================================
    # VENDOR OPERATIONS
    # ========================================================================
    
    async def generate_vendor_code(self) -> str:
        """
        Generate unique vendor code in format VEN-YYYY-XXXX
        
        Returns:
            Vendor code string
        """
        try:
            year = datetime.now().year
            prefix = f"VEN-{year}-"
            
            # Get count of vendors created this year
            query = select(func.count(Vendor.id)).where(
                Vendor.vendor_code.like(f"{prefix}%")
            )
            result = await self.db.execute(query)
            count = result.scalar() or 0
            
            return f"{prefix}{(count + 1):04d}"
            
        except Exception as e:
            logger.error(f"Error generating vendor code: {e}")
            # Fallback to timestamp-based code
            import time
            return f"VEN-{year}-{int(time.time() % 10000):04d}"
    
    async def check_duplicate_vendor(
        self, 
        name: str, 
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate vendors by name or email
        
        Args:
            name: Vendor name
            email: Contact email
            
        Returns:
            Duplicate vendor info or None
        """
        try:
            # Check by exact name match (case-insensitive)
            query = select(Vendor).where(
                and_(
                    func.lower(Vendor.name) == name.lower(),
                    Vendor.status != 'blacklisted'
                )
            )
            
            result = await self.db.execute(query)
            existing_vendor = result.scalar_one_or_none()
            
            if existing_vendor:
                return {
                    "id": existing_vendor.id,
                    "name": existing_vendor.name,
                    "vendor_code": existing_vendor.vendor_code,
                    "match_type": "exact_name"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking duplicate vendor: {e}")
            return None
    
    async def create_vendor(
        self, 
        data: VendorCreateRequest, 
        current_user: User
    ) -> Vendor:
        """
        Create a new vendor
        
        Args:
            data: Vendor creation data
            current_user: Current authenticated user
            
        Returns:
            Created vendor
            
        Raises:
            ValueError: If duplicate vendor exists
        """
        try:
            # Check for duplicates
            duplicate = await self.check_duplicate_vendor(
                data.name, 
                data.contact_email
            )
            if duplicate:
                raise ValueError(
                    f"Vendor with similar name already exists: {duplicate['vendor_code']}"
                )
            
            # Generate vendor code
            vendor_code = await self.generate_vendor_code()
            
            # Create vendor
            vendor = Vendor(
                vendor_code=vendor_code,
                name=data.name,
                service_category=data.service_category.value,
                contact_person=data.contact_person,
                contact_email=data.contact_email,
                contact_phone=data.contact_phone,
                alternate_contact=data.alternate_contact,
                website=data.website,
                address=data.address,
                city=data.city,
                state=data.state,
                country=data.country,
                postal_code=data.postal_code,
                tax_id=data.tax_id,
                vendor_manager_id=data.vendor_manager_id,
                created_by=current_user.id,
                status='active',
                compliance_status='pending'
            )
            
            self.db.add(vendor)
            await self.db.commit()
            await self.db.refresh(vendor)
            
            logger.info(f"Created vendor {vendor.vendor_code} by user {current_user.email}")
            return vendor
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating vendor: {e}")
            raise
    
    async def get_vendor_by_id(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        try:
            query = select(Vendor).where(Vendor.id == vendor_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting vendor {vendor_id}: {e}")
            return None
    
    async def update_vendor(
        self,
        vendor_id: str,
        data: VendorUpdateRequest,
        current_user: User
    ) -> Vendor:
        """
        Update vendor information
        
        Args:
            vendor_id: Vendor ID
            data: Update data
            current_user: Current user
            
        Returns:
            Updated vendor
            
        Raises:
            ValueError: If vendor not found
        """
        try:
            vendor = await self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Update fields
            update_data = data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(vendor, field):
                    if field == 'service_category' and value:
                        setattr(vendor, field, value.value)
                    elif field == 'status' and value:
                        setattr(vendor, field, value.value)
                    else:
                        setattr(vendor, field, value)
            
            vendor.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(vendor)
            
            logger.info(f"Updated vendor {vendor.vendor_code} by user {current_user.email}")
            return vendor
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating vendor {vendor_id}: {e}")
            raise
    
    async def deactivate_vendor(
        self,
        vendor_id: str,
        data: VendorDeactivateRequest,
        current_user: User
    ) -> Vendor:
        """Deactivate a vendor"""
        try:
            vendor = await self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            vendor.status = 'inactive'
            vendor.deactivated_at = datetime.now()
            vendor.deactivation_reason = data.reason
            
            await self.db.commit()
            await self.db.refresh(vendor)
            
            logger.info(f"Deactivated vendor {vendor.vendor_code} by user {current_user.email}")
            return vendor
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deactivating vendor {vendor_id}: {e}")
            raise
    
    async def list_vendors(
        self,
        status: Optional[str] = None,
        service_category: Optional[str] = None,
        vendor_manager_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List vendors with filters and pagination
        
        Args:
            status: Filter by status
            service_category: Filter by service category
            vendor_manager_id: Filter by vendor manager
            search: Search term for name/code
            page: Page number
            limit: Items per page
            
        Returns:
            Dictionary with vendors and pagination info
        """
        try:
            query = select(Vendor)
            
            # Apply filters
            if status:
                query = query.where(Vendor.status == status)
            if service_category:
                query = query.where(Vendor.service_category == service_category)
            if vendor_manager_id:
                query = query.where(Vendor.vendor_manager_id == vendor_manager_id)
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Vendor.name.ilike(search_term),
                        Vendor.vendor_code.ilike(search_term),
                        Vendor.contact_email.ilike(search_term)
                    )
                )
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = (await self.db.execute(count_query)).scalar()
            
            # Apply pagination
            offset = (page - 1) * limit
            query = query.order_by(Vendor.created_at.desc()).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            vendors = result.scalars().all()
            
            return {
                "vendors": vendors,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if total > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing vendors: {e}")
            raise
    
    async def get_vendor_dashboard_stats(self) -> Dict[str, int]:
        """Get dashboard statistics for vendors"""
        try:
            # Total vendors
            total_vendors = (await self.db.execute(
                select(func.count(Vendor.id))
            )).scalar()
            
            # Active vendors
            active_vendors = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.status == 'active')
            )).scalar()
            
            # Inactive vendors
            inactive_vendors = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.status == 'inactive')
            )).scalar()
            
            # Blacklisted vendors
            blacklisted_vendors = (await self.db.execute(
                select(func.count(Vendor.id)).where(Vendor.status == 'blacklisted')
            )).scalar()
            
            # Total contracts
            total_contracts = (await self.db.execute(
                select(func.count(VendorContract.id))
            )).scalar()
            
            # Active contracts
            active_contracts = (await self.db.execute(
                select(func.count(VendorContract.id)).where(
                    VendorContract.status == 'active'
                )
            )).scalar()
            
            # Expiring contracts (within 30 days)
            expiry_date = date.today() + timedelta(days=30)
            expiring_contracts = (await self.db.execute(
                select(func.count(VendorContract.id)).where(
                    and_(
                        VendorContract.status == 'active',
                        VendorContract.end_date <= expiry_date,
                        VendorContract.end_date >= date.today()
                    )
                )
            )).scalar()
            
            # Expired documents
            expired_documents = (await self.db.execute(
                select(func.count(VendorComplianceDocument.id)).where(
                    VendorComplianceDocument.status == 'expired'
                )
            )).scalar()
            
            # Pending reviews
            pending_reviews = (await self.db.execute(
                select(func.count(VendorPerformanceReview.id)).where(
                    VendorPerformanceReview.status == 'draft'
                )
            )).scalar()
            
            # Compliance alerts
            compliance_alerts = (await self.db.execute(
                select(func.count(Vendor.id)).where(
                    Vendor.compliance_status.in_(['non_compliant', 'under_review'])
                )
            )).scalar()
            
            return {
                "total_vendors": total_vendors or 0,
                "active_vendors": active_vendors or 0,
                "inactive_vendors": inactive_vendors or 0,
                "blacklisted_vendors": blacklisted_vendors or 0,
                "total_contracts": total_contracts or 0,
                "active_contracts": active_contracts or 0,
                "expiring_contracts": expiring_contracts or 0,
                "expired_documents": expired_documents or 0,
                "pending_reviews": pending_reviews or 0,
                "compliance_alerts": compliance_alerts or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor dashboard stats: {e}")
            raise
    
    # ========================================================================
    # CONTRACT OPERATIONS
    # ========================================================================
    
    async def generate_contract_number(self, vendor_id: str) -> str:
        """Generate unique contract number"""
        try:
            vendor = await self.get_vendor_by_id(vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            year = datetime.now().year
            prefix = f"{vendor.vendor_code}-CON-{year}-"
            
            # Get count of contracts for this vendor this year
            query = select(func.count(VendorContract.id)).where(
                and_(
                    VendorContract.vendor_id == vendor_id,
                    VendorContract.contract_number.like(f"{prefix}%")
                )
            )
            result = await self.db.execute(query)
            count = result.scalar() or 0
            
            return f"{prefix}{(count + 1):04d}"
            
        except Exception as e:
            logger.error(f"Error generating contract number: {e}")
            raise
    
    async def create_contract(
        self,
        data: ContractCreateRequest,
        current_user: User
    ) -> VendorContract:
        """Create a new vendor contract"""
        try:
            # Verify vendor exists
            vendor = await self.get_vendor_by_id(data.vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Generate contract number
            contract_number = await self.generate_contract_number(data.vendor_id)
            
            # Create contract
            contract = VendorContract(
                vendor_id=data.vendor_id,
                contract_number=contract_number,
                contract_type=data.contract_type,
                title=data.title,
                description=data.description,
                contract_value=data.contract_value,
                currency=data.currency,
                start_date=data.start_date,
                end_date=data.end_date,
                payment_terms=data.payment_terms,
                renewal_terms=data.renewal_terms,
                file_url=data.file_url,
                file_name=data.file_name,
                file_size=data.file_size,
                auto_renew=data.auto_renew,
                renewal_notice_days=data.renewal_notice_days,
                created_by=current_user.id,
                status='draft',
                approval_status='pending'
            )
            
            self.db.add(contract)
            
            # Update vendor contract count
            vendor.total_contracts += 1
            
            await self.db.commit()
            await self.db.refresh(contract)
            
            logger.info(f"Created contract {contract.contract_number} by user {current_user.email}")
            return contract
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating contract: {e}")
            raise
    
    async def get_vendor_contracts(
        self,
        vendor_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[VendorContract]:
        """Get contracts for a vendor"""
        try:
            query = select(VendorContract).where(
                VendorContract.vendor_id == vendor_id
            )
            
            if status:
                query = query.where(VendorContract.status == status)
            
            query = query.order_by(VendorContract.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting vendor contracts: {e}")
            return []
    
    # ========================================================================
    # PERFORMANCE REVIEW OPERATIONS
    # ========================================================================
    
    async def create_performance_review(
        self,
        data: PerformanceReviewCreateRequest,
        current_user: User
    ) -> VendorPerformanceReview:
        """Create a performance review for a vendor"""
        try:
            # Verify vendor exists
            vendor = await self.get_vendor_by_id(data.vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Calculate overall rating
            ratings = [
                data.service_quality_rating,
                data.timeliness_rating,
                data.communication_rating,
                data.cost_effectiveness_rating,
                data.compliance_rating
            ]
            overall_rating = sum(ratings) / len(ratings)
            
            # Create review
            review = VendorPerformanceReview(
                vendor_id=data.vendor_id,
                review_period=data.review_period,
                review_date=data.review_date,
                review_type=data.review_type,
                service_quality_rating=data.service_quality_rating,
                timeliness_rating=data.timeliness_rating,
                communication_rating=data.communication_rating,
                cost_effectiveness_rating=data.cost_effectiveness_rating,
                compliance_rating=data.compliance_rating,
                overall_rating=f"{overall_rating:.2f}",
                strengths=data.strengths,
                areas_for_improvement=data.areas_for_improvement,
                recommendations=data.recommendations,
                written_feedback=data.written_feedback,
                reviewed_by=current_user.id,
                status='draft'
            )
            
            self.db.add(review)
            await self.db.commit()
            await self.db.refresh(review)
            
            logger.info(f"Created performance review for vendor {vendor.vendor_code}")
            return review
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating performance review: {e}")
            raise
    
    async def get_vendor_reviews(
        self,
        vendor_id: str,
        limit: int = 10
    ) -> List[VendorPerformanceReview]:
        """Get performance reviews for a vendor"""
        try:
            query = select(VendorPerformanceReview).where(
                VendorPerformanceReview.vendor_id == vendor_id
            ).order_by(VendorPerformanceReview.review_date.desc()).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting vendor reviews: {e}")
            return []
    
    # ========================================================================
    # COMPLIANCE DOCUMENT OPERATIONS
    # ========================================================================
    
    async def create_compliance_document(
        self,
        data: ComplianceDocumentCreateRequest,
        current_user: User
    ) -> VendorComplianceDocument:
        """Create a compliance document for a vendor"""
        try:
            # Verify vendor exists
            vendor = await self.get_vendor_by_id(data.vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Determine document status based on expiry date
            status = 'valid'
            if data.expiry_date:
                days_to_expiry = (data.expiry_date - date.today()).days
                if days_to_expiry < 0:
                    status = 'expired'
                elif days_to_expiry <= 30:
                    status = 'expiring_soon'
            
            # Create document
            document = VendorComplianceDocument(
                vendor_id=data.vendor_id,
                document_type=data.document_type,
                document_name=data.document_name,
                document_number=data.document_number,
                issue_date=data.issue_date,
                expiry_date=data.expiry_date,
                issuing_authority=data.issuing_authority,
                file_url=data.file_url,
                file_name=data.file_name,
                file_size=data.file_size,
                notes=data.notes,
                uploaded_by=current_user.id,
                status=status,
                verification_status='pending'
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            logger.info(f"Created compliance document for vendor {vendor.vendor_code}")
            return document
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating compliance document: {e}")
            raise
    
    async def get_vendor_compliance_documents(
        self,
        vendor_id: str
    ) -> List[VendorComplianceDocument]:
        """Get compliance documents for a vendor"""
        try:
            query = select(VendorComplianceDocument).where(
                VendorComplianceDocument.vendor_id == vendor_id
            ).order_by(VendorComplianceDocument.uploaded_at.desc())
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting vendor compliance documents: {e}")
            return []
    
    # ========================================================================
    # COMMUNICATION OPERATIONS
    # ========================================================================
    
    async def create_communication(
        self,
        data: CommunicationCreateRequest,
        current_user: User
    ) -> VendorCommunication:
        """Log a communication with a vendor"""
        try:
            # Verify vendor exists
            vendor = await self.get_vendor_by_id(data.vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Create communication
            communication = VendorCommunication(
                vendor_id=data.vendor_id,
                communication_type=data.communication_type.value,
                communication_date=data.communication_date,
                subject=data.subject,
                details=data.details,
                attendees=data.attendees,
                outcome=data.outcome,
                follow_up_required=data.follow_up_required,
                follow_up_date=data.follow_up_date,
                follow_up_notes=data.follow_up_notes,
                tags=data.tags,
                is_important=data.is_important,
                logged_by=current_user.id
            )
            
            self.db.add(communication)
            await self.db.commit()
            await self.db.refresh(communication)
            
            logger.info(f"Logged communication for vendor {vendor.vendor_code}")
            return communication
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating communication: {e}")
            raise
    
    # ========================================================================
    # JOB ASSIGNMENT OPERATIONS
    # ========================================================================
    
    async def create_job_assignment(
        self,
        data: JobAssignmentCreateRequest,
        current_user: User
    ) -> VendorJobAssignment:
        """Assign a job to a vendor"""
        try:
            # Verify vendor exists
            vendor = await self.get_vendor_by_id(data.vendor_id)
            if not vendor:
                raise ValueError("Vendor not found")
            
            # Create assignment
            assignment = VendorJobAssignment(
                vendor_id=data.vendor_id,
                job_id=data.job_id,
                contract_id=data.contract_id,
                assignment_date=data.assignment_date,
                fee_structure=data.fee_structure,
                fee_amount=data.fee_amount,
                notes=data.notes,
                status='active'
            )
            
            self.db.add(assignment)
            await self.db.commit()
            await self.db.refresh(assignment)
            
            logger.info(f"Assigned job {data.job_id} to vendor {vendor.vendor_code}")
            return assignment
            
        except ValueError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job assignment: {e}")
            raise
