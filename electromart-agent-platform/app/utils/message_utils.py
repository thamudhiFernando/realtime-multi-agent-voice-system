"""
Utility functions for handling messages in agent workflows
"""
from typing import Any, Optional


def get_message_content(msg: Any) -> Optional[str]:
    """
    Safely extract content from a message, handling both dicts and LangChain Message objects

    Args:
        msg: Message object (dict or LangChain Message)

    Returns:
        Message content string or None
    """
    # LangChain Message object
    if hasattr(msg, 'content'):
        return msg.content
    # Dict-based message
    elif isinstance(msg, dict):
        return msg.get("content")
    return None


def is_user_message(msg: Any) -> bool:
    """
    Check if a message is from a user, handling both dicts and LangChain Message objects

    Args:
        msg: Message object (dict or LangChain Message)

    Returns:
        True if message is from user
    """
    # LangChain HumanMessage object
    if hasattr(msg, 'type') and msg.type == "human":
        return True
    # Dict-based message with role="user"
    elif isinstance(msg, dict) and msg.get("role") == "user":
        return True
    return False


def get_user_message(messages: list) -> Optional[Any]:
    """
    Get the most recent user message from a list of messages

    Args:
        messages: List of message objects

    Returns:
        Most recent user message or None
    """
    for msg in reversed(messages):
        if is_user_message(msg):
            return msg
    return None
