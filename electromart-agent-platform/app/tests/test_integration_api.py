"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def test_client_with_db():
    """Create test client with test database"""
    # Create test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.mark.integration
class TestHealthEndpoint:
    """Integration tests for health check endpoint"""

    def test_health_endpoint_returns_200(self, test_client_with_db):
        """Test that health endpoint returns 200 OK"""
        response = test_client_with_db.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_endpoint_returns_correct_structure(self, test_client_with_db):
        """Test health endpoint response structure"""
        response = test_client_with_db.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert data["service"] == "electromart-agents"


@pytest.mark.integration
class TestRootEndpoint:
    """Integration tests for root endpoint"""

    def test_root_endpoint_returns_service_info(self, test_client_with_db):
        """Test root endpoint returns service information"""
        response = test_client_with_db.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["service"] == "ElectroMart Multi-Agent System"


@pytest.mark.integration
@pytest.mark.database
class TestProductsEndpoint:
    """Integration tests for products endpoint"""

    def test_get_products_returns_list(self, test_client_with_db):
        """Test that products endpoint returns a list"""
        response = test_client_with_db.get("/api/products")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_products_with_category_filter(self, test_client_with_db):
        """Test products endpoint with category filter"""
        response = test_client_with_db.get("/api/products?category=Laptops")

        assert response.status_code == 200
        products = response.json()
        # All returned products should be Laptops
        for product in products:
            if "category" in product:
                assert product["category"] == "Laptops"


@pytest.mark.integration
@pytest.mark.database
class TestOrdersEndpoint:
    """Integration tests for orders endpoint"""

    def test_get_order_not_found_returns_404(self, test_client_with_db):
        """Test that non-existent order returns 404"""
        response = test_client_with_db.get("/api/orders/NONEXISTENT999")

        assert response.status_code == 404
        assert "detail" in response.json()


@pytest.mark.integration
@pytest.mark.database
class TestPromotionsEndpoint:
    """Integration tests for promotions endpoint"""

    def test_get_promotions_returns_list(self, test_client_with_db):
        """Test that promotions endpoint returns a list"""
        response = test_client_with_db.get("/api/promotions")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_active_promotions_only(self, test_client_with_db):
        """Test that active_only filter works"""
        response = test_client_with_db.get("/api/promotions?active_only=true")

        assert response.status_code == 200
        promotions = response.json()
        # Could verify is_active field if promotions exist
        assert isinstance(promotions, list)


@pytest.mark.integration
class TestAPIErrorHandling:
    """Integration tests for API error handling"""

    def test_invalid_endpoint_returns_404(self, test_client_with_db):
        """Test that invalid endpoint returns 404"""
        response = test_client_with_db.get("/api/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed_returns_405(self, test_client_with_db):
        """Test that wrong HTTP method returns 405"""
        response = test_client_with_db.post("/health")

        assert response.status_code == 405
