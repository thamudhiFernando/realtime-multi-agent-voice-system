"""
Agent Performance Analytics and Metrics Tracking
Tracks agent response times, accuracy, and usage statistics
"""
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import wraps
import redis.asyncio as redis

from app.utils.config import settings
from app.utils.logger import logger


class PerformanceAnalytics:
    """
    Tracks and stores agent performance metrics

    Metrics tracked:
    - Response time per agent
    - Intent classification accuracy
    - Agent handoff frequency
    - Database operation counts
    - Token usage (if available)
    - Error rates
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize performance analytics tracker

        Args:
            redis_url (str, optional): Redis connection URL for metrics storage
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """
        Connect to Redis for metrics storage

        Note:
            Metrics will be stored in memory if Redis is unavailable
        """
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis for performance analytics")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for analytics: {str(e)}")
            self.redis_client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis analytics")

    async def record_agent_response(
        self,
        agent_name: str,
        response_time_ms: float,
        session_id: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        tokens_used: Optional[int] = None,
        success: bool = True
    ):
        """
        Record agent response metrics

        Args:
            agent_name (str): Name of the agent
            response_time_ms (float): Response time in milliseconds
            session_id (str): Session identifier
            intent (str, optional): Classified intent
            confidence (float, optional): Intent confidence score
            tokens_used (int, optional): Number of tokens used
            success (bool): Whether response was successful
        """
        if not self.redis_client:
            return

        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            metric_key = f"metrics:agent:{agent_name}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"

            # Store daily metrics
            metric_data = {
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "session_id": session_id,
                "intent": intent or "unknown",
                "confidence": confidence or 0.0,
                "tokens_used": tokens_used or 0,
                "success": success
            }

            # Add to Redis list (keep last 1000 entries per agent per day)
            await self.redis_client.lpush(metric_key, json.dumps(metric_data))
            await self.redis_client.ltrim(metric_key, 0, 999)
            await self.redis_client.expire(metric_key, 86400 * 7)  # Keep for 7 days

            # Update aggregate stats
            await self._update_aggregate_stats(agent_name, response_time_ms, success)

        except Exception as e:
            logger.error(f"Failed to record agent response metrics: {str(e)}")

    async def _update_aggregate_stats(
        self,
        agent_name: str,
        response_time_ms: float,
        success: bool
    ):
        """
        Update aggregate statistics for an agent

        Args:
            agent_name (str): Name of the agent
            response_time_ms (float): Response time in milliseconds
            success (bool): Whether response was successful
        """
        if not self.redis_client:
            return

        try:
            stats_key = f"stats:agent:{agent_name}"

            # Increment counters
            await self.redis_client.hincrby(stats_key, "total_requests", 1)
            if success:
                await self.redis_client.hincrby(stats_key, "successful_requests", 1)
            else:
                await self.redis_client.hincrby(stats_key, "failed_requests", 1)

            # Update average response time (simple moving average)
            current_avg = await self.redis_client.hget(stats_key, "avg_response_time_ms")
            current_count = await self.redis_client.hget(stats_key, "total_requests")

            if current_avg and current_count:
                new_avg = (float(current_avg) * (int(current_count) - 1) + response_time_ms) / int(current_count)
                await self.redis_client.hset(stats_key, "avg_response_time_ms", new_avg)
            else:
                await self.redis_client.hset(stats_key, "avg_response_time_ms", response_time_ms)

            # Track min/max response times
            current_min = await self.redis_client.hget(stats_key, "min_response_time_ms")
            if not current_min or response_time_ms < float(current_min):
                await self.redis_client.hset(stats_key, "min_response_time_ms", response_time_ms)

            current_max = await self.redis_client.hget(stats_key, "max_response_time_ms")
            if not current_max or response_time_ms > float(current_max):
                await self.redis_client.hset(stats_key, "max_response_time_ms", response_time_ms)

        except Exception as e:
            logger.error(f"Failed to update aggregate stats: {str(e)}")

    async def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        Get aggregate statistics for an agent

        Args:
            agent_name (str): Name of the agent

        Returns:
            Dict[str, Any]: Agent statistics including request counts, response times, success rate
        """
        if not self.redis_client:
            return {}

        try:
            stats_key = f"stats:agent:{agent_name}"
            stats = await self.redis_client.hgetall(stats_key)

            if not stats:
                return {
                    "agent_name": agent_name,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "success_rate": 0.0,
                    "avg_response_time_ms": 0.0,
                    "min_response_time_ms": 0.0,
                    "max_response_time_ms": 0.0
                }

            total = int(stats.get("total_requests", 0))
            successful = int(stats.get("successful_requests", 0))

            return {
                "agent_name": agent_name,
                "total_requests": total,
                "successful_requests": successful,
                "failed_requests": int(stats.get("failed_requests", 0)),
                "success_rate": (successful / total * 100) if total > 0 else 0.0,
                "avg_response_time_ms": float(stats.get("avg_response_time_ms", 0.0)),
                "min_response_time_ms": float(stats.get("min_response_time_ms", 0.0)),
                "max_response_time_ms": float(stats.get("max_response_time_ms", 0.0))
            }

        except Exception as e:
            logger.error(f"Failed to get agent stats: {str(e)}")
            return {}

    async def get_all_agents_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all agents

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping agent names to their statistics
        """
        agent_names = ["orchestrator", "sales", "marketing", "support", "logistics"]
        stats = {}

        for agent_name in agent_names:
            stats[agent_name] = await self.get_agent_stats(agent_name)

        return stats

    async def record_handoff(
        self,
        from_agent: str,
        to_agent: str,
        session_id: str,
        reason: str
    ):
        """
        Record agent handoff event for analytics

        Args:
            from_agent (str): Source agent
            to_agent (str): Destination agent
            session_id (str): Session identifier
            reason (str): Reason for handoff
        """
        if not self.redis_client:
            return

        try:
            handoff_key = f"handoffs:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            handoff_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from_agent": from_agent,
                "to_agent": to_agent,
                "session_id": session_id,
                "reason": reason
            }

            await self.redis_client.lpush(handoff_key, json.dumps(handoff_data))
            await self.redis_client.expire(handoff_key, 86400 * 7)  # Keep for 7 days

            # Update handoff counter
            counter_key = f"stats:handoffs:{from_agent}:{to_agent}"
            await self.redis_client.incr(counter_key)

        except Exception as e:
            logger.error(f"Failed to record handoff: {str(e)}")


# Global analytics instance
_analytics: Optional[PerformanceAnalytics] = None


async def get_analytics() -> PerformanceAnalytics:
    """
    Get or create the global analytics instance

    Returns:
        PerformanceAnalytics: Global analytics instance
    """
    global _analytics

    if _analytics is None:
        _analytics = PerformanceAnalytics()
        await _analytics.connect()

    return _analytics


async def close_analytics():
    """Close the global analytics instance"""
    global _analytics

    if _analytics:
        await _analytics.disconnect()
        _analytics = None


def track_performance(agent_name: str):
    """
    Decorator to automatically track agent performance metrics

    Args:
        agent_name (str): Name of the agent being tracked

    Usage:
        @track_performance("sales")
        async def process(self, state):
            # Agent logic here
            return state
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = e
                raise
            finally:
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000

                # Record metrics
                try:
                    analytics = await get_analytics()

                    # Extract session_id and other info from args if available
                    session_id = "unknown"
                    intent = None
                    confidence = None

                    # If this is a method with state parameter
                    if len(args) > 1 and isinstance(args[1], dict):
                        state = args[1]
                        session_id = state.get("unique_session_id", "unknown")
                        intent = state.get("classified_intent")
                        confidence = state.get("intent_confidence_score")

                    await analytics.record_agent_response(
                        agent_name=agent_name,
                        response_time_ms=response_time_ms,
                        session_id=session_id,
                        intent=intent,
                        confidence=confidence,
                        success=success
                    )

                    if not success:
                        logger.error(f"Agent {agent_name} error: {str(error)}")

                except Exception as analytics_error:
                    logger.warning(f"Failed to track performance: {str(analytics_error)}")

        return wrapper
    return decorator
