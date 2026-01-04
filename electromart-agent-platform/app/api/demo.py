"""
Demo API Endpoints for Database Operations Showcase
Use these endpoints during your demo to show real-time database read/write operations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, timezone

from app.database.connection import get_db
from app.database.models import (
    Customer, Product, Order, Promotion,
    SupportTicket, Conversation
)

router = APIRouter(prefix="/api/demo", tags=["Demo Dashboard"])


@router.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get overall database statistics
    Perfect for showing total records in each table
    """
    try:
        stats = {
            "total_customers": db.query(func.count(Customer.id)).scalar() or 0,
            "total_products": db.query(func.count(Product.id)).scalar() or 0,
            "total_orders": db.query(func.count(Order.id)).scalar() or 0,
            "total_promotions": db.query(func.count(Promotion.id)).scalar() or 0,
            "total_support_tickets": db.query(func.count(SupportTicket.id)).scalar() or 0,
            "total_conversations": db.query(func.count(Conversation.id)).scalar() or 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Order statistics
        order_stats = {
            "pending": db.query(func.count(Order.id)).filter(Order.status == "pending").scalar() or 0,
            "confirmed": db.query(func.count(Order.id)).filter(Order.status == "confirmed").scalar() or 0,
            "shipped": db.query(func.count(Order.id)).filter(Order.status == "shipped").scalar() or 0,
            "delivered": db.query(func.count(Order.id)).filter(Order.status == "delivered").scalar() or 0,
        }

        # Ticket statistics
        ticket_stats = {
            "open": db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "open").scalar() or 0,
            "in_progress": db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "in_progress").scalar() or 0,
            "resolved": db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "resolved").scalar() or 0,
        }

        stats["order_breakdown"] = order_stats
        stats["ticket_breakdown"] = ticket_stats

        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/recent")
async def get_recent_conversations(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent conversations with messages
    Shows READ operation - fetching conversation history from database
    """
    try:
        conversations = (
            db.query(Conversation)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .all()
        )

        result = []
        for conv in conversations:
            result.append({
                "session_id": conv.session_id,
                "current_agent": conv.current_agent,
                "message_count": len(conv.messages) if conv.messages else 0,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                "messages": conv.messages[:3] if conv.messages else []  # Show first 3 messages
            })

        return {"success": True, "data": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/list")
async def get_products(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get product list
    Shows READ operation - fetching product catalog
    """
    try:
        products = db.query(Product).limit(limit).all()

        result = []
        for product in products:
            result.append({
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": float(product.price) if product.price else 0,
                "stock_status": product.stock_status,
                "specs": product.specs
            })

        return {"success": True, "data": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/recent")
async def get_recent_orders(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get recent orders with customer and product details
    Shows READ operation with JOIN - fetching related data
    """
    try:
        orders = (
            db.query(Order)
            .order_by(desc(Order.order_date))
            .limit(limit)
            .all()
        )

        result = []
        for order in orders:
            result.append({
                "order_number": order.order_number,
                "customer": {
                    "name": order.customer.name if order.customer else "Unknown",
                    "email": order.customer.email if order.customer else "Unknown"
                },
                "product": {
                    "name": order.product.name if order.product else "Unknown",
                    "category": order.product.category if order.product else "Unknown"
                },
                "status": order.status,
                "total_amount": float(order.total_amount) if order.total_amount else 0,
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "tracking_number": order.tracking_number
            })

        return {"success": True, "data": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/active")
async def get_active_tickets(db: Session = Depends(get_db)):
    """
    Get active support tickets
    Shows READ operation - fetching support tickets
    """
    try:
        tickets = (
            db.query(SupportTicket)
            .filter(SupportTicket.status.in_(["open", "in_progress"]))
            .order_by(desc(SupportTicket.created_at))
            .limit(15)
            .all()
        )

        result = []
        for ticket in tickets:
            result.append({
                "ticket_number": ticket.ticket_number,
                "customer": ticket.customer.name if ticket.customer else "Unknown",
                "issue_type": ticket.issue_type,
                "status": ticket.status,
                "priority": ticket.priority,
                "description": ticket.description[:100] + "..." if len(ticket.description) > 100 else ticket.description,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None
            })

        return {"success": True, "data": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/promotions/active")
async def get_active_promotions(db: Session = Depends(get_db)):
    """
    Get active promotions
    Shows READ operation - fetching marketing promotions
    """
    try:
        now = datetime.now(timezone.utc)
        promotions = (
            db.query(Promotion)
            .filter(
                Promotion.is_active == True,
                Promotion.start_date <= now,
                Promotion.end_date >= now
            )
            .all()
        )

        result = []
        for promo in promotions:
            result.append({
                "name": promo.name,
                "description": promo.description,
                "discount_percentage": float(promo.discount_percentage) if promo.discount_percentage else 0,
                "promo_code": promo.promo_code,
                "start_date": promo.start_date.isoformat() if promo.start_date else None,
                "end_date": promo.end_date.isoformat() if promo.end_date else None
            })

        return {"success": True, "data": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_demo_dashboard(db: Session = Depends(get_db)):
    """
    Complete dashboard view combining all data
    Perfect single endpoint to show during demo
    """
    try:
        # Get stats
        stats_response = await get_database_stats(db)

        # Get recent activity
        recent_conversations = await get_recent_conversations(5, db)
        recent_orders = await get_recent_orders(5, db)
        active_tickets = await get_active_tickets(db)
        active_promos = await get_active_promotions(db)

        dashboard = {
            "statistics": stats_response["data"],
            "recent_activity": {
                "conversations": recent_conversations["data"],
                "orders": recent_orders["data"][:5],
                "tickets": active_tickets["data"][:5],
                "promotions": active_promos["data"]
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

        return {"success": True, "data": dashboard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
