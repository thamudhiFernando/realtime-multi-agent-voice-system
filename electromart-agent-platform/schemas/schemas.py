"""
API Request/Response Schemas with Pydantic
Professional data validation and serialization for REST API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentType(str, Enum):
    """Agent type enumeration"""
    ORCHESTRATOR = "orchestrator"
    SALES = "sales"
    MARKETING = "marketing"
    SUPPORT = "support"
    LOGISTICS = "logistics"


class SentimentLabel(str, Enum):
    """Sentiment label enumeration"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class UrgencyLevel(str, Enum):
    """Urgency level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffPriority(str, Enum):
    """Handoff priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Base Schemas
# ============================================================================

class BaseResponse(BaseModel):
    """Base response schema with standard fields"""
    status: str = Field(..., description="Response status (success/error)")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")


# ============================================================================
# Product Schemas
# ============================================================================

class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Product price in USD")
    description: Optional[str] = Field(None, max_length=2000)


class ProductResponse(ProductBase):
    """Product response schema"""
    id: int
    stock_status: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ProductListResponse(BaseResponse):
    """Product list response"""
    data: List[ProductResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Order Schemas
# ============================================================================

class OrderResponse(BaseModel):
    """Order response schema"""
    order_number: str
    status: str
    order_date: Optional[datetime]
    tracking_number: Optional[str]
    total_amount: float

    class Config:
        orm_mode = True


class OrderDetailResponse(BaseResponse):
    """Order detail response"""
    data: OrderResponse


# ============================================================================
# Promotion Schemas
# ============================================================================

class PromotionResponse(BaseModel):
    """Promotion response schema"""
    id: int
    name: str
    description: Optional[str]
    discount_percentage: float
    promo_code: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True


class PromotionListResponse(BaseResponse):
    """Promotion list response"""
    data: List[PromotionResponse]
    total: int


# ============================================================================
# Analytics Schemas
# ============================================================================

class AgentStats(BaseModel):
    """Agent statistics schema"""
    agent_name: str
    total_requests: int = Field(..., ge=0)
    successful_requests: int = Field(..., ge=0)
    failed_requests: int = Field(..., ge=0)
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    avg_response_time_ms: float = Field(..., ge=0)
    min_response_time_ms: float = Field(..., ge=0)
    max_response_time_ms: float = Field(..., ge=0)


class AllAgentsAnalyticsResponse(BaseResponse):
    """All agents analytics response"""
    data: Dict[str, AgentStats]


class AgentAnalyticsResponse(BaseResponse):
    """Single agent analytics response"""
    data: AgentStats


# ============================================================================
# Handoff Schemas
# ============================================================================

class HandoffQueueStats(BaseModel):
    """Handoff queue statistics"""
    total_queued: int = Field(..., ge=0)
    by_priority: Dict[str, int]


class HandoffQueueStatsResponse(BaseResponse):
    """Handoff queue stats response"""
    data: HandoffQueueStats


class HandoffRequest(BaseModel):
    """Handoff request details"""
    handoff_id: str
    session_id: str
    customer_id: Optional[int]
    current_agent: str
    reason: str
    priority: HandoffPriority
    context: Dict[str, Any]
    sentiment: Optional[Dict[str, Any]]
    created_at: datetime
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    status: str


class HandoffResponse(BaseResponse):
    """Handoff response"""
    data: Optional[HandoffRequest]


# ============================================================================
# Conversation/Message Schemas
# ============================================================================

class MessageMetadata(BaseModel):
    """Message metadata"""
    intent: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)
    db_operations_count: int = Field(0, ge=0)
    sentiment: Optional[SentimentLabel] = None
    sentiment_polarity: Optional[float] = Field(None, ge=-1, le=1)
    urgency_level: Optional[UrgencyLevel] = None
    response_time_ms: Optional[float] = Field(None, ge=0)


class ConversationMessage(BaseModel):
    """Conversation message schema"""
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    agent_name: Optional[AgentType] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[MessageMetadata] = None


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    customer_id: Optional[int] = None
    current_agent: Optional[AgentType] = None
    created_at: datetime
    last_activity: datetime
    message_count: int = Field(..., ge=0)


# ============================================================================
# Health Check Schemas
# ============================================================================

class ServiceHealth(BaseModel):
    """Individual service health"""
    status: str = Field(..., description="healthy/unhealthy/degraded")
    latency_ms: Optional[float] = Field(None, ge=0)
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Comprehensive health check response"""
    status: str = Field(..., description="Overall system status")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, ServiceHealth]
    features: Dict[str, bool]


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail schema"""
    loc: Optional[List[str]] = Field(None, description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# ============================================================================
# Metrics Schemas (Prometheus-compatible)
# ============================================================================

class MetricSample(BaseModel):
    """Single metric sample"""
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    timestamp: Optional[datetime] = None


class MetricsResponse(BaseModel):
    """Metrics response for monitoring"""
    metrics: List[MetricSample]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Validation Examples
# ============================================================================

# Example usage in API endpoints:
"""
@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductBase) -> ProductResponse:
    # Pydantic automatically validates the input
    # Returns validated ProductResponse
    pass

@router.get("/products", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = None,
    pagination: PaginationParams = Depends()
) -> ProductListResponse:
    # Pagination automatically validated
    pass
"""
