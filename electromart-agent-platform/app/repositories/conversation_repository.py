"""
Conversation Repository for Database Persistence
Handles saving and retrieving conversations from PostgreSQL
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import Conversation
from app.database.connection import SessionLocal
from app.utils.logger import logger


class ConversationRepository:
    """Repository for managing conversations in database"""

    @staticmethod
    def _serialize_message(msg: Any) -> Dict[str, Any]:
        """
        Convert a LangChain message object to a JSON-serializable dictionary

        Args:
            msg: LangChain message object (HumanMessage, AIMessage, etc.)

        Returns:
            Dictionary representation of the message
        """
        # If it's already a dict, return it
        if isinstance(msg, dict):
            return msg

        # If it's a LangChain message object, extract its properties
        try:
            message_dict = {
                "type": msg.__class__.__name__,
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            }

            # Add additional_kwargs if present
            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                message_dict["additional_kwargs"] = msg.additional_kwargs

            # Add other common attributes
            if hasattr(msg, 'id'):
                message_dict["id"] = msg.id
            if hasattr(msg, 'name'):
                message_dict["name"] = msg.name

            return message_dict
        except Exception as e:
            logger.warning(f"Failed to serialize message object: {e}, using string representation")
            return {"type": "Unknown", "content": str(msg)}

    @staticmethod
    def save_conversation(
        session_id: str,
        messages: List[Dict[str, Any]],
        current_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        customer_id: Optional[int] = None
    ) -> bool:
        """
        Save or update conversation in database

        Args:
            session_id: Unique session identifier
            messages: List of conversation messages
            current_agent: Current active agent
            context: Additional conversation context
            customer_id: Optional customer ID

        Returns:
            True if successful, False otherwise
        """
        db = SessionLocal()
        try:
            # Serialize messages to ensure JSON compatibility
            serialized_messages = []
            if messages:
                for msg in messages:
                    serialized_messages.append(ConversationService._serialize_message(msg))

            # Check if conversation exists
            conversation = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()

            if conversation:
                # Update existing conversation
                conversation.messages = serialized_messages
                conversation.current_agent = current_agent
                conversation.context = context or {}
                conversation.updated_at = datetime.now(timezone.utc)
                logger.debug(f"Updated conversation {session_id} with {len(serialized_messages)} messages")
            else:
                # Create new conversation
                conversation = Conversation(
                    session_id=session_id,
                    customer_id=customer_id,
                    messages=serialized_messages,
                    current_agent=current_agent,
                    context=context or {},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(conversation)
                logger.info(f"Created new conversation {session_id}")

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save conversation {session_id}: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_conversation(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation from database

        Args:
            session_id: Session identifier

        Returns:
            Conversation data or None
        """
        db = SessionLocal()
        try:
            conversation = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()

            if conversation:
                return {
                    "session_id": conversation.session_id,
                    "messages": conversation.messages,
                    "current_agent": conversation.current_agent,
                    "context": conversation.context,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get conversation {session_id}: {str(e)}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_recent_conversations(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations from database

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversations
        """
        db = SessionLocal()
        try:
            conversations = db.query(Conversation).order_by(
                desc(Conversation.updated_at)
            ).limit(limit).all()

            return [{
                "session_id": conv.session_id,
                "current_agent": conv.current_agent,
                "message_count": len(conv.messages) if conv.messages else 0,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
            } for conv in conversations]

        except Exception as e:
            logger.error(f"Failed to get recent conversations: {str(e)}")
            return []
        finally:
            db.close()