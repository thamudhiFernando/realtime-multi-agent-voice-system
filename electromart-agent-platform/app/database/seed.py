"""
Database seed script for ElectroMart Multi-Agent System
Populates database with mock data for testing
"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database.connection import init_db, SessionLocal
from app.database.models import Customer, Product, Order, Promotion, SupportTicket
from app.utils.logger import logger

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # points to project root
KNOWLEDGE_DIR = BASE_DIR / "data/knowledge"

# -----------------------------
# Seed Functions
# -----------------------------

def seed_customers(db: Session) -> list:
    """Seed customer data"""
    customers_data = [
        {"name": "John Doe", "email": "john.doe@email.com", "phone": "(555) 111-2222"},
        {"name": "Jane Smith", "email": "jane.smith@email.com", "phone": "(555) 222-3333"},
        {"name": "Bob Johnson", "email": "bob.johnson@email.com", "phone": "(555) 333-4444"},
        {"name": "Alice Williams", "email": "alice.williams@email.com", "phone": "(555) 444-5555"},
        {"name": "Charlie Brown", "email": "charlie.brown@email.com", "phone": "(555) 555-6666"},
    ]

    customers = []
    for data in customers_data:
        customer = Customer(**data)
        db.add(customer)
        customers.append(customer)

    db.commit()
    logger.info(f"Seeded {len(customers)} customers")
    return customers


def seed_products(db: Session) -> list:
    """Seed product data from knowledge base"""
    kb_path = KNOWLEDGE_DIR / "sales_kb.json"
    if not kb_path.exists():
        raise FileNotFoundError(f"Sales KB not found at {kb_path}")

    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    products = []
    for product_data in kb.get("products", []):
        product = Product(
            name=product_data["name"],
            category=product_data["category"],
            price=Decimal(str(product_data["price"])),
            specs=product_data.get("specs", {}),
            stock_status=product_data.get("stock_status", "in_stock"),
            description=product_data.get("description", "")
        )
        db.add(product)
        products.append(product)

    db.commit()
    logger.info(f"Seeded {len(products)} products")
    return products


def seed_orders(db: Session, customers: list, products: list) -> list:
    """Seed order data"""
    orders_data = [
        {"order_number": "ORD001234", "status": "delivered", "tracking_number": "TRK001234XYZ", "days_ago": 15, "delivery_days": 5},
        {"order_number": "ORD001235", "status": "shipped", "tracking_number": "TRK001235XYZ", "days_ago": 3, "delivery_days": 2},
        {"order_number": "ORD001236", "status": "processing", "tracking_number": None, "days_ago": 1, "delivery_days": 5},
        {"order_number": "ORD001237", "status": "out_for_delivery", "tracking_number": "TRK001237XYZ", "days_ago": 5, "delivery_days": 0},
        {"order_number": "ORD001238", "status": "delivered", "tracking_number": "TRK001238XYZ", "days_ago": 30, "delivery_days": 7},
    ]

    orders = []
    for i, data in enumerate(orders_data):
        customer = customers[i % len(customers)]
        product = random.choice(products)

        order = Order(
            order_number=data["order_number"],
            customer_id=customer.id,
            product_id=product.id,
            status=data["status"],
            tracking_number=data["tracking_number"],
            order_date=datetime.now(timezone.utc) - timedelta(days=data["days_ago"]),
            delivery_date=(datetime.now(timezone.utc) - timedelta(days=data["days_ago"]) + timedelta(days=data["delivery_days"]))
                          if data["delivery_days"] is not None else None,
            total_amount=product.price
        )
        db.add(order)
        orders.append(order)

    db.commit()
    logger.info(f"Seeded {len(orders)} orders")
    return orders


def seed_promotions(db: Session) -> list:
    """Seed promotion data from knowledge base"""
    kb_path = KNOWLEDGE_DIR / "marketing_kb.json"
    if not kb_path.exists():
        raise FileNotFoundError(f"Marketing KB not found at {kb_path}")

    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)

    promotions = []
    for promo_data in kb.get("active_promotions", []):
        promotion = Promotion(
            name=promo_data["name"],
            description=promo_data.get("description", ""),
            discount_percentage=Decimal(str(promo_data["discount_percentage"])),
            start_date=datetime.fromisoformat(promo_data["start_date"]),
            end_date=datetime.fromisoformat(promo_data["end_date"]),
            promo_code=promo_data.get("promo_code"),
            is_active=True
        )
        db.add(promotion)
        promotions.append(promotion)

    db.commit()
    logger.info(f"Seeded {len(promotions)} promotions")
    return promotions


def seed_support_tickets(db: Session, customers: list, products: list) -> list:
    """Seed support ticket data"""
    tickets_data = [
        {"ticket_number": "TKT12345678", "issue_type": "technical", "description": "Laptop won't boot up after Windows update", "status": "open", "priority": "high"},
        {"ticket_number": "TKT12345679", "issue_type": "warranty", "description": "Phone screen cracked, checking warranty coverage", "status": "in_progress", "priority": "medium"},
        {"ticket_number": "TKT12345680", "issue_type": "repair", "description": "TV has no picture, backlight issue suspected", "status": "resolved", "priority": "medium"},
        {"ticket_number": "TKT12345681", "issue_type": "setup", "description": "Need help connecting soundbar to TV", "status": "resolved", "priority": "low"},
    ]

    tickets = []
    for i, data in enumerate(tickets_data):
        customer = customers[i % len(customers)]
        product = random.choice(products)

        ticket = SupportTicket(
            ticket_number=data["ticket_number"],
            customer_id=customer.id,
            product_id=product.id,
            issue_type=data["issue_type"],
            description=data["description"],
            status=data["status"],
            priority=data["priority"],
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            resolved_at=(datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))
                         if data["status"] == "resolved" else None)
        )
        db.add(ticket)
        tickets.append(ticket)

    db.commit()
    logger.info(f"Seeded {len(tickets)} support tickets")
    return tickets


# -----------------------------
# Main seed function
# -----------------------------
def seed_database():
    logger.info("Starting database seed...")

    try:
        # Initialize database tables
        init_db()

        # Create session
        db = SessionLocal()

        # Skip if already seeded
        if db.query(Customer).count() > 0:
            logger.info("Database already seeded. Skipping...")
            db.close()
            return

        # Seed all data
        customers = seed_customers(db)
        products = seed_products(db)
        orders = seed_orders(db, customers, products)
        promotions = seed_promotions(db)
        tickets = seed_support_tickets(db, customers, products)

        db.close()

        logger.info("Database seeded successfully!")
        logger.info(f"Total records created:")
        logger.info(f"  - Customers: {len(customers)}")
        logger.info(f"  - Products: {len(products)}")
        logger.info(f"  - Orders: {len(orders)}")
        logger.info(f"  - Promotions: {len(promotions)}")
        logger.info(f"  - Support Tickets: {len(tickets)}")

    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}", exc_info=True)
        raise


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    seed_database()