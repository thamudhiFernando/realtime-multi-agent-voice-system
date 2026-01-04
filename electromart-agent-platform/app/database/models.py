"""
Database models for ElectroMart Multi-Agent System
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Customer(Base):
    """Customer model"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    orders = relationship("Order", back_populates="customer")
    support_tickets = relationship("SupportTicket", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")


class Product(Base):
    """Product model"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    specs = Column(JSON)  # Store specifications as JSON
    stock_status = Column(String(50), default="in_stock")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    orders = relationship("Order", back_populates="product")
    support_tickets = relationship("SupportTicket", back_populates="product")


class Order(Base):
    """Order model"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, confirmed, shipped, delivered, cancelled
    tracking_number = Column(String(100))
    order_date = Column(DateTime, default=datetime.now(timezone.utc))
    delivery_date = Column(DateTime, nullable=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product", back_populates="orders")


class Promotion(Base):
    """Promotion model"""
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    discount_percentage = Column(DECIMAL(5, 2))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    promo_code = Column(String(50), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class SupportTicket(Base):
    """Support ticket model"""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    issue_type = Column(String(100))  # technical, warranty, repair, setup
    description = Column(Text, nullable=False)
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="support_tickets")
    product = relationship("Product", back_populates="support_tickets")


class Conversation(Base):
    """Conversation model for storing chat history"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    messages = Column(JSON, default=list)  # Store messages as JSON array
    current_agent = Column(String(50))  # current active agent
    context = Column(JSON, default=dict)  # Store conversation context
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Relationships
    customer = relationship("Customer", back_populates="conversations")
