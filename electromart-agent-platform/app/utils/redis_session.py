"""
Redis Session Manager for Persistent Conversation Memory
Provides persistent storage for conversation state across reconnections
"""
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional
from datetime import timedelta
from app.utils.config import settings
from app.utils.logger import logger


class RedisSessionManager:
    """
    Manages persistent conversation sessions using Redis

    Features:
    - Store conversation state persistently
    - Retrieve conversation history on reconnection
    - Automatic expiration after 24 hours of inactivity
    - JSON serialization of complex state objects
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize Redis session manager

        Args:
            redis_url (str, optional): Redis connection URL. Defaults to settings.redis_url
        """
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.session_ttl = timedelta(hours=24)  # 24 hour session expiration

    async def connect(self):
        """
        Establish connection to Redis server

        Note:
            Call this method before using the session manager
        """
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis for persistent conversation storage")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Using in-memory storage as fallback.")
            self.redis_client = None

    async def disconnect(self):
        """
        Close Redis connection gracefully
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def save_session(self, session_id: str, state: Dict[str, Any]) -> bool:
        """
        Save conversation state to Redis with automatic expiration

        Args:
            session_id (str): Unique session identifier
            state (Dict[str, Any]): Complete conversation state to persist

        Returns:
            bool: True if saved successfully, False otherwise

        Note:
            State is serialized to JSON and expires after 24 hours of inactivity
        """
        if not self.redis_client:
            logger.warning("Redis not available, cannot persist session")
            return False

        try:
            # Serialize state to JSON
            state_json = json.dumps(state, default=str)

            # Save to Redis with TTL
            key = f"session:{session_id}"
            await self.redis_client.setex(
                key,
                self.session_ttl,
                state_json
            )

            logger.debug(f"Saved session {session_id} to Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {str(e)}")
            return False

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation state from Redis

        Args:
            session_id (str): Unique session identifier

        Returns:
            Optional[Dict[str, Any]]: Conversation state if found, None otherwise

        Note:
            Automatically refreshes TTL on successful load to extend session life
        """
        if not self.redis_client:
            logger.warning("Redis not available, cannot load session")
            return None

        try:
            key = f"session:{session_id}"
            state_json = await self.redis_client.get(key)

            if state_json:
                # Refresh TTL on access
                await self.redis_client.expire(key, self.session_ttl)

                # Deserialize state
                state = json.loads(state_json)
                logger.debug(f"Loaded session {session_id} from Redis")
                return state
            else:
                logger.debug(f"Session {session_id} not found in Redis")
                return None

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete conversation session from Redis

        Args:
            session_id (str): Unique session identifier

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            await self.redis_client.delete(key)
            logger.debug(f"Deleted session {session_id} from Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists in Redis

        Args:
            session_id (str): Unique session identifier

        Returns:
            bool: True if session exists, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = f"session:{session_id}"
            exists = await self.redis_client.exists(key)
            return bool(exists)

        except Exception as e:
            logger.error(f"Failed to check session {session_id}: {str(e)}")
            return False

    async def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions in Redis

        Returns:
            int: Number of active sessions
        """
        if not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys("session:*")
            return len(keys)

        except Exception as e:
            logger.error(f"Failed to count active sessions: {str(e)}")
            return 0


# Global session manager instance
_session_manager: Optional[RedisSessionManager] = None


async def get_session_manager() -> RedisSessionManager:
    """
    Get or create the global Redis session manager instance

    Returns:
        RedisSessionManager: Global session manager instance

    Note:
        Automatically connects to Redis on first call
    """
    global _session_manager

    if _session_manager is None:
        _session_manager = RedisSessionManager()
        await _session_manager.connect()

    return _session_manager


async def close_session_manager():
    """
    Close the global Redis session manager connection

    Note:
        Call this on application shutdown
    """
    global _session_manager

    if _session_manager:
        await _session_manager.disconnect()
        _session_manager = None
