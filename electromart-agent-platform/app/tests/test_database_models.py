"""
Unit tests for database models
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.database.models import Customer, Product, Order, Promotion, SupportTicket, Conversation


class TestCustomerModel:
    """Test suite for Customer model"""

    def test_create_customer_successfully(self, test_database_session, sample_customer_data):
        """Test creating a customer with valid data"""
        customer = Customer(**sample_customer_data)
        test_database_session.add(customer)
        test_database_session.commit()

        assert customer.id is not None
        assert customer.name == sample_customer_data["name"]
        assert customer.email == sample_customer_data["email"]
        assert customer.phone == sample_customer_data["phone"]
        assert isinstance(customer.created_at, datetime)

    def test_customer_email_is_unique(self, test_database_session, sample_customer_data):
        """Test that customer email must be unique"""
        # Create first customer
        customer1 = Customer(**sample_customer_data)
        test_database_session.add(customer1)
        test_database_session.commit()

        # Try to create second customer with same email
        customer2 = Customer(**sample_customer_data)
        test_database_session.add(customer2)

        with pytest.raises(Exception):  # IntegrityError or similar
            test_database_session.commit()

    def test_customer_has_relationships(self, test_database_session, sample_customer_data):
        """Test that customer has relationship attributes"""
        customer = Customer(**sample_customer_data)
        test_database_session.add(customer)
        test_database_session.commit()

        # Check relationships exist (even if empty)
        assert hasattr(customer, 'orders')
        assert hasattr(customer, 'support_tickets')
        assert hasattr(customer, 'conversations')


class TestProductModel:
    """Test suite for Product model"""

    def test_create_product_successfully(self, test_database_session, sample_product_data):
        """Test creating a product with valid data"""
        product = Product(**sample_product_data)
        test_database_session.add(product)
        test_database_session.commit()

        assert product.id is not None
        assert product.name == sample_product_data["name"]
        assert product.category == sample_product_data["category"]
        assert product.price == Decimal(str(sample_product_data["price"]))
        assert product.specs == sample_product_data["specs"]
        assert product.stock_status == "in_stock"

    def test_product_price_is_decimal(self, test_database_session):
        """Test that product price is stored as Decimal"""
        product = Product(
            name="Test Product",
            category="Test",
            price=99.99,
            stock_status="in_stock"
        )
        test_database_session.add(product)
        test_database_session.commit()

        assert isinstance(product.price, Decimal)

    def test_product_specs_stored_as_json(self, test_database_session):
        """Test that product specs are stored as JSON"""
        specs = {"processor": "Intel i7", "ram": "16GB", "storage": "512GB"}
        product = Product(
            name="Test Laptop",
            category="Laptops",
            price=1299.99,
            specs=specs,
            stock_status="in_stock"
        )
        test_database_session.add(product)
        test_database_session.commit()

        # Retrieve and verify
        retrieved_product = test_database_session.query(Product).filter_by(id=product.id).first()
        assert retrieved_product.specs == specs
        assert retrieved_product.specs["processor"] == "Intel i7"


class TestOrderModel:
    """Test suite for Order model"""

    def test_create_order_with_relationships(
        self,
        test_database_session,
        sample_customer_data,
        sample_product_data,
        sample_order_data
    ):
        """Test creating an order with customer and product relationships"""
        # Create customer and product first
        customer = Customer(**sample_customer_data)
        product = Product(**sample_product_data)
        test_database_session.add(customer)
        test_database_session.add(product)
        test_database_session.commit()

        # Create order
        order = Order(
            **sample_order_data,
            customer_id=customer.id,
            product_id=product.id,
            order_date=datetime.now(timezone.utc),
            delivery_date=datetime.now(timezone.utc) + timedelta(days=5)
        )
        test_database_session.add(order)
        test_database_session.commit()

        assert order.id is not None
        assert order.customer_id == customer.id
        assert order.product_id == product.id
        assert order.order_number == "TEST001"

    def test_order_has_customer_relationship(
        self,
        test_database_session,
        sample_customer_data,
        sample_product_data,
        sample_order_data
    ):
        """Test that order can access customer through relationship"""
        customer = Customer(**sample_customer_data)
        product = Product(**sample_product_data)
        test_database_session.add_all([customer, product])
        test_database_session.commit()

        order = Order(
            **sample_order_data,
            customer_id=customer.id,
            product_id=product.id
        )
        test_database_session.add(order)
        test_database_session.commit()

        # Access customer through relationship
        assert order.customer.name == sample_customer_data["name"]
        assert order.customer.email == sample_customer_data["email"]

    def test_order_number_is_unique(self, test_database_session, sample_customer_data, sample_product_data):
        """Test that order number must be unique"""
        customer = Customer(**sample_customer_data)
        product = Product(**sample_product_data)
        test_database_session.add_all([customer, product])
        test_database_session.commit()

        # Create first order
        order1 = Order(
            order_number="UNIQUE001",
            customer_id=customer.id,
            product_id=product.id,
            status="processing",
            total_amount=100.00
        )
        test_database_session.add(order1)
        test_database_session.commit()

        # Try to create second order with same order number
        order2 = Order(
            order_number="UNIQUE001",
            customer_id=customer.id,
            product_id=product.id,
            status="processing",
            total_amount=200.00
        )
        test_database_session.add(order2)

        with pytest.raises(Exception):
            test_database_session.commit()


class TestPromotionModel:
    """Test suite for Promotion model"""

    def test_create_promotion_successfully(self, test_database_session):
        """Test creating a promotion with valid data"""
        promotion = Promotion(
            name="Summer Sale",
            description="Great summer discounts",
            discount_percentage=Decimal("15.00"),
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            promo_code="SUMMER15",
            is_active=True
        )
        test_database_session.add(promotion)
        test_database_session.commit()

        assert promotion.id is not None
        assert promotion.name == "Summer Sale"
        assert promotion.discount_percentage == Decimal("15.00")
        assert promotion.is_active is True

    def test_promotion_promo_code_is_unique(self, test_database_session):
        """Test that promo code must be unique"""
        promo1 = Promotion(
            name="Promo 1",
            discount_percentage=10.00,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=10),
            promo_code="UNIQUE10",
            is_active=True
        )
        test_database_session.add(promo1)
        test_database_session.commit()

        promo2 = Promotion(
            name="Promo 2",
            discount_percentage=20.00,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=10),
            promo_code="UNIQUE10",
            is_active=True
        )
        test_database_session.add(promo2)

        with pytest.raises(Exception):
            test_database_session.commit()


class TestSupportTicketModel:
    """Test suite for SupportTicket model"""

    def test_create_support_ticket(
        self,
        test_database_session,
        sample_customer_data,
        sample_product_data
    ):
        """Test creating a support ticket"""
        customer = Customer(**sample_customer_data)
        product = Product(**sample_product_data)
        test_database_session.add_all([customer, product])
        test_database_session.commit()

        ticket = SupportTicket(
            ticket_number="TKT001",
            customer_id=customer.id,
            product_id=product.id,
            issue_type="technical",
            description="Product not working",
            status="open",
            priority="high"
        )
        test_database_session.add(ticket)
        test_database_session.commit()

        assert ticket.id is not None
        assert ticket.ticket_number == "TKT001"
        assert ticket.status == "open"
        assert ticket.priority == "high"

    def test_support_ticket_has_timestamps(
        self,
        test_database_session,
        sample_customer_data,
        sample_product_data
    ):
        """Test that support ticket has created_at timestamp"""
        customer = Customer(**sample_customer_data)
        product = Product(**sample_product_data)
        test_database_session.add_all([customer, product])
        test_database_session.commit()

        ticket = SupportTicket(
            ticket_number="TKT002",
            customer_id=customer.id,
            product_id=product.id,
            issue_type="warranty",
            description="Need warranty info",
            status="open"
        )
        test_database_session.add(ticket)
        test_database_session.commit()

        assert isinstance(ticket.created_at, datetime)
        assert ticket.resolved_at is None  # Not resolved yet


class TestConversationModel:
    """Test suite for Conversation model"""

    def test_create_conversation(self, test_database_session, sample_customer_data):
        """Test creating a conversation"""
        customer = Customer(**sample_customer_data)
        test_database_session.add(customer)
        test_database_session.commit()

        conversation = Conversation(
            session_id="session-123",
            customer_id=customer.id,
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            current_agent="sales",
            context={"intent": "sales"}
        )
        test_database_session.add(conversation)
        test_database_session.commit()

        assert conversation.id is not None
        assert conversation.session_id == "session-123"
        assert len(conversation.messages) == 2

    def test_conversation_messages_stored_as_json(self, test_database_session):
        """Test that conversation messages are stored as JSON"""
        conversation = Conversation(
            session_id="session-456",
            messages=[
                {"role": "user", "content": "Show me laptops"},
                {"role": "assistant", "content": "Here are the laptops", "agent": "sales"}
            ],
            current_agent="sales"
        )
        test_database_session.add(conversation)
        test_database_session.commit()

        # Retrieve and verify
        retrieved = test_database_session.query(Conversation).filter_by(
            session_id="session-456"
        ).first()

        assert retrieved.messages[0]["role"] == "user"
        assert retrieved.messages[1]["agent"] == "sales"

    def test_conversation_has_timestamps(self, test_database_session):
        """Test that conversation has created_at and updated_at timestamps"""
        conversation = Conversation(
            session_id="session-789",
            messages=[],
            current_agent="orchestrator"
        )
        test_database_session.add(conversation)
        test_database_session.commit()

        assert isinstance(conversation.created_at, datetime)
        assert isinstance(conversation.updated_at, datetime)
