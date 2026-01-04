"""
Socket.IO event handlers for real-time communication
Enhanced with persistent sessions, analytics, sentiment analysis, and human handoff
Supports concurrent message processing for real-time chat and voice input
"""
import socketio
from typing import Dict, Any
import uuid
import time

from app.graph.workflow import process_message
from app.repositories.conversation_repository import ConversationRepository
from app.utils.analytics import get_analytics
from app.utils.config import settings
from app.utils.deduplication import get_dedup_manager
from app.utils.human_handoff import get_handoff_manager
from app.utils.logger import logger, log_agent_activity
from app.utils.message_queue import get_queue_manager, QueuedMessage
from app.utils.redis_session import get_session_manager
from app.utils.sentiment import get_sentiment_analyzer

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins_list,
    logger=True,
    engineio_logger=False
)

# Store active sessions (fallback for when Redis is unavailable)
active_sessions: Dict[str, Dict[str, Any]] = {}

# Global queue manager instance
queue_manager = None


async def initialize_queue_manager(num_workers: int = 5):
    """
    Initialize the message queue manager on startup

    Args:
        num_workers: Number of concurrent worker tasks
    """
    global queue_manager
    queue_manager = await get_queue_manager(num_workers=num_workers)
    queue_manager.set_process_function(process_message_worker)
    logger.info(f"Queue manager initialized with {num_workers} workers")


async def process_message_worker(queued_msg: QueuedMessage) -> Dict[str, Any]:
    """
    Worker function to process a queued message
    This is called by queue workers to process messages concurrently

    Args:
        queued_msg: Queued message with all context

    Returns:
        Dictionary containing response data and metadata
    """
    start_time = time.time()

    try:
        session_data = active_sessions.get(queued_msg.sid)

        if not session_data:
            raise Exception("Session not found")

        # Analyze sentiment
        sentiment_analyzer = get_sentiment_analyzer()
        sentiment = sentiment_analyzer.analyze(queued_msg.user_message)

        logger.info(
            f"Processing message {queued_msg.message_id[:8]}... "
            f"Sentiment: {sentiment['sentiment_label']} (polarity: {sentiment['polarity']}, "
            f"urgency: {sentiment['urgency_level']})"
        )

        # Send typing indicator
        await sio.emit('typing', {
            "is_typing": True,
            "agent": "processing",
            "message_id": queued_msg.message_id
        }, room=queued_msg.sid)

        # Process message through agent workflow
        existing_state = session_data.get("state")

        result_state = await process_message(
            session_id=queued_msg.session_id,
            message=queued_msg.user_message,
            customer_id=None,
            existing_state=existing_state
        )

        # Add sentiment to state context
        if "conversation_context" not in result_state:
            result_state["conversation_context"] = {}
        result_state["conversation_context"]["last_sentiment"] = sentiment

        # Update session state
        session_data["state"] = result_state

        # Save to Redis for persistence
        session_manager = await get_session_manager()
        await session_manager.save_session(queued_msg.session_id, result_state)

        # Save to PostgreSQL database for persistent storage
        try:
            messages = result_state.get("conversation_messages", [])
            current_agent = result_state.get("current_active_agent")
            context = result_state.get("conversation_context", {})

            ConversationRepository.save_conversation(
                session_id=queued_msg.session_id,
                messages=messages,
                current_agent=current_agent,
                context=context,
                customer_id=None
            )
            logger.debug(f"Saved conversation {queued_msg.session_id} to PostgreSQL database")
        except Exception as db_error:
            logger.error(f"Failed to save conversation to database: {str(db_error)}")
            # Don't fail the request if database save fails

        # Get response using new state key names
        response_text = result_state.get("generated_response", "I'm not sure how to respond to that.")
        current_agent = result_state.get("current_active_agent", "assistant")

        # Record performance metrics
        response_time_ms = (time.time() - start_time) * 1000
        analytics = await get_analytics()
        await analytics.record_agent_response(
            agent_name=current_agent,
            response_time_ms=response_time_ms,
            session_id=queued_msg.session_id,
            intent=result_state.get("classified_intent"),
            confidence=result_state.get("intent_confidence_score"),
            success=True
        )

        # Check if human handoff is needed
        handoff_manager = await get_handoff_manager()
        needs_handoff, handoff_reason, handoff_priority = await handoff_manager.check_handoff_needed(
            result_state,
            sentiment
        )

        # Stop typing indicator
        await sio.emit('typing', {
            "is_typing": False,
            "message_id": queued_msg.message_id
        }, room=queued_msg.sid)

        # Collect sequence processing metadata (if available from V2 agents)
        sequence_metadata = result_state.get("sequence_metadata", {})
        sequence_processing = None

        if sequence_metadata:
            # Calculate total duration from all sequences
            total_seq_duration = sum(
                seq_info.get("duration_seconds", 0)
                for seq_info in sequence_metadata.values()
            )

            sequence_processing = {
                "seq1_duration": sequence_metadata.get("seq1", {}).get("duration_seconds"),
                "seq2_duration": sequence_metadata.get("seq2", {}).get("duration_seconds"),
                "total_duration": total_seq_duration,
                "sequences_executed": len(sequence_metadata),
                "prompt_chain_used": True
            }

        # Send response with enhanced metadata and message_id for correlation
        await sio.emit('response', {
            "message": response_text,
            "agent": current_agent,
            "timestamp": None,
            "message_id": queued_msg.message_id,  # Correlation ID
            "metadata": {
                "intent": result_state.get("classified_intent"),
                "confidence": result_state.get("intent_confidence_score"),
                "db_operations_count": len(result_state.get("database_operations_log", [])),
                "sentiment": sentiment['sentiment_label'],
                "sentiment_polarity": sentiment['polarity'],
                "urgency_level": sentiment['urgency_level'],
                "response_time_ms": round(response_time_ms, 2),
                "sequence_processing": sequence_processing  # NEW: Multi-prompt sequence info
            }
        }, room=queued_msg.sid)

        # If agent was switched, notify client
        if result_state.get("agent_handoff_history"):
            last_handoff = result_state["agent_handoff_history"][-1]
            await sio.emit('agent_switch', {
                "from_agent": last_handoff["from_agent"],
                "to_agent": last_handoff["to_agent"],
                "reason": last_handoff["reason"],
                "message_id": queued_msg.message_id
            }, room=queued_msg.sid)

        # If human handoff is needed, trigger escalation
        if needs_handoff:
            handoff_result = await handoff_manager.request_handoff(
                session_id=queued_msg.session_id,
                customer_id=None,
                current_agent=current_agent,
                reason=handoff_reason,
                priority=handoff_priority,
                context={
                    "conversation_messages": result_state.get("conversation_messages", []),
                    "intent": result_state.get("classified_intent"),
                    "agent_handoff_history": result_state.get("agent_handoff_history", [])
                },
                sentiment=sentiment
            )

            await sio.emit('human_handoff', {
                "handoff_id": handoff_result["handoff_id"],
                "queue_position": handoff_result["queue_position"],
                "estimated_wait_time": handoff_result["estimated_wait_time"],
                "reason": handoff_reason.value if handoff_reason else "unknown",
                "priority": handoff_priority.value if handoff_priority else "medium",
                "message": handoff_result["message"],
                "message_id": queued_msg.message_id
            }, room=queued_msg.sid)

            logger.info(f"Human handoff requested for session {queued_msg.session_id}: {handoff_reason}")

        log_agent_activity(
            agent_name=current_agent,
            activity="message_processed",
            session_id=queued_msg.session_id,
            metadata={
                "message_id": queued_msg.message_id,
                "intent": result_state.get("classified_intent"),
                "response_length": len(response_text),
                "sentiment": sentiment['sentiment_label'],
                "response_time_ms": response_time_ms,
                "human_handoff": needs_handoff
            }
        )

        return {
            "success": True,
            "message_id": queued_msg.message_id,
            "response_time_ms": response_time_ms
        }

    except Exception as e:
        logger.error(
            f"Error processing message {queued_msg.message_id[:8]}...: {str(e)}",
            exc_info=True
        )

        # Record failed request
        response_time_ms = (time.time() - start_time) * 1000
        try:
            analytics = await get_analytics()
            await analytics.record_agent_response(
                agent_name="system",
                response_time_ms=response_time_ms,
                session_id=queued_msg.session_id,
                success=False
            )
        except:
            pass

        # Stop typing indicator
        await sio.emit('typing', {
            "is_typing": False,
            "message_id": queued_msg.message_id
        }, room=queued_msg.sid)

        # Send error with message_id for correlation
        await sio.emit('error', {
            "code": "PROCESSING_ERROR",
            "message": "An error occurred while processing your message. Please try again.",
            "message_id": queued_msg.message_id
        }, room=queued_msg.sid)

        return {
            "success": False,
            "message_id": queued_msg.message_id,
            "error": str(e),
            "response_time_ms": response_time_ms
        }


@sio.event
async def connect(sid: str, environ: dict, auth: dict = None):
    """
    Handle client connection with persistent session support

    Args:
        sid: Socket ID
        environ: WSGI environment
        auth: Authentication data (can include existing_session_id for reconnection)
    """
    logger.info(f"Client connected: {sid}")

    # Get session manager
    session_manager = await get_session_manager()

    # Check if reconnecting with existing session
    existing_session_id = None
    if auth and isinstance(auth, dict):
        existing_session_id = auth.get("session_id")

    # Try to load existing session from Redis
    loaded_state = None
    if existing_session_id:
        loaded_state = await session_manager.load_session(existing_session_id)
        if loaded_state:
            logger.info(f"Restored session {existing_session_id} from Redis")
            session_id = existing_session_id
        else:
            logger.info(f"Session {existing_session_id} not found, creating new session")
            session_id = str(uuid.uuid4())
    else:
        session_id = str(uuid.uuid4())

    # Create session entry
    active_sessions[sid] = {
        "session_id": session_id,
        "state": loaded_state,
        "connected_at": time.time()
    }

    # Send connection confirmation
    await sio.emit('connected', {
        "session_id": session_id,
        "message": "Connected to ElectroMart Agent System",
        "restored": loaded_state is not None
    }, room=sid)

    log_agent_activity(
        agent_name="system",
        activity="client_connected",
        session_id=session_id,
        metadata={"sid": sid, "restored": loaded_state is not None}
    )


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection with session persistence

    Args:
        sid: Socket ID
    """
    session_data = active_sessions.get(sid)

    if session_data:
        session_id = session_data['session_id']
        logger.info(f"Client disconnected: {sid}, session: {session_id}")

        # Save state to Redis for persistence
        if session_data.get('state'):
            session_manager = await get_session_manager()
            await session_manager.save_session(session_id, session_data['state'])
            logger.info(f"Saved session {session_id} to Redis")

            # Also save to PostgreSQL database
            try:
                result_state = session_data['state']
                messages = result_state.get("conversation_messages", [])
                current_agent = result_state.get("current_active_agent")
                context = result_state.get("conversation_context", {})

                ConversationRepository.save_conversation(
                    session_id=session_id,
                    messages=messages,
                    current_agent=current_agent,
                    context=context,
                    customer_id=None
                )
                logger.info(f"Saved session {session_id} to PostgreSQL database")
            except Exception as db_error:
                logger.error(f"Failed to save conversation to database on disconnect: {str(db_error)}")

        del active_sessions[sid]
    else:
        logger.info(f"Client disconnected: {sid}")


@sio.event
async def message(sid: str, data: dict):
    """
    Handle incoming message from client - Concurrent version
    Messages are queued and processed by worker pool for true real-time experience

    Args:
        sid: Socket ID
        data: Message data
            - message: User message text
            - type: Message type ('text' or 'voice')

    Features:
        - Concurrent message processing (no blocking)
        - Message correlation IDs for response tracking
        - Sentiment analysis
        - Performance analytics
        - Human handoff detection
        - Persistent session storage
    """
    try:
        session_data = active_sessions.get(sid)

        if not session_data:
            await sio.emit('error', {
                "code": "NO_SESSION",
                "message": "Session not found. Please reconnect."
            }, room=sid)
            return

        session_id = session_data["session_id"]
        user_message = data.get("message", "")
        message_type = data.get("type", "text")

        if not user_message:
            await sio.emit('error', {
                "code": "EMPTY_MESSAGE",
                "message": "Message cannot be empty"
            }, room=sid)
            return

        logger.info(f"Message received from {sid}: {user_message[:100]}")

        # Check for duplicate messages (prevents double-click, timeout retries)
        dedup_manager = get_dedup_manager()
        is_duplicate, reason = dedup_manager.is_duplicate(session_id, user_message)

        if is_duplicate:
            logger.info(
                f"Duplicate message ignored for session {session_id[:8]}... "
                f"Reason: {reason}"
            )

            # Send duplicate acknowledgment (so frontend knows it was received)
            await sio.emit('message_duplicate', {
                "message": "This message was already received and is being processed.",
                "reason": reason,
                "original_message": user_message[:50]
            }, room=sid)

            return

        # Record this message to prevent future duplicates
        dedup_manager.record_message(session_id, user_message)

        # Check for interruption keywords ("never mind", "stop", "cancel", etc.)
        interruption_keywords = [
            "never mind", "nevermind", "forget it", "stop", "cancel",
            "ignore that", "scratch that", "wait", "hold on"
        ]

        user_message_lower = user_message.lower().strip()
        is_interruption = any(keyword in user_message_lower for keyword in interruption_keywords)

        # If this is an interruption, cancel all pending messages
        if is_interruption and queue_manager:
            cancelled_count = await queue_manager.cancel_session_messages(session_id)

            if cancelled_count > 0:
                logger.info(
                    f"Interruption detected: '{user_message[:50]}...' - "
                    f"Cancelled {cancelled_count} pending messages for session {session_id[:8]}..."
                )

                # Notify client
                await sio.emit('all_messages_cancelled', {
                    "cancelled_count": cancelled_count,
                    "reason": "interruption_detected",
                    "message": f"Cancelled {cancelled_count} pending message(s) due to interruption"
                }, room=sid)

        # Enqueue message for concurrent processing
        if queue_manager is None:
            logger.error("Queue manager not initialized!")
            await sio.emit('error', {
                "code": "SYSTEM_ERROR",
                "message": "Message processing system not ready. Please try again."
            }, room=sid)
            return

        # Enqueue the message (non-blocking)
        message_id = await queue_manager.enqueue_message(
            sid=sid,
            session_id=session_id,
            user_message=user_message,
            message_type=message_type,
            metadata={"received_at": time.time()}
        )

        # Send immediate acknowledgment with message_id
        await sio.emit('message_queued', {
            "message_id": message_id,
            "queue_position": queue_manager.get_queue_size(),
            "status": "queued"
        }, room=sid)

        logger.info(
            f"Message {message_id[:8]}... queued for session {session_id[:8]}... "
            f"(queue size: {queue_manager.get_queue_size()})"
        )

    except Exception as e:
        logger.error(f"Error queueing message: {str(e)}", exc_info=True)

        await sio.emit('error', {
            "code": "QUEUE_ERROR",
            "message": "Failed to queue your message. Please try again."
        }, room=sid)


@sio.event
async def typing(sid: str, data: dict):
    """
    Handle typing indicator from client

    Args:
        sid: Socket ID
        data: Typing data
            - is_typing: Boolean indicating typing status
    """
    # Echo typing indicator (useful for multi-user scenarios)
    is_typing = data.get("is_typing", False)
    logger.debug(f"Client {sid} typing: {is_typing}")


@sio.event
async def cancel_message(sid: str, data: dict):
    """
    Handle message cancellation from client

    Args:
        sid: Socket ID
        data: Cancellation data
            - message_id: Message correlation ID to cancel
    """
    try:
        message_id = data.get("message_id")

        if not message_id:
            await sio.emit('error', {
                "code": "INVALID_REQUEST",
                "message": "message_id is required"
            }, room=sid)
            return

        session_data = active_sessions.get(sid)
        if not session_data:
            await sio.emit('error', {
                "code": "NO_SESSION",
                "message": "Session not found"
            }, room=sid)
            return

        # Cancel the message in queue manager
        if queue_manager:
            cancelled = await queue_manager.cancel_message(message_id)

            if cancelled:
                await sio.emit('message_cancelled', {
                    "message_id": message_id,
                    "status": "cancelled"
                }, room=sid)

                logger.info(f"Message {message_id[:8]}... cancelled by user {sid}")
            else:
                await sio.emit('error', {
                    "code": "CANNOT_CANCEL",
                    "message": "Message cannot be cancelled (already completed or not found)",
                    "message_id": message_id
                }, room=sid)
        else:
            await sio.emit('error', {
                "code": "SYSTEM_ERROR",
                "message": "Queue manager not available"
            }, room=sid)

    except Exception as e:
        logger.error(f"Error cancelling message: {str(e)}", exc_info=True)
        await sio.emit('error', {
            "code": "CANCEL_ERROR",
            "message": "Failed to cancel message"
        }, room=sid)


@sio.event
async def cancel_all_messages(sid: str, data: dict = None):
    """
    Handle cancellation of all pending messages for this session
    Useful for "never mind" interruptions

    Args:
        sid: Socket ID
        data: Optional data
    """
    try:
        session_data = active_sessions.get(sid)
        if not session_data:
            await sio.emit('error', {
                "code": "NO_SESSION",
                "message": "Session not found"
            }, room=sid)
            return

        session_id = session_data["session_id"]

        # Cancel all messages for this session
        if queue_manager:
            cancelled_count = await queue_manager.cancel_session_messages(session_id)

            await sio.emit('all_messages_cancelled', {
                "cancelled_count": cancelled_count,
                "status": "cancelled"
            }, room=sid)

            logger.info(
                f"Cancelled {cancelled_count} messages for session {session_id[:8]}... "
                f"by user request"
            )
        else:
            await sio.emit('error', {
                "code": "SYSTEM_ERROR",
                "message": "Queue manager not available"
            }, room=sid)

    except Exception as e:
        logger.error(f"Error cancelling all messages: {str(e)}", exc_info=True)
        await sio.emit('error', {
            "code": "CANCEL_ERROR",
            "message": "Failed to cancel messages"
        }, room=sid)


@sio.event
async def ping(sid: str, data: dict = None):
    """
    Handle ping from client for keep-alive

    Args:
        sid: Socket ID
        data: Optional ping data
    """
    await sio.emit('pong', {"timestamp": None}, room=sid)


# Create ASGI app for Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io'
)