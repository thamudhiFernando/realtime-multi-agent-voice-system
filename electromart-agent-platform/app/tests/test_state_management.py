"""
Unit tests for state management functionality
"""
from datetime import datetime
from app.graph.state import (
    create_initial_conversation_state,
    append_message_to_conversation,
    record_agent_handoff,
    log_database_operation,
)


class TestStateInitialization:
    """Test suite for state initialization"""

    def test_create_initial_state_with_session_id_only(self):
        """Test creating initial state with just session ID"""
        session_id = "test-session-123"
        state = create_initial_conversation_state(session_id)

        assert state["unique_session_id"] == session_id
        assert state["customer_identifier"] is None
        assert len(state["conversation_messages"]) == 0
        assert state["current_active_agent"] == "orchestrator"
        assert state["classified_intent"] is None
        assert state["should_end_conversation_turn"] is False

    def test_create_initial_state_with_customer_id(self):
        """Test creating initial state with customer ID"""
        session_id = "test-session-456"
        customer_id = 42

        state = create_initial_conversation_state(session_id, customer_id)

        assert state["unique_session_id"] == session_id
        assert state["customer_identifier"] == customer_id

    def test_initial_state_has_empty_collections(self):
        """Test that initial state has empty collections"""
        state = create_initial_conversation_state("test-session")

        assert isinstance(state["conversation_messages"], list)
        assert isinstance(state["conversation_context"], dict)
        assert isinstance(state["agent_handoff_history"], list)
        assert isinstance(state["database_operations_log"], list)
        assert len(state["agent_handoff_history"]) == 0


class TestMessageManagement:
    """Test suite for message management"""

    def test_append_user_message(self, mock_conversation_state):
        """Test appending a user message"""
        updated_state = append_message_to_conversation(
            mock_conversation_state,
            message_role="user",
            message_content="Hello, I need help",
            originating_agent=None
        )

        assert len(updated_state["conversation_messages"]) == 1
        message = updated_state["conversation_messages"][0]
        assert message["role"] == "user"
        assert message["content"] == "Hello, I need help"
        assert message["agent_name"] is None

    def test_append_assistant_message_with_agent(self, mock_conversation_state):
        """Test appending an assistant message with agent name"""
        updated_state = append_message_to_conversation(
            mock_conversation_state,
            message_role="assistant",
            message_content="I can help you with that",
            originating_agent="sales"
        )

        message = updated_state["conversation_messages"][0]
        assert message["role"] == "assistant"
        assert message["agent_name"] == "sales"

    def test_message_has_timestamp(self, mock_conversation_state):
        """Test that messages have timestamps"""
        updated_state = append_message_to_conversation(
            mock_conversation_state,
            message_role="user",
            message_content="Test message"
        )

        message = updated_state["conversation_messages"][0]
        assert "timestamp" in message
        assert message["timestamp"] is not None
        # Verify timestamp is ISO format
        datetime.fromisoformat(message["timestamp"])

    def test_append_message_with_metadata(self, mock_conversation_state):
        """Test appending message with additional metadata"""
        metadata = {"intent": "sales", "confidence": 0.95}

        updated_state = append_message_to_conversation(
            mock_conversation_state,
            message_role="assistant",
            message_content="Here are the products",
            originating_agent="sales",
            extra_metadata=metadata
        )

        message = updated_state["conversation_messages"][0]
        assert message["additional_metadata"]["intent"] == "sales"
        assert message["additional_metadata"]["confidence"] == 0.95

    def test_multiple_messages_appended_in_order(self, mock_conversation_state):
        """Test that multiple messages maintain order"""
        state = mock_conversation_state

        # Add three messages
        state = append_message_to_conversation(state, "user", "First message")
        state = append_message_to_conversation(state, "assistant", "Second message", "sales")
        state = append_message_to_conversation(state, "user", "Third message")

        assert len(state["conversation_messages"]) == 3
        assert state["conversation_messages"][0]["content"] == "First message"
        assert state["conversation_messages"][1]["content"] == "Second message"
        assert state["conversation_messages"][2]["content"] == "Third message"


class TestAgentHandoffManagement:
    """Test suite for agent handoff management"""

    def test_record_agent_handoff_basic(self, mock_conversation_state):
        """Test recording a basic agent handoff"""
        updated_state = record_agent_handoff(
            mock_conversation_state,
            source_agent_name="sales",
            destination_agent_name="support",
            handoff_reason="Customer needs technical assistance"
        )

        assert len(updated_state["agent_handoff_history"]) == 1
        handoff = updated_state["agent_handoff_history"][0]
        assert handoff["from_agent"] == "sales"
        assert handoff["to_agent"] == "support"
        assert handoff["reason"] == "Customer needs technical assistance"

    def test_handoff_updates_current_agent(self, mock_conversation_state):
        """Test that handoff updates the current active agent"""
        updated_state = record_agent_handoff(
            mock_conversation_state,
            source_agent_name="orchestrator",
            destination_agent_name="marketing",
            handoff_reason="Promotion inquiry"
        )

        assert updated_state["current_active_agent"] == "marketing"

    def test_handoff_clears_handoff_flags(self, mock_conversation_state):
        """Test that handoff clears the handoff request flags"""
        # Set handoff flags
        mock_conversation_state["requires_agent_handoff"] = True
        mock_conversation_state["target_handoff_agent"] = "support"

        updated_state = record_agent_handoff(
            mock_conversation_state,
            source_agent_name="sales",
            destination_agent_name="support",
            handoff_reason="Technical issue"
        )

        assert updated_state["requires_agent_handoff"] is False
        assert updated_state["target_handoff_agent"] is None

    def test_multiple_handoffs_recorded(self, mock_conversation_state):
        """Test that multiple handoffs are recorded in history"""
        state = mock_conversation_state

        state = record_agent_handoff(state, "orchestrator", "sales", "Product inquiry")
        state = record_agent_handoff(state, "sales", "support", "Technical issue")
        state = record_agent_handoff(state, "support", "logistics", "Return request")

        assert len(state["agent_handoff_history"]) == 3
        assert state["current_active_agent"] == "logistics"

    def test_handoff_has_timestamp(self, mock_conversation_state):
        """Test that handoffs have timestamps"""
        updated_state = record_agent_handoff(
            mock_conversation_state,
            source_agent_name="sales",
            destination_agent_name="marketing",
            handoff_reason="Discount inquiry"
        )

        handoff = updated_state["agent_handoff_history"][0]
        assert "timestamp" in handoff
        # Verify timestamp is valid
        datetime.fromisoformat(handoff["timestamp"])


class TestDatabaseOperationLogging:
    """Test suite for database operation logging"""

    def test_log_read_operation(self, mock_conversation_state):
        """Test logging a database READ operation"""
        updated_state = log_database_operation(
            mock_conversation_state,
            operation_type="READ",
            database_table_name="products",
            operation_details={"query": "search_by_category", "category": "Laptops"}
        )

        assert len(updated_state["database_operations_log"]) == 1
        operation = updated_state["database_operations_log"][0]
        assert operation["type"] == "READ"
        assert operation["table"] == "products"
        assert operation["details"]["category"] == "Laptops"

    def test_log_write_operation(self, mock_conversation_state):
        """Test logging a database WRITE operation"""
        updated_state = log_database_operation(
            mock_conversation_state,
            operation_type="WRITE",
            database_table_name="support_tickets",
            operation_details={"action": "create_ticket", "ticket_id": "TKT123"}
        )

        operation = updated_state["database_operations_log"][0]
        assert operation["type"] == "WRITE"
        assert operation["table"] == "support_tickets"

    def test_operation_includes_current_agent(self, mock_conversation_state):
        """Test that logged operations include the current agent"""
        mock_conversation_state["current_active_agent"] = "sales"

        updated_state = log_database_operation(
            mock_conversation_state,
            operation_type="READ",
            database_table_name="products",
            operation_details={}
        )

        operation = updated_state["database_operations_log"][0]
        assert operation["agent"] == "sales"

    def test_multiple_operations_logged(self, mock_conversation_state):
        """Test that multiple operations are logged"""
        state = mock_conversation_state

        state = log_database_operation(state, "READ", "products", {})
        state = log_database_operation(state, "READ", "orders", {})
        state = log_database_operation(state, "WRITE", "support_tickets", {})

        assert len(state["database_operations_log"]) == 3

    def test_operation_has_timestamp(self, mock_conversation_state):
        """Test that operations have timestamps"""
        updated_state = log_database_operation(
            mock_conversation_state,
            operation_type="READ",
            database_table_name="products",
            operation_details={}
        )

        operation = updated_state["database_operations_log"][0]
        assert "timestamp" in operation
        datetime.fromisoformat(operation["timestamp"])


class TestStateIntegrity:
    """Test suite for state integrity and consistency"""

    def test_state_remains_immutable_reference(self):
        """Test that state modifications don't break references"""
        original_session_id = "test-123"
        state = create_initial_conversation_state(original_session_id)

        # Modify state
        state = append_message_to_conversation(state, "user", "Hello")

        # Original session ID should still be accessible
        assert state["unique_session_id"] == original_session_id

    def test_complex_state_workflow(self):
        """Test a complex workflow with multiple state modifications"""
        # Initialize
        state = create_initial_conversation_state("session-complex")

        # Add user message
        state = append_message_to_conversation(state, "user", "Show me laptops")

        # Set intent
        state["classified_intent"] = "sales"
        state["intent_confidence_score"] = 0.92

        # Log database read
        state = log_database_operation(state, "READ", "products", {"category": "Laptops"})

        # Add assistant response
        state = append_message_to_conversation(
            state, "assistant", "Here are the laptops", "sales"
        )

        # Handoff to support
        state = record_agent_handoff(state, "sales", "support", "Warranty question")

        # Verify final state
        assert len(state["conversation_messages"]) == 2
        assert len(state["database_operations_log"]) == 1
        assert len(state["agent_handoff_history"]) == 1
        assert state["current_active_agent"] == "support"
        assert state["classified_intent"] == "sales"
