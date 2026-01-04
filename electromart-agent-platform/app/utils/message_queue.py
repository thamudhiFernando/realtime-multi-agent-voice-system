"""
Message Queue Manager for Concurrent Processing
Handles multiple messages concurrently without blocking
"""
import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import time

from app.utils.logger import logger


@dataclass
class QueuedMessage:
    """Represents a queued message with metadata"""
    message_id: str
    session_id: str
    sid: str  # Socket ID
    user_message: str
    message_type: str
    queued_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageResponse:
    """Represents a processed message response"""
    message_id: str
    session_id: str
    response: Dict[str, Any]
    error: Optional[str] = None
    processing_time: float = 0.0


class MessageQueueManager:
    """
    Manages concurrent message processing with asyncio queues and workers

    Features:
    - Concurrent message processing per session
    - Worker pool for parallel execution
    - Session-level locking to prevent race conditions
    - Message correlation IDs for response matching
    - Graceful error handling
    """

    def __init__(self, num_workers: int = 5, max_queue_size: int = 1000):
        """
        Initialize the message queue manager

        Args:
            num_workers: Number of concurrent worker tasks
            max_queue_size: Maximum queue size before blocking
        """
        self.message_queue = asyncio.Queue(maxsize=max_queue_size)
        self.response_callbacks: Dict[str, Callable] = {}
        self.num_workers = num_workers
        self.workers = []
        self.session_locks: Dict[str, asyncio.Lock] = {}
        self.running = False

        # Processing function to be set by the handler
        self.process_function: Optional[Callable] = None

        # Track queued and processing messages for cancellation
        self.queued_messages: Dict[str, QueuedMessage] = {}
        self.processing_messages: Dict[str, QueuedMessage] = {}
        self.cancelled_messages: set = set()

        # Statistics
        self.stats = {
            "messages_queued": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "messages_cancelled": 0,
            "total_processing_time": 0.0
        }

        logger.info(f"MessageQueueManager initialized with {num_workers} workers")

    def set_process_function(self, func: Callable):
        """Set the message processing function"""
        self.process_function = func

    async def start(self):
        """Start the worker pool"""
        if self.running:
            logger.warning("MessageQueueManager already running")
            return

        self.running = True

        # Start worker tasks
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker(worker_id=i))
            self.workers.append(worker)

        logger.info(f"Started {self.num_workers} message processing workers")

    async def stop(self):
        """Stop the worker pool gracefully"""
        if not self.running:
            return

        self.running = False

        # Wait for all workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()
        logger.info("Message queue manager stopped")

    async def enqueue_message(
        self,
        sid: str,
        session_id: str,
        user_message: str,
        message_type: str = "text",
        callback: Optional[Callable] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Enqueue a message for processing

        Args:
            sid: Socket ID
            session_id: Session identifier
            user_message: User's message text
            message_type: Type of message (text, voice)
            callback: Optional callback function for response
            metadata: Additional metadata

        Returns:
            Message correlation ID
        """
        message_id = str(uuid.uuid4())

        queued_msg = QueuedMessage(
            message_id=message_id,
            session_id=session_id,
            sid=sid,
            user_message=user_message,
            message_type=message_type,
            metadata=metadata or {}
        )

        # Store callback if provided
        if callback:
            self.response_callbacks[message_id] = callback

        # Track the message
        self.queued_messages[message_id] = queued_msg

        # Add to queue
        await self.message_queue.put(queued_msg)

        self.stats["messages_queued"] += 1

        logger.info(
            f"Message enqueued: {message_id[:8]}... for session {session_id[:8]}... "
            f"(queue size: {self.message_queue.qsize()})"
        )

        return message_id

    async def cancel_message(self, message_id: str) -> bool:
        """
        Cancel a pending message

        Args:
            message_id: Message correlation ID to cancel

        Returns:
            True if message was cancelled, False if already processing/completed
        """
        # Check if message is queued (not yet processing)
        if message_id in self.queued_messages:
            self.cancelled_messages.add(message_id)
            del self.queued_messages[message_id]
            self.stats["messages_cancelled"] += 1

            logger.info(f"Message cancelled: {message_id[:8]}... (was queued)")
            return True

        # Check if message is currently being processed
        if message_id in self.processing_messages:
            self.cancelled_messages.add(message_id)
            self.stats["messages_cancelled"] += 1

            logger.warning(
                f"Message {message_id[:8]}... marked for cancellation "
                f"(already processing - will skip response)"
            )
            return True

        logger.warning(f"Cannot cancel message {message_id[:8]}... (not found or already completed)")
        return False

    async def cancel_session_messages(self, session_id: str) -> int:
        """
        Cancel all pending messages for a session

        Args:
            session_id: Session identifier

        Returns:
            Number of messages cancelled
        """
        cancelled_count = 0

        # Cancel queued messages
        messages_to_cancel = [
            msg_id for msg_id, msg in self.queued_messages.items()
            if msg.session_id == session_id
        ]

        for msg_id in messages_to_cancel:
            if await self.cancel_message(msg_id):
                cancelled_count += 1

        # Mark processing messages for cancellation
        processing_to_cancel = [
            msg_id for msg_id, msg in self.processing_messages.items()
            if msg.session_id == session_id
        ]

        for msg_id in processing_to_cancel:
            if await self.cancel_message(msg_id):
                cancelled_count += 1

        logger.info(
            f"Cancelled {cancelled_count} messages for session {session_id[:8]}..."
        )

        return cancelled_count

    def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """Get or create a lock for a session"""
        if session_id not in self.session_locks:
            self.session_locks[session_id] = asyncio.Lock()
        return self.session_locks[session_id]

    async def _worker(self, worker_id: int):
        """
        Worker task that processes messages from the queue

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get message from queue with timeout
                try:
                    queued_msg = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                start_time = time.time()

                # Check if message was cancelled
                if queued_msg.message_id in self.cancelled_messages:
                    logger.info(
                        f"Worker {worker_id} skipping cancelled message {queued_msg.message_id[:8]}..."
                    )

                    # Remove from tracking
                    self.cancelled_messages.discard(queued_msg.message_id)
                    if queued_msg.message_id in self.queued_messages:
                        del self.queued_messages[queued_msg.message_id]

                    # Mark task as done
                    self.message_queue.task_done()
                    continue

                # Move to processing
                if queued_msg.message_id in self.queued_messages:
                    del self.queued_messages[queued_msg.message_id]
                self.processing_messages[queued_msg.message_id] = queued_msg

                logger.info(
                    f"Worker {worker_id} processing message {queued_msg.message_id[:8]}... "
                    f"for session {queued_msg.session_id[:8]}..."
                )

                # Get session lock to prevent race conditions
                session_lock = self._get_session_lock(queued_msg.session_id)

                # Process message with session lock
                async with session_lock:
                    # Double-check for cancellation before processing
                    if queued_msg.message_id in self.cancelled_messages:
                        logger.info(
                            f"Worker {worker_id} skipping cancelled message {queued_msg.message_id[:8]}... "
                            f"(cancelled during lock wait)"
                        )
                        self.cancelled_messages.discard(queued_msg.message_id)
                        if queued_msg.message_id in self.processing_messages:
                            del self.processing_messages[queued_msg.message_id]
                        self.message_queue.task_done()
                        continue
                    try:
                        if self.process_function is None:
                            raise Exception("Process function not set")

                        # Call the processing function
                        response_data = await self.process_function(queued_msg)

                        processing_time = time.time() - start_time

                        response = MessageResponse(
                            message_id=queued_msg.message_id,
                            session_id=queued_msg.session_id,
                            response=response_data,
                            processing_time=processing_time
                        )

                        self.stats["messages_processed"] += 1
                        self.stats["total_processing_time"] += processing_time

                        # Remove from processing
                        if queued_msg.message_id in self.processing_messages:
                            del self.processing_messages[queued_msg.message_id]

                        logger.info(
                            f"Worker {worker_id} completed message {queued_msg.message_id[:8]}... "
                            f"in {processing_time:.2f}s"
                        )

                    except Exception as e:
                        processing_time = time.time() - start_time

                        logger.error(
                            f"Worker {worker_id} failed processing message {queued_msg.message_id[:8]}...: {str(e)}",
                            exc_info=True
                        )

                        response = MessageResponse(
                            message_id=queued_msg.message_id,
                            session_id=queued_msg.session_id,
                            response={},
                            error=str(e),
                            processing_time=processing_time
                        )

                        self.stats["messages_failed"] += 1

                        # Remove from processing
                        if queued_msg.message_id in self.processing_messages:
                            del self.processing_messages[queued_msg.message_id]

                # Call the callback if registered
                callback = self.response_callbacks.pop(queued_msg.message_id, None)
                if callback:
                    try:
                        await callback(response)
                    except Exception as e:
                        logger.error(f"Error in response callback: {str(e)}", exc_info=True)

                # Mark task as done
                self.message_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}", exc_info=True)

        logger.info(f"Worker {worker_id} stopped")

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.message_queue.qsize()

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        if stats["messages_processed"] > 0:
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["messages_processed"]
        else:
            stats["avg_processing_time"] = 0.0

        stats["queue_size"] = self.get_queue_size()
        stats["active_sessions"] = len(self.session_locks)

        return stats

    async def wait_for_completion(self):
        """Wait for all queued messages to be processed"""
        await self.message_queue.join()


# Global queue manager instance
_queue_manager: Optional[MessageQueueManager] = None


async def get_queue_manager(num_workers: int = 5) -> MessageQueueManager:
    """
    Get or create the global queue manager instance

    Args:
        num_workers: Number of worker tasks

    Returns:
        MessageQueueManager instance
    """
    global _queue_manager

    if _queue_manager is None:
        _queue_manager = MessageQueueManager(num_workers=num_workers)
        await _queue_manager.start()
        logger.info("Global message queue manager created and started")

    return _queue_manager


async def shutdown_queue_manager():
    """Shutdown the global queue manager"""
    global _queue_manager

    if _queue_manager is not None:
        await _queue_manager.stop()
        _queue_manager = None
        logger.info("Global message queue manager shut down")
