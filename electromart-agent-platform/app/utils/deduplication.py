"""
Message Deduplication Manager
Prevents duplicate message processing from retries/double-clicks
"""
import hashlib
import time
from typing import Dict, Tuple
from dataclasses import dataclass

from app.utils.logger import logger


@dataclass
class MessageRecord:
    """Record of a processed message"""
    message_hash: str
    session_id: str
    timestamp: float
    message_content: str


class MessageDeduplicationManager:
    """
    Manages message deduplication with intelligent time-based windows

    Rules:
    - Same message within 30 seconds → Duplicate (ignore)
    - Same message after 30 seconds → New question (process)

    This allows:
    - User asks "iPhone 15 price?" at 10:00 AM → Answered
    - User asks "iPhone 15 price?" at 10:05 AM → Answered again (legitimate repeat)
    - User double-clicks send → Second ignored (duplicate)
    """

    def __init__(self, dedup_window_seconds: int = 30):
        """
        Initialize deduplication manager

        Args:
            dedup_window_seconds: Time window for considering duplicates (default: 30s)
        """
        self.dedup_window = dedup_window_seconds

        # Track recent messages: {session_id: [MessageRecord, ...]}
        self.recent_messages: Dict[str, list] = {}

        # Cleanup interval
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Clean up every 5 minutes

        logger.info(f"MessageDeduplicationManager initialized (window: {dedup_window_seconds}s)")

    def generate_message_hash(self, session_id: str, message: str) -> str:
        """
        Generate hash for message content

        Args:
            session_id: Session identifier
            message: Message content

        Returns:
            Hash string
        """
        # Normalize message: lowercase, strip whitespace
        normalized = message.lower().strip()

        # Create hash from session + normalized message
        hash_input = f"{session_id}:{normalized}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def is_duplicate(self, session_id: str, message: str) -> Tuple[bool, str]:
        """
        Check if message is a duplicate within the time window

        Args:
            session_id: Session identifier
            message: Message content

        Returns:
            Tuple of (is_duplicate: bool, reason: str)
        """
        current_time = time.time()
        message_hash = self.generate_message_hash(session_id, message)

        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_records()

        # Check recent messages for this session
        if session_id in self.recent_messages:
            for record in self.recent_messages[session_id]:
                # Check if same message
                if record.message_hash == message_hash:
                    time_diff = current_time - record.timestamp

                    # Within deduplication window
                    if time_diff <= self.dedup_window:
                        logger.warning(
                            f"Duplicate message detected for session {session_id[:8]}... "
                            f"(time since last: {time_diff:.1f}s)"
                        )
                        return True, f"duplicate_within_{self.dedup_window}s"

                    # Outside window - legitimate repeat question
                    logger.info(
                        f"Same message after {time_diff:.1f}s - treating as new question "
                        f"for session {session_id[:8]}..."
                    )
                    return False, "legitimate_repeat"

        return False, "unique"

    def record_message(self, session_id: str, message: str):
        """
        Record a message as processed

        Args:
            session_id: Session identifier
            message: Message content
        """
        current_time = time.time()
        message_hash = self.generate_message_hash(session_id, message)

        record = MessageRecord(
            message_hash=message_hash,
            session_id=session_id,
            timestamp=current_time,
            message_content=message[:100]  # Store truncated for debugging
        )

        # Initialize session list if needed
        if session_id not in self.recent_messages:
            self.recent_messages[session_id] = []

        # Add record
        self.recent_messages[session_id].append(record)

        # Keep only recent messages (last 10 per session)
        self.recent_messages[session_id] = self.recent_messages[session_id][-10:]

        logger.debug(f"Recorded message for session {session_id[:8]}...")

    def _cleanup_old_records(self):
        """Remove old message records outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - (self.dedup_window * 2)  # Keep 2x window for safety

        cleaned_count = 0

        for session_id in list(self.recent_messages.keys()):
            # Filter out old records
            original_count = len(self.recent_messages[session_id])
            self.recent_messages[session_id] = [
                record for record in self.recent_messages[session_id]
                if record.timestamp > cutoff_time
            ]

            # Remove empty session lists
            if not self.recent_messages[session_id]:
                del self.recent_messages[session_id]
                cleaned_count += 1
            else:
                cleaned_count += original_count - len(self.recent_messages[session_id])

        self.last_cleanup = current_time

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old message records")

    def get_stats(self) -> Dict:
        """
        Get deduplication statistics

        Returns:
            Statistics dictionary
        """
        total_records = sum(len(records) for records in self.recent_messages.values())

        return {
            "active_sessions": len(self.recent_messages),
            "total_tracked_messages": total_records,
            "dedup_window_seconds": self.dedup_window,
            "last_cleanup": time.time() - self.last_cleanup
        }


# Global instance
_dedup_manager: MessageDeduplicationManager = None


def get_dedup_manager(dedup_window_seconds: int = 30) -> MessageDeduplicationManager:
    """
    Get or create the global deduplication manager

    Args:
        dedup_window_seconds: Deduplication time window

    Returns:
        MessageDeduplicationManager instance
    """
    global _dedup_manager

    if _dedup_manager is None:
        _dedup_manager = MessageDeduplicationManager(dedup_window_seconds)

    return _dedup_manager
