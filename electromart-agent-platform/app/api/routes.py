"""
REST API routes for ElectroMart Multi-Agent System
Enhanced with analytics and handoff management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.connection import get_db
from app.database.models import Product, Order, Promotion
from app.utils import logger
from app.utils.analytics import get_analytics
from app.utils.human_handoff import get_handoff_manager

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "electromart-agents"}


@router.get("/products")
async def get_products(
    category: str = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get products list

    Args:
        category: Optional category filter
        db: Database session

    Returns:
        List of products
    """
    try:
        query = db.query(Product)

        if category:
            query = query.filter(Product.category == category)

        products = query.all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": float(p.price),
                "stock_status": p.stock_status
            }
            for p in products
        ]

    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")


@router.get("/orders/{order_number}")
async def get_order(
    order_number: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get order by order number

    Args:
        order_number: Order number
        db: Database session

    Returns:
        Order details
    """
    try:
        order = db.query(Order).filter(Order.order_number == order_number).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return {
            "order_number": order.order_number,
            "status": order.status,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "tracking_number": order.tracking_number,
            "total_amount": float(order.total_amount)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch order")


@router.get("/promotions")
async def get_promotions(
    active_only: bool = True,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get promotions list

    Args:
        active_only: Return only active promotions
        db: Database session

    Returns:
        List of promotions
    """
    try:
        query = db.query(Promotion)

        if active_only:
            query = query.filter(Promotion.is_active == True)

        promotions = query.all()

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "discount_percentage": float(p.discount_percentage) if p.discount_percentage else 0,
                "promo_code": p.promo_code,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None
            }
            for p in promotions
        ]

    except Exception as e:
        logger.error(f"Error fetching promotions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch promotions")


# ============================================================================
# BONUS FEATURES: Analytics and Human Handoff Endpoints
# ============================================================================

@router.get("/analytics/agents")
async def get_agent_analytics() -> Dict[str, Any]:
    """
    Get performance analytics for all agents

    Returns:
        Dictionary with statistics for each agent including:
        - Total requests
        - Success rate
        - Average response time
        - Min/max response times
    """
    try:
        analytics = await get_analytics()
        stats = await analytics.get_all_agents_stats()

        return {
            "status": "success",
            "data": stats,
            "message": "Agent analytics retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error fetching agent analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent analytics")


@router.get("/analytics/agents/{agent_name}")
async def get_agent_analytics_detail(agent_name: str) -> Dict[str, Any]:
    """
    Get detailed performance analytics for a specific agent

    Args:
        agent_name: Name of the agent (orchestrator, sales, marketing, support, logistics)

    Returns:
        Detailed statistics for the specified agent
    """
    try:
        analytics = await get_analytics()
        stats = await analytics.get_agent_stats(agent_name)

        if not stats or stats.get("total_requests", 0) == 0:
            return {
                "status": "success",
                "data": stats,
                "message": f"No analytics data available for {agent_name}"
            }

        return {
            "status": "success",
            "data": stats,
            "message": f"Analytics for {agent_name} retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error fetching analytics for {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics for {agent_name}")


@router.get("/handoff/queue")
async def get_handoff_queue_stats() -> Dict[str, Any]:
    """
    Get statistics about human handoff queue

    Returns:
        Queue statistics including:
        - Total queued requests
        - Count by priority level
    """
    try:
        handoff_manager = await get_handoff_manager()
        stats = await handoff_manager.get_queue_stats()

        return {
            "status": "success",
            "data": stats,
            "message": "Handoff queue statistics retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error fetching handoff queue stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch handoff queue statistics")


@router.get("/handoff/next")
async def get_next_handoff(human_agent_id: str) -> Dict[str, Any]:
    """
    Get next handoff request from queue for human agent

    Args:
        human_agent_id: ID of the human agent requesting work

    Returns:
        Next handoff request or null if queue is empty
    """
    try:
        if not human_agent_id:
            raise HTTPException(status_code=400, detail="human_agent_id is required")

        handoff_manager = await get_handoff_manager()
        handoff = await handoff_manager.get_next_handoff(human_agent_id)

        if not handoff:
            return {
                "status": "success",
                "data": None,
                "message": "No handoff requests in queue"
            }

        return {
            "status": "success",
            "data": handoff,
            "message": f"Handoff assigned to {human_agent_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next handoff: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get next handoff")
