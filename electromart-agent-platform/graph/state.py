"""
LangGraph State Management for ElectroMart Multi-Agent System
Refactored with meaningful variable and function names
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import add_messages
from datetime import datetime


class ConversationMessage(TypedDict):
    """Represents a single message in the conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    agent_name: Optional[str]  # Which agent generated this message
    additional_metadata: Optional[Dict[str, Any]]


class AgentConversationState(TypedDict):
    """
    Complete state schema for the multi-agent conversation system

    This state is passed between nodes in the LangGraph workflow
    and maintains all conversation context
    """
    # Session identification
    unique_session_id: str
    customer_identifier: Optional[int]

    # Complete conversation history
    conversation_messages: Annotated[List[ConversationMessage], add_messages]

    # Active agent information
    current_active_agent: str  # 'orchestrator', 'sales', 'marketing', 'support', 'logistics'

    # Intent classification results
    classified_intent: Optional[str]  # 'sales', 'marketing', 'support', 'orders', 'general'
    intent_confidence_score: Optional[float]  # Confidence score for intent classification

    # Additional context and extracted entities
    conversation_context: Dict[str, Any]  # Store extracted entities (product IDs, order numbers, etc.)

    # Agent handoff tracking
    agent_handoff_history: List[Dict[str, Any]]  # Track all agent transitions
    requires_agent_handoff: bool  # Flag indicating if handoff is needed
    target_handoff_agent: Optional[str]  # Target agent for handoff

    # Database operations audit trail
    database_operations_log: List[Dict[str, Any]]  # Track READ/WRITE operations

    # Multi-step sequence tracking (Seq1, Seq2, etc.)
    current_sequence_step: int  # Current sequence step (1, 2, 3...)
    total_sequence_steps: int  # Total number of sequence steps
    prompt_chain_results: Dict[str, Any]  # Store results from each prompt (P1, P2, etc.)
    sequence_metadata: Dict[str, Any]  # Metadata for each sequence step

    # Response generation
    generated_response: Optional[str]  # Final response to user
    should_end_conversation_turn: bool  # Flag to end conversation turn


def create_initial_conversation_state(
    session_id: str,
    customer_id: Optional[int] = None
) -> AgentConversationState:
    """
    Initialize a new conversation state for a customer session

    Args:
        session_id: Unique identifier for the conversation session
        customer_id: Optional customer database identifier

    Returns:
        AgentConversationState: Initial state with default values
    """
    return AgentConversationState(
        unique_session_id=session_id,
        customer_identifier=customer_id,
        conversation_messages=[],
        current_active_agent="orchestrator",
        classified_intent=None,
        intent_confidence_score=None,
        conversation_context={},
        agent_handoff_history=[],
        requires_agent_handoff=False,
        target_handoff_agent=None,
        database_operations_log=[],
        current_sequence_step=1,
        total_sequence_steps=2,
        prompt_chain_results={},
        sequence_metadata={},
        generated_response=None,
        should_end_conversation_turn=False
    )


def append_message_to_conversation(
    current_state: AgentConversationState,
    message_role: str,
    message_content: str,
    originating_agent: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> AgentConversationState:
    """
    Add a new message to the conversation state

    Args:
        current_state: Current conversation state
        message_role: Role of the message sender ('user', 'assistant', 'system')
        message_content: The actual message text
        originating_agent: Name of the agent that generated the message
        extra_metadata: Additional metadata to attach to the message

    Returns:
        AgentConversationState: Updated state with new message
    """
    new_message = ConversationMessage(
        role=message_role,
        content=message_content,
        timestamp=datetime.utcnow().isoformat(),
        agent_name=originating_agent,
        additional_metadata=extra_metadata or {}
    )

    current_state["conversation_messages"].append(new_message)
    return current_state


def record_agent_handoff(
    current_state: AgentConversationState,
    source_agent_name: str,
    destination_agent_name: str,
    handoff_reason: str
) -> AgentConversationState:
    """
    Record an agent-to-agent handoff in the conversation state

    Args:
        current_state: Current conversation state
        source_agent_name: Name of the agent handing off
        destination_agent_name: Name of the agent receiving
        handoff_reason: Reason for the handoff

    Returns:
        AgentConversationState: Updated state with handoff record
    """
    handoff_record = {
        "from_agent": source_agent_name,
        "to_agent": destination_agent_name,
        "reason": handoff_reason,
        "timestamp": datetime.utcnow().isoformat()
    }

    current_state["agent_handoff_history"].append(handoff_record)
    current_state["current_active_agent"] = destination_agent_name
    current_state["requires_agent_handoff"] = False
    current_state["target_handoff_agent"] = None

    return current_state


def log_database_operation(
    current_state: AgentConversationState,
    operation_type: str,  # 'READ' or 'WRITE'
    database_table_name: str,
    operation_details: Dict[str, Any]
) -> AgentConversationState:
    """
    Log a database operation for audit trail

    Args:
        current_state: Current conversation state
        operation_type: Type of database operation ('READ' or 'WRITE')
        database_table_name: Name of the database table
        operation_details: Details about what was read/written

    Returns:
        AgentConversationState: Updated state with operation log
    """
    operation_record = {
        "type": operation_type,
        "table": database_table_name,
        "details": operation_details,
        "timestamp": datetime.utcnow().isoformat(),
        "agent": current_state["current_active_agent"]
    }

    current_state["database_operations_log"].append(operation_record)
    return current_state
