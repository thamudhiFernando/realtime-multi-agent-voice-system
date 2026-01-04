"""
Pytest configuration and fixtures for ElectroMart testing
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_database_session():
    """
    Create a test database session with in-memory SQLite

    Yields:
        Session: Test database session
    """
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    # Create session
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        "name": "Test Customer",
        "email": "test@example.com",
        "phone": "(555) 123-4567"
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "name": "Test Laptop",
        "category": "Laptops",
        "price": 999.99,
        "specs": {"ram": "16GB", "storage": "512GB SSD"},
        "stock_status": "in_stock",
        "description": "Test laptop for testing purposes"
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "order_number": "TEST001",
        "status": "processing",
        "tracking_number": "TRACK123",
        "total_amount": 999.99
    }


@pytest.fixture
def mock_conversation_state():
    """Mock conversation state for testing"""
    from ..graph.state import create_initial_conversation_state
    return create_initial_conversation_state(
        session_id="test-session-123",
        customer_id=1
    )


@pytest.fixture
def sample_user_messages():
    """Sample user messages for testing intent classification"""
    return {
        "sales": [
            "What's the price of iPhone 15?",
            "Do you have gaming laptops?",
            "Show me TVs under $1000"
        ],
        "marketing": [
            "Are there any discounts available?",
            "Tell me about your loyalty program",
            "Do you have any Black Friday deals?"
        ],
        "support": [
            "My laptop won't turn on",
            "I need help with warranty claim",
            "The screen is cracked, can you fix it?"
        ],
        "orders": [
            "Where is my order #12345?",
            "I want to return my product",
            "Can I change my delivery address?"
        ]
    }
