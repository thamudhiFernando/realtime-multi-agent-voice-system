"""
Application Constants - Single Source of Truth
Eliminates magic numbers scattered throughout codebase
"""
from enum import Enum


# ============================================================================
# MESSAGE PROCESSING CONFIGURATION
# ============================================================================

class MessageProcessing:
    """Message queue and processing settings"""
    # Worker pool configuration
    NUM_WORKERS = 5
    MAX_QUEUE_SIZE = 1000

    # Deduplication settings
    DEDUPLICATION_WINDOW_SECONDS = 30
    DEDUPLICATION_CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes
    MAX_MESSAGES_PER_SESSION = 10

    # Timeout settings
    MESSAGE_PROCESSING_TIMEOUT_SECONDS = 120
    AGENT_RESPONSE_TIMEOUT_SECONDS = 60


# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

class RateLimiting:
    """Rate limiting thresholds"""
    # Per-IP rate limits
    MAX_REQUESTS_PER_WINDOW = 100
    RATE_LIMIT_WINDOW_SECONDS = 60

    # LRU cache for rate limiter
    MAX_TRACKED_IPS = 10000
    RATE_LIMIT_CLEANUP_INTERVAL_SECONDS = 300


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionConfig:
    """Session persistence and TTL"""
    # Redis session settings
    SESSION_TTL_SECONDS = 86400  # 24 hours
    SESSION_CLEANUP_INTERVAL_SECONDS = 3600  # 1 hour

    # Session lock cleanup
    INACTIVE_SESSION_CLEANUP_SECONDS = 7200  # 2 hours
    MAX_CONCURRENT_SESSIONS = 10000


# ============================================================================
# FRONTEND TIMING CONSTANTS
# ============================================================================

class FrontendTiming:
    """Frontend timing thresholds"""
    # Send throttling
    DUPLICATE_SEND_THROTTLE_MS = 2000  # 2 seconds
    SENDING_STATE_DURATION_MS = 1000  # 1 second

    # Error display
    ERROR_AUTO_CLEAR_MS = 2000

    # Reconnection
    RECONNECTION_DELAY_MS = 1000
    RECONNECTION_DELAY_MAX_MS = 10000
    RECONNECTION_TIMEOUT_MS = 20000

    # UI updates
    TYPING_INDICATOR_DEBOUNCE_MS = 300
    SCROLL_TO_BOTTOM_DEBOUNCE_MS = 100


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

class AgentConfig:
    """Agent behavior settings"""
    # LLM parameters
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 500

    # Agent timeout
    AGENT_PROCESSING_TIMEOUT_SECONDS = 60

    # Context management
    MAX_CONVERSATION_HISTORY = 20
    MAX_CONTEXT_LENGTH_CHARS = 4000


# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

class RedisConfig:
    """Redis connection and operation settings"""
    # Connection pool
    MAX_CONNECTIONS = 50
    SOCKET_TIMEOUT_SECONDS = 5
    SOCKET_CONNECT_TIMEOUT_SECONDS = 5

    # Retry strategy
    MAX_RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_SECONDS = 1

    # Health check
    HEALTH_CHECK_INTERVAL_SECONDS = 30


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database connection pool settings"""
    # Connection pool
    POOL_SIZE = 20
    MAX_OVERFLOW = 10
    POOL_RECYCLE_SECONDS = 3600
    POOL_PRE_PING = True

    # Query timeout
    QUERY_TIMEOUT_SECONDS = 30


# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

class MiddlewareConfig:
    """Middleware settings"""
    # Request ID
    REQUEST_ID_HEADER = "X-Request-ID"

    # Logging
    LOG_REQUEST_BODY = False
    LOG_RESPONSE_BODY = False
    MAX_LOG_BODY_SIZE = 1000


# ============================================================================
# WEBSOCKET CONFIGURATION
# ============================================================================

class WebSocketConfig:
    """Socket.IO settings"""
    # Ping/pong
    PING_INTERVAL_SECONDS = 25
    PING_TIMEOUT_SECONDS = 60

    # Connection
    MAX_HTTP_BUFFER_SIZE = 1_000_000  # 1MB
    ASYNC_MODE = "asgi"

    # CORS
    CORS_ALLOWED_ORIGINS = "*"


# ============================================================================
# PERFORMANCE THRESHOLDS
# ============================================================================

class PerformanceThresholds:
    """Performance monitoring thresholds"""
    # Response time warnings
    SLOW_REQUEST_THRESHOLD_MS = 1000
    VERY_SLOW_REQUEST_THRESHOLD_MS = 3000

    # Memory warnings
    HIGH_MEMORY_USAGE_MB = 500
    CRITICAL_MEMORY_USAGE_MB = 1000

    # Queue warnings
    HIGH_QUEUE_SIZE = 50
    CRITICAL_QUEUE_SIZE = 100


# ============================================================================
# FILE AND PATH CONFIGURATION
# ============================================================================

class PathConfig:
    """File paths and directories"""
    KNOWLEDGE_BASE_DIR = "knowledge"
    LOGS_DIR = "logs"
    TEMP_DIR = "tmp"

    # Knowledge base files
    SALES_KB_FILE = "sales_kb.json"
    MARKETING_KB_FILE = "marketing_kb.json"
    SUPPORT_KB_FILE = "support_kb.json"
    LOGISTICS_KB_FILE = "logistics_kb.json"


# ============================================================================
# MESSAGE CORRELATION
# ============================================================================

class MessageCorrelation:
    """Message correlation settings"""
    # Visual settings
    CORRELATION_COLORS = [
        '#1976d2',  # Blue
        '#9c27b0',  # Purple
        '#2e7d32',  # Green
        '#ed6c02',  # Orange
        '#d32f2f',  # Red
        '#00796b'   # Teal
    ]

    # Limits
    MAX_PENDING_MESSAGES = 10
    MESSAGE_CORRELATION_TIMEOUT_MS = 30000


# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

class SentimentConfig:
    """Sentiment analysis thresholds"""
    NEGATIVE_THRESHOLD = -0.3
    POSITIVE_THRESHOLD = 0.3

    # Handoff triggers
    VERY_NEGATIVE_THRESHOLD = -0.6
    ESCALATION_KEYWORDS = [
        'manager', 'supervisor', 'complaint', 'frustrated',
        'angry', 'unacceptable', 'terrible', 'horrible'
    ]


# ============================================================================
# AGENT TYPES (ENUM)
# ============================================================================

class AgentType(str, Enum):
    """Agent type enumeration"""
    ORCHESTRATOR = "orchestrator"
    SALES = "sales"
    MARKETING = "marketing"
    SUPPORT = "support"
    LOGISTICS = "logistics"
    HUMAN = "human"


# ============================================================================
# MESSAGE STATUS (ENUM)
# ============================================================================

class MessageStatus(str, Enum):
    """Message processing status"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# INTENT TYPES (ENUM)
# ============================================================================

class IntentType(str, Enum):
    """User intent classification"""
    PRODUCT_INQUIRY = "product_inquiry"
    ORDER_STATUS = "order_status"
    TECHNICAL_SUPPORT = "technical_support"
    PROMOTION_INQUIRY = "promotion_inquiry"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    HUMAN_HANDOFF = "human_handoff"


# ============================================================================
# HTTP STATUS CODES
# ============================================================================

class HTTPStatus:
    """Common HTTP status codes"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ============================================================================
# ERROR MESSAGES
# ============================================================================

class ErrorMessages:
    """Standardized error messages"""
    # Generic errors
    INTERNAL_ERROR = "I apologize, but I'm having trouble processing your request right now. Please try again."
    RATE_LIMITED = "You're sending messages too quickly. Please wait a moment and try again."
    SESSION_EXPIRED = "Your session has expired. Please refresh the page to start a new conversation."

    # Agent-specific errors
    AGENT_TIMEOUT = "I'm taking longer than expected to respond. Please try rephrasing your question."
    AGENT_UNAVAILABLE = "I'm temporarily unavailable. Please try again in a moment."

    # Database errors
    DATABASE_ERROR = "I'm having trouble accessing our information right now. Please try again."
    DATABASE_TIMEOUT = "The database is taking too long to respond. Please try again."

    # External service errors
    LLM_ERROR = "I'm having trouble understanding right now. Please try rephrasing."
    LLM_TIMEOUT = "I'm taking too long to think. Please try again."

    # Validation errors
    EMPTY_MESSAGE = "Please enter a message."
    MESSAGE_TOO_LONG = "Your message is too long. Please keep it under 1000 characters."
    INVALID_INPUT = "I couldn't understand that input. Please try again."


# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

class SuccessMessages:
    """Standardized success messages"""
    MESSAGE_SENT = "Message sent successfully"
    MESSAGE_CANCELLED = "Message cancelled"
    SESSION_CREATED = "Welcome! How can I help you today?"
    HANDOFF_INITIATED = "I'm connecting you with a human agent..."


# ============================================================================
# FEATURE FLAGS
# ============================================================================

class FeatureFlags:
    """Feature toggles for gradual rollouts"""
    ENABLE_VOICE_INPUT = True
    ENABLE_MESSAGE_CANCELLATION = True
    ENABLE_OFFLINE_QUEUE = True
    ENABLE_SENTIMENT_ANALYSIS = True
    ENABLE_ANALYTICS = True
    ENABLE_HUMAN_HANDOFF = True

    # Performance features
    ENABLE_MESSAGE_DEDUPLICATION = True
    ENABLE_RATE_LIMITING = True
    ENABLE_REQUEST_LOGGING = True


# ============================================================================
# VALIDATION RULES
# ============================================================================

class ValidationRules:
    """Input validation rules"""
    MIN_MESSAGE_LENGTH = 1
    MAX_MESSAGE_LENGTH = 1000

    MIN_SESSION_ID_LENGTH = 8
    MAX_SESSION_ID_LENGTH = 64

    # File upload limits (future)
    MAX_FILE_SIZE_MB = 10
    ALLOWED_FILE_TYPES = ['.jpg', '.jpeg', '.png', '.pdf', '.txt']
