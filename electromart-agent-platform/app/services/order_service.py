"""
Order Service Layer
Handles all order-related business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database.models import Order
from app.utils.logger import logger


class OrderService:
    """Service for order-related operations"""

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        try:
            return db.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}")
            return None

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        try:
            return db.query(Order).filter(Order.order_number == order_number).first()
        except Exception as e:
            logger.error(f"Error fetching order {order_number}: {str(e)}")
            return None

    @staticmethod
    def get_orders_by_customer(
        db: Session,
        customer_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get all orders for a customer"""
        try:
            return db.query(Order).filter(
                Order.customer_id == customer_id
            ).order_by(Order.order_date.desc()).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching orders for customer {customer_id}: {str(e)}")
            return []

    @staticmethod
    def get_orders_by_status(db: Session, status: str) -> List[Order]:
        """Get all orders with a specific status"""
        try:
            return db.query(Order).filter(Order.status == status).all()
        except Exception as e:
            logger.error(f"Error fetching orders by status {status}: {str(e)}")
            return []

    @staticmethod
    def create_order(
        db: Session,
        order_number: str,
        customer_id: int,
        product_id: int,
        quantity: int,
        total_amount: Decimal,
        status: str = "pending"
    ) -> Optional[Order]:
        """Create a new order"""
        try:
            order = Order(
                order_number=order_number,
                customer_id=customer_id,
                product_id=product_id,
                quantity=quantity,
                total_amount=total_amount,
                status=status
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            logger.info(f"Created order: {order_number}")
            return order
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating order: {str(e)}")
            return None

    @staticmethod
    def update_order_status(
        db: Session,
        order_id: int,
        new_status: str
    ) -> Optional[Order]:
        """Update order status"""
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return None

            order.status = new_status
            db.commit()
            db.refresh(order)
            logger.info(f"Updated status for order {order_id}: {new_status}")
            return order
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating order status {order_id}: {str(e)}")
            return None

    @staticmethod
    def update_tracking_number(
        db: Session,
        order_id: int,
        tracking_number: str
    ) -> Optional[Order]:
        """Update order tracking number"""
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return None

            order.tracking_number = tracking_number
            db.commit()
            db.refresh(order)
            logger.info(f"Updated tracking number for order {order_id}: {tracking_number}")
            return order
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating tracking number {order_id}: {str(e)}")
            return None

    @staticmethod
    def cancel_order(db: Session, order_id: int) -> bool:
        """Cancel an order"""
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False

            # Only allow cancellation if order is pending or processing
            if order.status not in ["pending", "processing"]:
                logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
                return False

            order.status = "cancelled"
            db.commit()
            logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False

    @staticmethod
    def get_order_count_by_status(db: Session, status: str) -> int:
        """Get count of orders by status"""
        try:
            return db.query(Order).filter(Order.status == status).count()
        except Exception as e:
            logger.error(f"Error counting orders by status {status}: {str(e)}")
            return 0
