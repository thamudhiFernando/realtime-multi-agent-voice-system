"""
Customer Service Layer
Handles all customer-related business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.models import Customer
from app.utils.logger import logger


class CustomerService:
    """Service for customer-related operations"""

    @staticmethod
    def get_customer_by_id(db: Session, customer_id: int) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            return db.query(Customer).filter(Customer.id == customer_id).first()
        except Exception as e:
            logger.error(f"Error fetching customer {customer_id}: {str(e)}")
            return None

    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
        """Get customer by email"""
        try:
            return db.query(Customer).filter(Customer.email == email).first()
        except Exception as e:
            logger.error(f"Error fetching customer by email {email}: {str(e)}")
            return None

    @staticmethod
    def get_all_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get all customers with pagination"""
        try:
            return db.query(Customer).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching customers: {str(e)}")
            return []

    @staticmethod
    def create_customer(
        db: Session,
        name: str,
        email: str,
        phone: Optional[str] = None
    ) -> Optional[Customer]:
        """Create a new customer"""
        try:
            customer = Customer(
                name=name,
                email=email,
                phone=phone
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            logger.info(f"Created customer: {email}")
            return customer
        except IntegrityError:
            db.rollback()
            logger.warning(f"Customer with email {email} already exists")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating customer: {str(e)}")
            return None

    @staticmethod
    def update_customer(
        db: Session,
        customer_id: int,
        name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[Customer]:
        """Update customer information"""
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None

            if name:
                customer.name = name
            if phone:
                customer.phone = phone

            db.commit()
            db.refresh(customer)
            logger.info(f"Updated customer: {customer_id}")
            return customer
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating customer {customer_id}: {str(e)}")
            return None

    @staticmethod
    def delete_customer(db: Session, customer_id: int) -> bool:
        """Delete a customer"""
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False

            db.delete(customer)
            db.commit()
            logger.info(f"Deleted customer: {customer_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting customer {customer_id}: {str(e)}")
            return False

    @staticmethod
    def search_customers(db: Session, query: str) -> List[Customer]:
        """Search customers by name or email"""
        try:
            return db.query(Customer).filter(
                (Customer.name.ilike(f"%{query}%")) |
                (Customer.email.ilike(f"%{query}%"))
            ).all()
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []
