"""
Human Handoff Management
Handles escalation from AI agents to human support agents
"""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import redis.asyncio as redis
import json
from app.utils.config import settings
from app.utils.logger import logger


class HandoffPriority(Enum):
    """Priority levels for human handoff"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffReason(Enum):
    """Reasons for human handoff"""
    NEGATIVE_SENTIMENT = "negative_sentiment"
    COMPLEX_QUERY = "complex_query"
    EXPLICIT_REQUEST = "explicit_request"
    AGENT_UNCERTAINTY = "agent_uncertainty"
    REPEATED_FAILURE = "repeated_failure"
    URGENT_ISSUE = "urgent_issue"
    POLICY_VIOLATION = "policy_violation"


class HumanHandoffManager:
    """
    Manages handoff from AI agents to human support agents

    Features:
    - Queue management for handoff requests
    - Priority-based routing
    - Human agent availability tracking
    - Handoff history and analytics
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize human handoff manager

        Args:
            redis_url (str, optional): Redis connection URL
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis for handoff queue management"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis for human handoff management")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for handoff: {str(e)}")
            self.redis_client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis handoff")

    async def request_handoff(
        self,
        session_id: str,
        customer_id: Optional[int],
        current_agent: str,
        reason: HandoffReason,
        priority: HandoffPriority,
        context: Dict[str, Any],
        sentiment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Request handoff to human agent

        Args:
            session_id (str): Unique session identifier
            customer_id (int, optional): Customer database ID
            current_agent (str): Current AI agent name
            reason (HandoffReason): Reason for handoff
            priority (HandoffPriority): Priority level
            context (Dict[str, Any]): Conversation context and history
            sentiment (Dict[str, Any], optional): Customer sentiment analysis

        Returns:
            Dict[str, Any]: Handoff request details including:
                - handoff_id (str): Unique handoff request identifier
                - queue_position (int): Position in queue
                - estimated_wait_time (int): Estimated wait in seconds
                - status (str): Current status
        """
        if not self.redis_client:
            logger.error("Redis not available for handoff")
            return {
                "handoff_id": None,
                "queue_position": 0,
                "estimated_wait_time": 0,
                "status": "failed",
                "message": "Handoff service unavailable"
            }

        try:
            # Generate unique handoff ID
            handoff_id = f"HO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{session_id[:8]}"

            # Create handoff request
            handoff_request = {
                "handoff_id": handoff_id,
                "session_id": session_id,
                "customer_id": customer_id,
                "current_agent": current_agent,
                "reason": reason.value,
                "priority": priority.value,
                "context": context,
                "sentiment": sentiment,
                "created_at": datetime.utcnow().isoformat(),
                "status": "queued"
            }

            # Add to appropriate priority queue
            queue_key = f"handoff_queue:{priority.value}"
            await self.redis_client.lpush(queue_key, json.dumps(handoff_request))

            # Store handoff details
            handoff_key = f"handoff:{handoff_id}"
            await self.redis_client.setex(
                handoff_key,
                3600 * 24,  # 24 hour expiration
                json.dumps(handoff_request)
            )

            # Get queue position
            queue_position = await self._get_queue_position(priority)

            # Estimate wait time (rough estimate: 5 min per person ahead)
            estimated_wait_time = queue_position * 300  # seconds

            logger.info(f"Handoff requested: {handoff_id} (Priority: {priority.value}, Reason: {reason.value})")

            return {
                "handoff_id": handoff_id,
                "queue_position": queue_position,
                "estimated_wait_time": estimated_wait_time,
                "status": "queued",
                "message": f"Your request has been queued for a human agent. Queue position: {queue_position}"
            }

        except Exception as e:
            logger.error(f"Failed to request handoff: {str(e)}")
            return {
                "handoff_id": None,
                "queue_position": 0,
                "estimated_wait_time": 0,
                "status": "failed",
                "message": "Failed to request handoff"
            }

    async def _get_queue_position(self, priority: HandoffPriority) -> int:
        """
        Get current position in handoff queue

        Args:
            priority (HandoffPriority): Priority level

        Returns:
            int: Queue position (1-based)
        """
        if not self.redis_client:
            return 0

        try:
            queue_key = f"handoff_queue:{priority.value}"
            length = await self.redis_client.llen(queue_key)
            return length

        except Exception as e:
            logger.error(f"Failed to get queue position: {str(e)}")
            return 0

    async def get_next_handoff(
        self,
        human_agent_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get next handoff request for human agent (prioritized)

        Args:
            human_agent_id (str): ID of the human agent requesting work

        Returns:
            Optional[Dict[str, Any]]: Next handoff request or None if queue is empty

        Note:
            Checks queues in priority order: critical > high > medium > low
        """
        if not self.redis_client:
            return None

        try:
            # Check queues in priority order
            priorities = [
                HandoffPriority.CRITICAL,
                HandoffPriority.HIGH,
                HandoffPriority.MEDIUM,
                HandoffPriority.LOW
            ]

            for priority in priorities:
                queue_key = f"handoff_queue:{priority.value}"
                handoff_json = await self.redis_client.rpop(queue_key)

                if handoff_json:
                    handoff = json.loads(handoff_json)
                    handoff["assigned_to"] = human_agent_id
                    handoff["assigned_at"] = datetime.utcnow().isoformat()
                    handoff["status"] = "assigned"

                    # Update handoff details
                    handoff_key = f"handoff:{handoff['handoff_id']}"
                    await self.redis_client.setex(
                        handoff_key,
                        3600 * 24,
                        json.dumps(handoff)
                    )

                    logger.info(f"Handoff {handoff['handoff_id']} assigned to {human_agent_id}")
                    return handoff

            return None

        except Exception as e:
            logger.error(f"Failed to get next handoff: {str(e)}")
            return None

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about handoff queues

        Returns:
            Dict[str, Any]: Queue statistics including counts per priority
        """
        if not self.redis_client:
            return {}

        try:
            stats = {
                "total_queued": 0,
                "by_priority": {}
            }

            for priority in HandoffPriority:
                queue_key = f"handoff_queue:{priority.value}"
                count = await self.redis_client.llen(queue_key)
                stats["by_priority"][priority.value] = count
                stats["total_queued"] += count

            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {}

    async def check_handoff_needed(
        self,
        state: Dict[str, Any],
        sentiment: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[HandoffReason], Optional[HandoffPriority]]:
        """
        Check if current conversation should trigger human handoff

        Args:
            state (Dict[str, Any]): Current conversation state
            sentiment (Dict[str, Any], optional): Sentiment analysis results

        Returns:
            tuple: (needs_handoff, reason, priority)

        Note:
            Analyzes conversation history, sentiment, and agent confidence
        """
        # Check for explicit handoff request
        messages = state.get("conversation_messages", [])
        if messages:
            last_message = messages[-1]
            # Replace dict-style .get() with .content
            text_lower = getattr(last_message, "content", "") or last_message.get("content", "")
            text_lower = text_lower.lower()

            if any(phrase in text_lower for phrase in [
                "speak to human", "talk to person", "human agent",
                "real person", "speak to manager", "escalate"
            ]):
                return True, HandoffReason.EXPLICIT_REQUEST, HandoffPriority.HIGH

        # Check sentiment-based escalation
        if sentiment and sentiment.get("requires_escalation"):
            urgency = sentiment.get("urgency_level", "medium")
            priority = {
                "critical": HandoffPriority.CRITICAL,
                "high": HandoffPriority.HIGH,
                "medium": HandoffPriority.MEDIUM,
                "low": HandoffPriority.LOW
            }.get(urgency, HandoffPriority.MEDIUM)

            return True, HandoffReason.NEGATIVE_SENTIMENT, priority

        # Check for low confidence
        confidence = state.get("intent_confidence_score", 1.0)
        if confidence < 0.3:
            return True, HandoffReason.AGENT_UNCERTAINTY, HandoffPriority.MEDIUM

        # Check for repeated handoffs (potential failure loop)
        handoff_history = state.get("agent_handoff_history", [])
        if len(handoff_history) >= 3:
            return True, HandoffReason.REPEATED_FAILURE, HandoffPriority.HIGH

        return False, None, None


# Global handoff manager instance
_handoff_manager: Optional[HumanHandoffManager] = None


async def get_handoff_manager() -> HumanHandoffManager:
    """
    Get or create the global human handoff manager instance

    Returns:
        HumanHandoffManager: Global handoff manager instance
    """
    global _handoff_manager

    if _handoff_manager is None:
        _handoff_manager = HumanHandoffManager()
        await _handoff_manager.connect()

    return _handoff_manager


async def close_handoff_manager():
    """Close the global handoff manager connection"""
    global _handoff_manager

    if _handoff_manager:
        await _handoff_manager.disconnect()
        _handoff_manager = None
