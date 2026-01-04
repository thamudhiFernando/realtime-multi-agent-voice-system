"""
Product Service Layer
Handles all product-related business logic
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.database.models import Product
from app.utils.logger import logger


class ProductService:
    """Service for product-related operations"""

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        try:
            return db.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None

    @staticmethod
    def get_all_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        in_stock_only: bool = False
    ) -> List[Product]:
        """Get all products with optional filtering"""
        try:
            query = db.query(Product)

            if category:
                query = query.filter(Product.category == category)

            if in_stock_only:
                query = query.filter(Product.stock_status == "in_stock")

            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            return []

    @staticmethod
    def search_products(
        db: Session,
        query: str,
        category: Optional[str] = None
    ) -> List[Product]:
        """Search products by name or description"""
        try:
            search = db.query(Product).filter(
                (Product.name.ilike(f"%{query}%")) |
                (Product.description.ilike(f"%{query}%"))
            )

            if category:
                search = search.filter(Product.category == category)

            return search.all()
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    @staticmethod
    def get_products_by_category(db: Session, category: str) -> List[Product]:
        """Get all products in a specific category"""
        try:
            return db.query(Product).filter(Product.category == category).all()
        except Exception as e:
            logger.error(f"Error fetching products by category {category}: {str(e)}")
            return []

    @staticmethod
    def create_product(
        db: Session,
        name: str,
        category: str,
        price: Decimal,
        description: Optional[str] = None,
        specs: Optional[dict] = None,
        stock_status: str = "in_stock"
    ) -> Optional[Product]:
        """Create a new product"""
        try:
            product = Product(
                name=name,
                category=category,
                price=price,
                description=description,
                specs=specs,
                stock_status=stock_status
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            logger.info(f"Created product: {name}")
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating product: {str(e)}")
            return None

    @staticmethod
    def update_product_stock(
        db: Session,
        product_id: int,
        stock_status: str
    ) -> Optional[Product]:
        """Update product stock status"""
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None

            product.stock_status = stock_status
            db.commit()
            db.refresh(product)
            logger.info(f"Updated stock status for product {product_id}: {stock_status}")
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating product stock {product_id}: {str(e)}")
            return None

    @staticmethod
    def update_product_price(
        db: Session,
        product_id: int,
        new_price: Decimal
    ) -> Optional[Product]:
        """Update product price"""
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None

            product.price = new_price
            db.commit()
            db.refresh(product)
            logger.info(f"Updated price for product {product_id}: {new_price}")
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating product price {product_id}: {str(e)}")
            return None

    @staticmethod
    def get_available_categories(db: Session) -> List[str]:
        """Get all unique product categories"""
        try:
            categories = db.query(Product.category).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
